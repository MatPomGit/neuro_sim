import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

"""
Interpretacja modułów jest następująca. VIS, AUD i INT reprezentują wejścia sensoryczne i interoceptywne.
SAL wykrywa istotność bodźca, zwłaszcza gdy pojawia się błąd predykcji lub zagrożenie. ATT wzmacnia precyzję sygnałów,
czyli decyduje, które błędy predykcji są silniej przetwarzane. PHON, VSWM, EXEC i EPIS odpowiadają odpowiednio
pętli fonologicznej, szkicownikowi wzrokowo-przestrzennemu, centralnemu systemowi wykonawczemu i buforowi epizodycznemu.
SEM i HIP modelują pamięć semantyczną oraz hipokampalne wiązanie epizodów. VAL koduje oczekiwaną wartość/nagrodę.
DMN konkuruje z kontrolą zadaniową. GW oznacza globalną dostępność reprezentacji.

W praktyce model powinien pokazać, że po pojawieniu się bodźca wzrokowego wzrasta aktywacja VIS, potem ATT, VSWM i EXEC.
Po bodźcu słuchowym aktywuje się AUD, PHON i LANG. Bodziec zagrażający powinien podnieść SAL, INT, noradrenalinę
i chwilowo wzmocnić GW. Nagroda zwiększa sygnał dopaminowy i aktualizuje VAL.
"""

def sigmoid(z, beta=4.0):
    return 1.0 / (1.0 + np.exp(-beta * z))


@dataclass
class BrainParams:
    dt: float = 0.01
    noise: float = 0.015
    gw_threshold: float = 0.62
    gw_gain: float = 10.0
    learning_rate_semantic: float = 0.004
    learning_rate_value: float = 0.02
    decay_semantic: float = 0.001


