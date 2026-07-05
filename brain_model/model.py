"""Model poznawczy integrujący aktywacje, bodźce i oscylatory."""

from typing import Callable, cast

import numpy as np

from brain_core.cognition import regions_for_module

from .activations import sigmoid
from .behavior import map_behavior_state
from .connectivity import build_connectivity
from .modules import MODULES, TAU
from .oscillators import WilsonCowanOscillatorBank, WilsonCowanParams
from .params import BrainParams
from .plasticity import (
    WeightUpdateMap,
    apply_state_learning,
    build_weight_history_series,
    update_connectivity,
)
from .scenarios import CHANNELS, get_scenario
from .scenarios.types import StimulusScenario
from .stimuli import StimulusFn, build_stimulus_fn

StimulusChannels = dict[str, float]
StepDiagnostics = dict[str, float | WeightUpdateMap]
SimulationDiagnostics = dict[str, np.ndarray]
OscillationOutputs = dict[str, dict[str, np.ndarray]]
BehaviorOutputs = dict[str, np.ndarray]
SimulationResult = tuple[
    np.ndarray,
    np.ndarray,
    SimulationDiagnostics,
    OscillationOutputs,
    BehaviorOutputs,
]


class CognitiveBrainModel:
    """
    Mezoskopowy model dynamiki poznawczej.

    Równanie główne:

        dx/dt = (-x + sigmoid(Wx + external + error + global_broadcast)) / tau + noise

    gdzie:
        x:
            wektor aktywacji modułów poznawczych,
        W:
            macierz połączeń funkcjonalnych,
        external:
            wejścia sensoryczne i zadaniowe,
        error:
            błąd predykcji,
        global_broadcast:
            globalne udostępnienie reprezentacji,
        tau:
            stałe czasowe modułów.
    """

    def __init__(
        self,
        params: BrainParams | None = None,
        stimulus: str | StimulusFn | None = None,
        seed: int = 7,
        oscillator_params: WilsonCowanParams | None = None,
        oscillator_band_map: dict[str, str] | None = None,
    ) -> None:
        """Przygotuj stan modelu poznawczego i źródło bodźców.

        Parameters
        ----------
        params:
            Parametry integracji, plastyczności i progów decyzyjnych. Brak
            wartości tworzy domyślną konfigurację ``BrainParams``.
        stimulus:
            ``None`` wybiera scenariusz ``reward-learning``, napis wybiera
            scenariusz z rejestru, a funkcja zwraca amplitudy kanałów bodźca
            dla czasu w sekundach.
        seed:
            Ziarno generatora NumPy kontrolujące szum stanu i oscylatorów.
        oscillator_params:
            Parametry fenomenologicznego banku oscylatorów Wilsona-Cowana.
        oscillator_band_map:
            Opcjonalne przypisanie modułów do pasm EEG.

        Raises:
        ------
        ValueError
            Gdy funkcja bodźca nie zwraca wszystkich wymaganych kanałów.
        TypeError
            Gdy ``stimulus`` nie jest identyfikatorem, funkcją ani ``None``.
        """
        self.p: BrainParams = params or BrainParams()
        self.rng: np.random.Generator = np.random.default_rng(seed)

        self.names: list[str] = MODULES
        self.idx: dict[str, int] = {name: i for i, name in enumerate(self.names)}
        self.n: int = len(self.names)

        self.tau: np.ndarray = np.array(TAU)
        self.W: np.ndarray = build_connectivity(self.names)

        self.scenario_id: str | None = None
        self.scenario: StimulusScenario | None = None
        self.stimulus_fn: StimulusFn
        if stimulus is None:
            self.scenario_id = "reward-learning"
            self.scenario = get_scenario(self.scenario_id)
            self.stimulus_fn = build_stimulus_fn(self.scenario)
        elif isinstance(stimulus, str):
            self.scenario_id = stimulus
            self.scenario = get_scenario(stimulus)
            self.stimulus_fn = build_stimulus_fn(self.scenario)
        elif callable(stimulus):
            probe = stimulus(0.0)
            required = set(CHANNELS)
            if not isinstance(probe, dict) or not required.issubset(probe):
                raise ValueError(
                    f"Callable stimulus must return dict with required channels: {CHANNELS}"
                )
            self.stimulus_fn = stimulus
        else:
            raise TypeError("stimulus must be None, scenario id (str), or callable")

        self.oscillator_bank: WilsonCowanOscillatorBank = WilsonCowanOscillatorBank(
            module_names=self.names,
            connectivity=self.W,
            band_map=oscillator_band_map,
            params=oscillator_params,
        )

    def initial_state(self) -> np.ndarray:
        """
        Stan początkowy modelu.

        DMN i pamięć semantyczna mają umiarkowaną aktywność spoczynkową.
        """
        x = np.zeros(self.n)
        x[self.idx["DMN"]] = 0.45
        x[self.idx["SEM"]] = 0.25
        return x

    def compute_prediction_error(
        self, x: np.ndarray, u: StimulusChannels
    ) -> tuple[float, float, float]:
        """
        Uproszczony mechanizm predictive processing.

        Pamięć semantyczna i bufor epizodyczny generują predykcje sensoryczne.
        Różnica między bodźcem a predykcją tworzy błąd predykcji.
        """
        SEM = self.idx["SEM"]
        EPIS = self.idx["EPIS"]

        pred_visual = 0.45 * x[SEM] + 0.30 * x[EPIS]
        pred_auditory = 0.40 * x[SEM] + 0.25 * x[EPIS]

        err_visual = u["visual"] - pred_visual
        err_auditory = u["auditory"] - pred_auditory

        total_error = abs(err_visual) + abs(err_auditory)

        return err_visual, err_auditory, total_error

    def compute_neuromodulation(
        self, x: np.ndarray, u: StimulusChannels, prediction_error: float
    ) -> tuple[float, float, float, float, float, float, float, float]:
        """
        Bardzo uproszczone zmienne neuromodulacyjne.

        dopamine_delta:
            błąd predykcji nagrody.
        noradrenaline:
            pobudzenie zależne od niepewności, zaskoczenia i zagrożenia.
        acetylcholine:
            wzrost precyzji sygnałów związany z zadaniem i uwagą.
        serotonin:
            modulacja nastroju, hamowania impulsywności i odporności na stresory.
        gaba:
            dominująca inhibicja stabilizująca pobudzenie sieci.
        glutamate:
            dominujące pobudzenie i wzmacnianie transmisji korowej.
        endorphins:
            analgezja i redukcja awersyjnej odpowiedzi na stres.
        cortisol:
            hormonalna odpowiedź stresowa HPA, rośnie przy zagrożeniu i utrzymanym błędzie.
        """
        VAL = self.idx["VAL"]
        ATT = self.idx["ATT"]

        dopamine_delta = u["reward"] - x[VAL]
        noradrenaline = sigmoid(prediction_error + u["threat"] - 0.45)
        acetylcholine = sigmoid(u["task_cue"] + x[ATT] - 0.55)

        serotonin = sigmoid(
            0.70 * u["reward"] - 0.45 * u["threat"] + 0.25 * x[self.idx["DMN"]] - 0.2
        )
        gaba = sigmoid(
            0.55 * x[self.idx["ATT"]]
            + 0.35 * x[self.idx["EXEC"]]
            + 0.30 * u["interoceptive"]
            - 0.45
        )
        glutamate = sigmoid(
            0.70 * u["visual"]
            + 0.65 * u["auditory"]
            + 0.50 * u["task_cue"]
            + 0.35 * prediction_error
            - 0.4
        )
        endorphins = sigmoid(
            0.65 * u["reward"] + 0.40 * u["threat"] + 0.30 * u["interoceptive"] - 0.35
        )
        cortisol = sigmoid(
            0.80 * u["threat"]
            + 0.45 * prediction_error
            + 0.30 * u["task_cue"]
            - 0.40 * serotonin
            - 0.20
        )

        return (
            float(dopamine_delta),
            float(noradrenaline),
            float(acetylcholine),
            float(serotonin),
            float(gaba),
            float(glutamate),
            float(endorphins),
            float(cortisol),
        )

    def compute_global_workspace(self, x: np.ndarray) -> float:
        """
        Nieliniowy zapłon global workspace.

        Gdy aktywacja uwagi, kontroli wykonawczej, bufora epizodycznego
        lub salience przekracza próg, reprezentacja staje się globalnie dostępna.
        """
        candidate = max(
            x[self.idx["ATT"]],
            x[self.idx["EXEC"]],
            x[self.idx["EPIS"]],
            x[self.idx["SAL"]],
        )
        return cast(
            float, sigmoid(candidate - self.p.gw_threshold, beta=self.p.gw_gain)
        )

    def _add_drive_to_module_regions(
        self, external: np.ndarray, module_name: str, value: float
    ) -> None:
        """Rozdziel zewnętrzny napęd modułu na odpowiadające mu regiony.

        ``external`` jest wektorem napędów o długości liczby modułów/regionów,
        ``module_name`` wskazuje moduł poznawczy, a ``value`` jest skalarną
        amplitudą napędu. Brak mapowanych regionów kończy funkcję bez zmian.
        """
        regions = [r for r in regions_for_module(module_name) if r in self.idx]
        if not regions:
            return
        share = value / len(regions)
        for region in regions:
            external[self.idx[region]] += share

    def build_external_drive(
        self,
        x: np.ndarray,
        u: StimulusChannels,
        err_visual: float,
        err_auditory: float,
        prediction_error: float,
        acetylcholine: float,
    ) -> np.ndarray:
        """Zbuduj wektor zewnętrznego pobudzenia dla bieżącego kroku modelu.

        Łączy aktywność stanu ``x``, kanały bodźców ``u``, błędy predykcji i
        acetylocholinę w wektor długości ``n``. Wartości są bezwymiarowymi
        amplitudami modelu; brak wymaganych kluczy lub indeksów propaguje wyjątek.
        """
        VIS = self.idx["VIS"]
        AUD = self.idx["AUD"]
        INT = self.idx["INT"]
        ATT = self.idx["ATT"]

        external = np.zeros(self.n)

        precision_gain = 0.6 + 1.4 * x[ATT]

        external[VIS] += precision_gain * u["visual"]
        external[AUD] += precision_gain * u["auditory"]
        external[INT] += u["interoceptive"]
        self._add_drive_to_module_regions(
            external, "SAL", 0.8 * u["threat"] + 0.4 * prediction_error
        )
        self._add_drive_to_module_regions(
            external, "ATT", 0.5 * u["task_cue"] + 0.25 * acetylcholine
        )
        self._add_drive_to_module_regions(external, "EXEC", 0.35 * u["task_cue"])

        external[VIS] += 0.65 * err_visual
        external[AUD] += 0.65 * err_auditory
        self._add_drive_to_module_regions(external, "SAL", 0.40 * prediction_error)

        return external

    def build_global_broadcast(self, gw_ignition: float) -> np.ndarray:
        """
        Global workspace wzmacnia aktywność systemów zadaniowych
        i hamuje DMN w warunkach aktywnej kontroli.
        """
        broadcast = np.zeros(self.n)
        broadcast += 0.25 * gw_ignition
        broadcast[self.idx["DMN"]] -= 0.25 * gw_ignition
        return broadcast

    def step(
        self,
        x: np.ndarray,
        t: float,
        external_drive: np.ndarray | None = None,
    ) -> tuple[np.ndarray, StepDiagnostics]:
        """Wykonuje pojedynczy krok integracji modelu dla czasu t.

        Parameters
        ----------
        x:
            Bieżący wektor aktywacji regionów neural-mass.
        t:
            Czas symulacji w sekundach.
        external_drive:
            Opcjonalny, jawny wektor dodatkowego wejścia regionalnego, np.
            opóźnione sprzężenie zwrotne SNN dla regionu HIP.

        Returns:
        -------
        tuple[np.ndarray, StepDiagnostics]
            Następny stan aktywacji i diagnostyka kroku.

        Raises:
        ------
        ValueError
            Gdy external_drive ma niepoprawny kształt lub wartości nieskończone.
        """
        p = self.p
        u = self.stimulus_fn(t)

        err_visual, err_auditory, prediction_error = self.compute_prediction_error(x, u)

        (
            dopamine_delta,
            noradrenaline,
            acetylcholine,
            serotonin,
            gaba,
            glutamate,
            endorphins,
            cortisol,
        ) = self.compute_neuromodulation(
            x=x,
            u=u,
            prediction_error=prediction_error,
        )

        gw_ignition = self.compute_global_workspace(x)

        external = self.build_external_drive(
            x=x,
            u=u,
            err_visual=err_visual,
            err_auditory=err_auditory,
            prediction_error=prediction_error,
            acetylcholine=acetylcholine,
        )
        if external_drive is not None:
            external_drive_arr = np.asarray(external_drive, dtype=float)
            if external_drive_arr.shape != (self.n,):
                raise ValueError("external_drive musi mieć kształt zgodny z regionami")
            if not np.all(np.isfinite(external_drive_arr)):
                raise ValueError("external_drive musi zawierać wartości skończone")
            external += external_drive_arr

        # Wartościowanie przez błąd predykcji nagrody.
        external[self.idx["VAL"]] += 0.50 * dopamine_delta

        recurrent = self.W @ x
        global_broadcast = self.build_global_broadcast(gw_ignition)

        target = sigmoid(recurrent + external + global_broadcast - 0.35, beta=3.5)

        dx = (-x + target) / self.tau

        dx = apply_state_learning(
            dx=dx,
            x=x,
            diagnostics={"gw_ignition": gw_ignition, "dopamine_delta": dopamine_delta},
            params=p,
            idx=self.idx,
        )

        # Osobna aktualizacja global workspace.
        dx[self.idx["GW"]] += (-x[self.idx["GW"]] + gw_ignition) / self.tau[
            self.idx["GW"]
        ]

        noise = p.noise * self.rng.normal(size=self.n)

        x_next = x + p.dt * dx + np.sqrt(p.dt) * noise
        x_next = np.clip(x_next, 0.0, 1.0)

        diagnostics: StepDiagnostics = {
            "prediction_error": prediction_error,
            "dopamine_delta": dopamine_delta,
            "noradrenaline": noradrenaline,
            "acetylcholine": acetylcholine,
            "serotonin": serotonin,
            "gaba": gaba,
            "glutamate": glutamate,
            "endorphins": endorphins,
            "cortisol": cortisol,
            "gw_ignition": gw_ignition,
            "weight_updates": {},
        }

        self.W = update_connectivity(
            W=self.W,
            x=x_next,
            diagnostics=diagnostics,
            params=p,
            idx=self.idx,
        )

        return x_next, diagnostics

    def simulate(
        self,
        T: float = 45.0,
        progress_callback: Callable[[float], None] | None = None,
        external_drive_callback: (
            Callable[
                [int, float, np.ndarray, np.ndarray, np.ndarray], np.ndarray | None
            ]
            | None
        ) = None,
    ) -> SimulationResult:
        """Przeprowadza pełną symulację modelu w przedziale czasowym od 0 do T.

        Parameters
        ----------
        T:
            Czas trwania symulacji w sekundach.
        progress_callback:
            Opcjonalne wywołanie raportujące postęp symulacji.
        external_drive_callback:
            Funkcja zwracająca dodatkowe wejście regionalne dla bieżącego kroku.
            Używana do jawnego sprzężenia zwrotnego SNN -> neural-mass.

        Returns:
        -------
        SimulationResult
            Krotka zawierająca wektor czasu, macierz aktywności modułów,
            szeregi diagnostyczne, sygnały oscylacyjne oraz metryki zachowania.
        """
        steps = int(T / self.p.dt)
        time = np.arange(steps) * self.p.dt

        x = self.initial_state()
        oscillator_state = self.oscillator_bank.initial_state(self.rng)

        activity = np.zeros((steps, self.n))
        eeg = np.zeros((steps, self.n))
        excitatory = np.zeros((steps, self.n))
        inhibitory = np.zeros((steps, self.n))
        band_power = {
            "theta": np.zeros(steps),
            "alpha": np.zeros(steps),
            "beta": np.zeros(steps),
            "gamma": np.zeros(steps),
        }

        behavior: BehaviorOutputs = {
            "decision": np.empty(steps, dtype=object),
            "latency": np.zeros(steps),
            "confidence": np.zeros(steps),
            "decision_score": np.zeros(steps),
            "decision_event": np.zeros(steps, dtype=bool),
        }

        diagnostics: SimulationDiagnostics = {
            "prediction_error": np.zeros(steps),
            "dopamine_delta": np.zeros(steps),
            "noradrenaline": np.zeros(steps),
            "acetylcholine": np.zeros(steps),
            "serotonin": np.zeros(steps),
            "gaba": np.zeros(steps),
            "glutamate": np.zeros(steps),
            "endorphins": np.zeros(steps),
            "cortisol": np.zeros(steps),
            "gw_ignition": np.zeros(steps),
        }

        weight_history: list[WeightUpdateMap] = []

        prev_decision = "wait"

        progress_stride = max(1, steps // 100)

        diagnostic_keys = (
            "prediction_error",
            "dopamine_delta",
            "noradrenaline",
            "acetylcholine",
            "serotonin",
            "gaba",
            "glutamate",
            "endorphins",
            "cortisol",
            "gw_ignition",
        )

        for k, t in enumerate(time):
            activity[k] = x

            if self.p.enable_oscillators:
                oscillator_state, eeg_vector, power = self.oscillator_bank.step(
                    state=oscillator_state,
                    cognitive_activity=x,
                    dt=self.p.dt,
                    rng=self.rng,
                )
                eeg[k] = eeg_vector
                excitatory[k] = oscillator_state[:, 0]
                inhibitory[k] = oscillator_state[:, 1]
                for band in band_power:
                    band_power[band][k] = power[band]

            sample = map_behavior_state(
                x=x,
                idx=self.idx,
                dt=self.p.dt,
                step_index=k,
                decision_threshold=self.p.decision_threshold,
                confidence_gain=self.p.confidence_gain,
            )
            behavior["decision"][k] = sample.decision
            behavior["latency"][k] = sample.latency
            behavior["confidence"][k] = sample.confidence
            behavior["decision_score"][k] = sample.decision_score
            behavior["decision_event"][k] = (
                sample.decision != "wait" and prev_decision == "wait"
            )
            prev_decision = sample.decision

            external_drive = None
            if external_drive_callback is not None:
                external_drive = external_drive_callback(
                    k,
                    float(t),
                    x.copy(),
                    excitatory[k].copy(),
                    inhibitory[k].copy(),
                )

            x, diag = self.step(x, t, external_drive=external_drive)

            for key in diagnostic_keys:
                diagnostic_series = cast(np.ndarray, diagnostics[key])
                diagnostic_series[k] = cast(float, diag[key])

            weight_updates = cast(WeightUpdateMap, diag.get("weight_updates", {}))
            weight_history.append(weight_updates)
            if progress_callback and (k % progress_stride == 0 or k == steps - 1):
                progress_callback((k + 1) / steps)

        if self.scenario is not None:
            scenario_metadata = self.scenario.to_metadata()
        else:
            scenario_metadata = {
                "scenario_id": "custom-callable",
                "scenario_name": "custom-callable",
                "scenario_description": "User-provided callable stimulus.",
                "schema_version": "callable-v1",
                "duration_hint": T,
                "tags": ["custom"],
                "phases": [],
                "events": [],
                "context": {},
            }

        diagnostics["weight_history"] = build_weight_history_series(
            weight_history, steps
        )

        oscillations: OscillationOutputs = {
            "eeg": eeg,
            "excitatory": excitatory,
            "inhibitory": inhibitory,
            "band_power": band_power,
            "module_bands": self.oscillator_bank.module_bands,
            "frequency": self.oscillator_bank.frequency,
            "metadata": scenario_metadata,
        }

        return cast(
            SimulationResult, (time, activity, diagnostics, oscillations, behavior)
        )