class CognitiveBrainModel:
    """
    Mezoskopowy model dynamiki poznawczej.

    Moduły:
    VIS     przetwarzanie wzrokowe
    AUD     przetwarzanie słuchowe
    INT     interocepcja
    SAL     salience / detekcja istotności
    ATT     uwaga selektywna
    PHON    pętla fonologiczna
    VSWM    szkicownik wzrokowo-przestrzenny
    EXEC    central executive / kontrola wykonawcza
    EPIS    bufor epizodyczny
    SEM     pamięć semantyczna
    HIP     kodowanie hipokampalne
    VAL     wartościowanie / oczekiwana nagroda
    MOT     planowanie działania
    DMN     default mode network / przetwarzanie wewnętrzne
    LANG    przetwarzanie językowe
    GW      global workspace
    """

    def __init__(self, params=BrainParams(), seed=7):
        self.p = params
        self.rng = np.random.default_rng(seed)

        self.names = [
            "VIS", "AUD", "INT", "SAL", "ATT", "PHON", "VSWM", "EXEC",
            "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "LANG", "GW"
        ]
        self.idx = {name: i for i, name in enumerate(self.names)}
        self.n = len(self.names)

        self.tau = np.array([
            0.08,  # VIS
            0.08,  # AUD
            0.12,  # INT
            0.10,  # SAL
            0.15,  # ATT
            0.25,  # PHON
            0.25,  # VSWM
            0.30,  # EXEC
            0.35,  # EPIS
            0.80,  # SEM
            0.45,  # HIP
            0.40,  # VAL
            0.18,  # MOT
            0.60,  # DMN
            0.30,  # LANG
            0.12,  # GW
        ])

        self.W = np.zeros((self.n, self.n))
        self._build_connectivity()

    def _c(self, target, source, weight):
        self.W[self.idx[target], self.idx[source]] = weight

    def _build_connectivity(self):
        # Sensory -> salience / attention
        self._c("SAL", "VIS", 0.55)
        self._c("SAL", "AUD", 0.50)
        self._c("SAL", "INT", 0.45)

        self._c("ATT", "SAL", 0.65)
        self._c("ATT", "EXEC", 0.35)
        self._c("ATT", "GW", 0.30)

        # Working memory subsystems
        self._c("PHON", "AUD", 0.55)
        self._c("PHON", "LANG", 0.45)
        self._c("VSWM", "VIS", 0.60)
        self._c("VSWM", "ATT", 0.40)

        # Central executive
        self._c("EXEC", "ATT", 0.45)
        self._c("EXEC", "PHON", 0.25)
        self._c("EXEC", "VSWM", 0.25)
        self._c("EXEC", "SAL", 0.35)
        self._c("EXEC", "DMN", -0.25)

        # Episodic buffer and hippocampus
        self._c("EPIS", "PHON", 0.30)
        self._c("EPIS", "VSWM", 0.30)
        self._c("EPIS", "SEM", 0.25)
        self._c("EPIS", "HIP", 0.35)
        self._c("HIP", "EPIS", 0.45)
        self._c("HIP", "ATT", 0.25)

        # Semantic and language systems
        self._c("SEM", "LANG", 0.35)
        self._c("LANG", "AUD", 0.40)
        self._c("LANG", "PHON", 0.35)
        self._c("LANG", "SEM", 0.30)

        # Valuation and action
        self._c("VAL", "SAL", 0.30)
        self._c("VAL", "HIP", 0.25)
        self._c("MOT", "EXEC", 0.45)
        self._c("MOT", "VAL", 0.35)
        self._c("MOT", "SAL", 0.20)

        # Default mode network: konkurencja z kontrolą zadaniową
        self._c("DMN", "SEM", 0.25)
        self._c("DMN", "HIP", 0.25)
        self._c("DMN", "EXEC", -0.35)
        self._c("EXEC", "DMN", -0.30)

        # Global workspace broadcast
        for module in ["ATT", "EXEC", "EPIS", "SEM", "HIP", "LANG", "MOT"]:
            self._c(module, "GW", 0.35)

        self._c("GW", "ATT", 0.40)
        self._c("GW", "EXEC", 0.45)
        self._c("GW", "EPIS", 0.35)
        self._c("GW", "SAL", 0.25)

    def stimulus(self, t):
        """
        Scenariusz eksperymentalny:
        1. pojawia się bodziec wzrokowy,
        2. później bodziec słuchowo-językowy,
        3. następnie bodziec zagrażający,
        4. na końcu sygnał nagrody.
        """
        u = {
            "visual": 0.0,
            "auditory": 0.0,
            "interoceptive": 0.15,
            "task_cue": 0.0,
            "threat": 0.0,
            "reward": 0.0,
        }

        if 2.0 < t < 18.0:
            u["visual"] = 0.9

        if 8.0 < t < 24.0:
            u["auditory"] = 0.75

        if 1.0 < t < 35.0:
            u["task_cue"] = 0.65

        if 22.0 < t < 30.0:
            u["threat"] = 0.85
            u["interoceptive"] = 0.55

        if 34.0 < t < 38.0:
            u["reward"] = 1.0

        return u

    def step(self, x, t):
        p = self.p
        u = self.stimulus(t)

        VIS = self.idx["VIS"]
        AUD = self.idx["AUD"]
        INT = self.idx["INT"]
        SAL = self.idx["SAL"]
        ATT = self.idx["ATT"]
        EXEC = self.idx["EXEC"]
        EPIS = self.idx["EPIS"]
        SEM = self.idx["SEM"]
        HIP = self.idx["HIP"]
        VAL = self.idx["VAL"]
        GW = self.idx["GW"]

        # Predykcje top-down: pamięć semantyczna i epizodyczna przewidują wejście sensoryczne
        pred_visual = 0.45 * x[SEM] + 0.30 * x[EPIS]
        pred_auditory = 0.40 * x[SEM] + 0.25 * x[EPIS]

        err_visual = u["visual"] - pred_visual
        err_auditory = u["auditory"] - pred_auditory
        prediction_error = abs(err_visual) + abs(err_auditory)

        # Neuromodulacja uproszczona
        dopamine_delta = u["reward"] - x[VAL]
        noradrenaline = sigmoid(prediction_error + u["threat"] - 0.45)
        acetylcholine = sigmoid(u["task_cue"] + x[ATT] - 0.55)

        # Uwaga jako precyzja błędu predykcji
        precision_gain = 0.6 + 1.4 * x[ATT]

        external = np.zeros(self.n)
        external[VIS] += precision_gain * u["visual"]
        external[AUD] += precision_gain * u["auditory"]
        external[INT] += u["interoceptive"]
        external[SAL] += 0.8 * u["threat"] + 0.4 * prediction_error
        external[ATT] += 0.5 * u["task_cue"] + 0.25 * acetylcholine
        external[EXEC] += 0.35 * u["task_cue"]
        external[VAL] += 0.50 * dopamine_delta

        # Błąd predykcji bezpośrednio moduluje sensorykę i salience
        error_drive = np.zeros(self.n)
        error_drive[VIS] += 0.65 * err_visual
        error_drive[AUD] += 0.65 * err_auditory
        error_drive[SAL] += 0.40 * prediction_error

        # Global workspace ignition: nieliniowy próg globalnej dostępności
        candidate = max(x[ATT], x[EXEC], x[EPIS], x[SAL])
        gw_ignition = sigmoid(candidate - p.gw_threshold, beta=p.gw_gain)

        global_broadcast = np.zeros(self.n)
        global_broadcast += 0.25 * gw_ignition
        global_broadcast[self.idx["DMN"]] -= 0.25 * gw_ignition

        recurrent = self.W @ x

        target = sigmoid(
            recurrent + external + error_drive + global_broadcast - 0.35,
            beta=3.5
        )

        dx = (-x + target) / self.tau

        # Uczenie semantyczne: powolna konsolidacja przy aktywnym hipokampie i workspace
        dx[SEM] += p.learning_rate_semantic * x[HIP] * gw_ignition
        dx[SEM] -= p.decay_semantic * x[SEM]

        # Uczenie wartościowania: prosty błąd predykcji nagrody
        dx[VAL] += p.learning_rate_value * dopamine_delta

        # Aktualizacja global workspace jako osobnego modułu
        dx[GW] += (-x[GW] + gw_ignition) / self.tau[GW]

        noise = p.noise * self.rng.normal(size=self.n)
        x_next = x + p.dt * dx + np.sqrt(p.dt) * noise
        x_next = np.clip(x_next, 0.0, 1.0)

        diagnostics = {
            "prediction_error": prediction_error,
            "dopamine_delta": dopamine_delta,
            "noradrenaline": noradrenaline,
            "acetylcholine": acetylcholine,
            "gw_ignition": gw_ignition,
        }

        return x_next, diagnostics

    def simulate(self, T=45.0):
        steps = int(T / self.p.dt)
        time = np.arange(steps) * self.p.dt

        x = np.zeros(self.n)
        x[self.idx["DMN"]] = 0.45
        x[self.idx["SEM"]] = 0.25

        X = np.zeros((steps, self.n))
        D = {
            "prediction_error": np.zeros(steps),
            "dopamine_delta": np.zeros(steps),
            "noradrenaline": np.zeros(steps),
            "acetylcholine": np.zeros(steps),
            "gw_ignition": np.zeros(steps),
        }

        for k, t in enumerate(time):
            X[k] = x
            x, diag = self.step(x, t)
            for key in D:
                D[key][k] = diag[key]

        return time, X, D

    def plot(self, time, X, D):
        selected = [
            "VIS", "AUD", "SAL", "ATT", "PHON", "VSWM",
            "EXEC", "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "GW"
        ]

        plt.figure(figsize=(14, 8))
        for name in selected:
            plt.plot(time, X[:, self.idx[name]], label=name)

        plt.xlabel("Czas symulacji [s]")
        plt.ylabel("Aktywacja modułu [0-1]")
        plt.title("Mezoskopowa dynamika procesów poznawczych")
        plt.legend(ncol=4, fontsize=9)
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(14, 4))
        plt.plot(time, D["prediction_error"], label="błąd predykcji")
        plt.plot(time, D["gw_ignition"], label="global workspace ignition")
        plt.plot(time, D["dopamine_delta"], label="błąd predykcji nagrody")
        plt.xlabel("Czas symulacji [s]")
        plt.ylabel("Wartość")
        plt.title("Zmienne obliczeniowe")
        plt.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    model = CognitiveBrainModel()
    time, X, D = model.simulate(T=45.0)
    model.plot(time, X, D)
