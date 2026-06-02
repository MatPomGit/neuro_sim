from __future__ import annotations

import re
import warnings
from functools import lru_cache
from pathlib import Path
from textwrap import fill
from typing import Any

import matplotlib.pyplot as plt

from .stimuli import build_stimulus_fn

SVG_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "svg"
SVG_VIEW_FILES = {
    "axial": SVG_ASSETS_DIR / "brain_axial_inline_regions.svg",
    "coronal": SVG_ASSETS_DIR / "brain_coronal_inline_regions.svg",
    "sagittal": SVG_ASSETS_DIR / "brain_sagittal_inline_regions.svg",
    "lateral": SVG_ASSETS_DIR / "brain_lateral_inline_regions.svg",
}


INTERPRETATION_BOX_STYLE = {
    "facecolor": "#f8fafc",
    "edgecolor": "#94a3b8",
    "boxstyle": "round,pad=0.45",
    "alpha": 0.96,
}


def _add_interpretation_box(fig: Any, text: str) -> None:
    """Dodaj pod wykresem stałe pole z opisem interpretacji."""
    wrapped_text = fill(text, width=150)
    line_count = wrapped_text.count("\n") + 1
    fig.text(
        0.01, 0.01, wrapped_text, ha="left", va="bottom",
        fontsize=9, bbox=INTERPRETATION_BOX_STYLE,
    )
    fig._neuro_sim_interpretation_bottom = min(0.34, 0.10 + line_count * 0.035)


def _apply_interpretation_layout(fig: Any) -> None:
    """Dopasuj układ figury do opcjonalnego pola opisu interpretacyjnego."""
    bottom = getattr(fig, "_neuro_sim_interpretation_bottom", None)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="This figure includes Axes that are not compatible with tight_layout.*",
            category=UserWarning,
        )
        if bottom is None:
            fig.tight_layout()
        else:
            fig.tight_layout(rect=(0.0, float(bottom), 1.0, 1.0))


@lru_cache(maxsize=8)
def _load_svg_region_shapes(svg_path: str) -> dict[str, tuple[list[float], list[float]]]:
    """Wczytaj przybliżone kontury regionów SVG jako tło rzutów mózgu."""
    text = Path(svg_path).read_text(encoding="utf-8")
    region_matches = re.findall(r'<path[^>]*data-region="([^"]+)"[^>]*d="([^"]+)"', text)
    shapes = {}
    for region, d_attr in region_matches:
        numbers = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_attr)]
        if len(numbers) >= 4:
            shapes[region] = (numbers[0::2], numbers[1::2])
    return shapes


def _plot_svg_region_background(
    ax: Any, shapes: dict[str, tuple[list[float], list[float]]]
) -> None:
    """Narysuj lekkie kontury regionów SVG jako tło mapy aktywacji."""
    for xs, ys in shapes.values():
        ax.plot(xs, ys, color="#64748b", linewidth=0.45, alpha=0.35, zorder=1)
        ax.fill(xs, ys, color="#e2e8f0", alpha=0.08, zorder=0)


def _set_svg_data_limits(ax: Any, shapes: dict[str, tuple[list[float], list[float]]]) -> None:
    """Dopasuj zakres osi do rzeczywistych współrzędnych regionów SVG."""
    all_x = [x for xs, _ in shapes.values() for x in xs]
    all_y = [y for _, ys in shapes.values() for y in ys]
    if not all_x or not all_y:
        ax.set_xlim(0, 2048)
        ax.set_ylim(2048, 0)
        return
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    ax.set_xlim(x_min - max((x_max - x_min) * 0.06, 1.0), x_max + max((x_max - x_min) * 0.06, 1.0))
    ax.set_ylim(y_max + max((y_max - y_min) * 0.06, 1.0), y_min - max((y_max - y_min) * 0.06, 1.0))

MODULE_DESCRIPTIONS = {
    "VIS": "Przetwarzanie wzrokowe.",
    "AUD": "Przetwarzanie słuchowe.",
    "INT": "Sygnały interoceptywne.",
    "SAL": "Sieć salience: istotność, zaskoczenie i zagrożenie.",
    "ATT": "Uwaga i wzmocnienie precyzji sygnałów.",
    "PHON": "Pętla fonologiczna pamięci roboczej.",
    "VSWM": "Wzrokowo-przestrzenna pamięć robocza.",
    "EXEC": "Kontrola wykonawcza i utrzymanie celu zadania.",
    "EPIS": "Bufor epizodyczny.",
    "SEM": "Pamięć semantyczna.",
    "HIP": "Hipokamp i integracja epizodyczna.",
    "VAL": "Wartościowanie i sygnał nagrody.",
    "MOT": "Przygotowanie odpowiedzi ruchowej.",
    "DMN": "Default mode network: aktywność spoczynkowa.",
    "GW": "Global workspace: globalne udostępnienie reprezentacji.",
}

DIAGNOSTIC_DESCRIPTIONS = {
    "błąd predykcji": "Różnica między bodźcem a predykcją sensoryczną.",
    "global workspace ignition": "Nieliniowy zapłon global workspace.",
    "błąd predykcji nagrody": "Różnica między nagrodą a aktualnym wartościowaniem.",
    "noradrenalina": "Pobudzenie zależne od niepewności, zaskoczenia i zagrożenia.",
    "acetylocholina": "Wzrost precyzji sygnałów związany z zadaniem i uwagą.",
    "serotonina": "Regulacja nastroju i obniżanie reaktywności na stresory.",
    "gaba": "Dominująca inhibicja stabilizująca pobudzenie sieci neuronowych.",
    "glutaminian": "Dominujący neuroprzekaźnik pobudzający wzmacniający transmisję korową.",
    "endorfiny": "Endogenna analgezja i tłumienie awersyjnego komponentu stresu.",
    "kortyzol": "Hormonalna odpowiedź stresowa osi HPA, rośnie przy zagrożeniu i niepewności.",
}

BAND_DESCRIPTIONS = {
    "theta": "Pasmo theta: hipokamp, bufor epizodyczny i pamięć robocza.",
    "alpha": "Pasmo alfa: hamowanie i bramkowanie sensoryczne.",
    "beta": "Pasmo beta: kontrola wykonawcza i nastawienie zadaniowe.",
    "gamma": "Pasmo gamma: lokalne wiązanie cech i reprezentacji.",
}

REGION_TO_MODULE_WEIGHTS = {
    "DLPFC_L": [("EXEC", 0.6), ("VSWM", 0.4)],
    "DLPFC_R": [("EXEC", 0.6), ("VSWM", 0.4)],
    "OFC_L": [("VAL", 1.0)],
    "OFC_R": [("VAL", 1.0)],
    "ACC": [("SAL", 0.45), ("EXEC", 0.35), ("GW", 0.2)],
    "M1_L": [("MOT", 1.0)],
    "M1_R": [("MOT", 1.0)],
    "S1_L": [("INT", 0.6), ("ATT", 0.4)],
    "S1_R": [("INT", 0.6), ("ATT", 0.4)],
    "IPS_L": [("ATT", 0.65), ("VSWM", 0.35)],
    "IPS_R": [("ATT", 0.65), ("VSWM", 0.35)],
    "A1_L": [("AUD", 1.0)],
    "A1_R": [("AUD", 1.0)],
    "STG_L": [("AUD", 0.6), ("PHON", 0.4)],
    "STG_R": [("AUD", 0.6), ("PHON", 0.4)],
    "IFG_L": [("PHON", 0.75), ("EXEC", 0.25)],
    "IFG_R": [("PHON", 0.75), ("EXEC", 0.25)],
    "Insula_L": [("SAL", 0.6), ("INT", 0.4)],
    "Insula_R": [("SAL", 0.6), ("INT", 0.4)],
    "Thalamus_L": [("GW", 0.8), ("ATT", 0.2)],
    "Thalamus_R": [("GW", 0.8), ("ATT", 0.2)],
    "BasalGanglia_L": [("VAL", 0.55), ("MOT", 0.45)],
    "BasalGanglia_R": [("VAL", 0.55), ("MOT", 0.45)],
    "HIP_L": [("HIP", 0.7), ("EPIS", 0.3)],
    "HIP_R": [("HIP", 0.7), ("EPIS", 0.3)],
    "AMY_L": [("SAL", 0.6), ("VAL", 0.4)],
    "AMY_R": [("SAL", 0.6), ("VAL", 0.4)],
    "PCC": [("DMN", 0.65), ("EPIS", 0.35)],
    "mPFC": [("DMN", 0.55), ("GW", 0.25), ("VAL", 0.2)],
    "Angular_L": [("SEM", 0.65), ("DMN", 0.35)],
    "Angular_R": [("SEM", 0.65), ("DMN", 0.35)],
    "V1_L": [("VIS", 1.0)],
    "V1_R": [("VIS", 1.0)],
    "V2_L": [("VIS", 1.0)],
    "V2_R": [("VIS", 1.0)],
    "Cerebellum_L": [("MOT", 0.85), ("ATT", 0.15)],
    "Cerebellum_R": [("MOT", 0.85), ("ATT", 0.15)],
    "Brainstem": [("INT", 0.55), ("SAL", 0.25), ("GW", 0.2)],
}


@lru_cache(maxsize=8)
def _load_svg_region_centroids(svg_path: str) -> dict[str, tuple[float, float]]:
    """Wczytuje plik SVG i oblicza środki ciężkości dla zdefiniowanych regionów."""
    text = Path(svg_path).read_text(encoding="utf-8")
    region_matches = re.findall(r'<path[^>]*data-region="([^"]+)"[^>]*d="([^"]+)"', text)
    centroids = {}
    for region, d_attr in region_matches:
        numbers = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_attr)]
        if len(numbers) < 2:
            continue
        xs = numbers[0::2]
        ys = numbers[1::2]
        if not xs or not ys:
            continue
        centroids[region] = (sum(xs) / len(xs), sum(ys) / len(ys))
    return centroids


def _draw_brain_projection(
    ax: Any, time: Any, activity: Any, idx: Any, svg_path: str, title: str
) -> Any:
    """Narysuj aktywację regionów na tle konturów z wybranego rzutu SVG."""
    centroids = _load_svg_region_centroids(svg_path)
    shapes = _load_svg_region_shapes(svg_path)
    if not centroids:
        ax.text(
            0.5, 0.5, "Brak regionów SVG do wizualizacji.",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.set_title(title)
        return None

    _plot_svg_region_background(ax, shapes)
    region_activity_t = _compute_region_activity_series(activity, idx, centroids.keys())
    region_activity = {region: float(values[-1]) for region, values in region_activity_t.items()}

    xs, ys, vals, labels = [], [], [], []
    for region, (x, y) in centroids.items():
        xs.append(x)
        ys.append(y)
        vals.append(region_activity.get(region, 0.0))
        labels.append(region)

    scatter = ax.scatter(
        xs, ys, c=vals, cmap="magma", vmin=0.0, vmax=1.0, s=95,
        edgecolors="#111827", linewidths=0.4, zorder=3,
    )
    _set_svg_data_limits(ax, shapes)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title)
    ax.text(
        0.02, 0.02, f"T={float(time[-1]):.2f}s\nwartość w ostatnim kroku",
        transform=ax.transAxes, fontsize=8,
        bbox={
            "facecolor": "white", "alpha": 0.8, "edgecolor": "#d1d5db",
            "boxstyle": "round,pad=0.2",
        },
    )
    return scatter

def _compute_region_activity_series(activity: Any, idx: Any, regions: Any) -> Any:
    """Opis funkcji _compute_region_activity_series."""
    region_activity_t = {}
    for region in regions:
        mapping = REGION_TO_MODULE_WEIGHTS.get(region, [])
        if not mapping:
            region_activity_t[region] = activity[:, 0] * 0.0
            continue
        numerator = None
        weight_sum = 0.0
        for module, weight in mapping:
            if module not in idx:
                continue
            values = activity[:, idx[module]]
            numerator = values * weight if numerator is None else numerator + values * weight
            weight_sum += weight
        if numerator is None or weight_sum <= 0.0:
            region_activity_t[region] = activity[:, 0] * 0.0
        else:
            region_activity_t[region] = numerator / weight_sum
    return region_activity_t


def _describe(label: str) -> str:
    """Zwraca polski opis dla podanej etykiety modułu, zmiennej lub pasma."""
    return (
        MODULE_DESCRIPTIONS.get(label)
        or DIAGNOSTIC_DESCRIPTIONS.get(label)
        or BAND_DESCRIPTIONS.get(label)
        or label
    )


def _attach_line_tooltips(fig: Any, axes: Any) -> Any:
    """Opis funkcji _attach_line_tooltips."""
    annotations = {}
    for ax in axes:
        annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "#ffffe0", "ec": "#777777", "alpha": 0.95},
            arrowprops={"arrowstyle": "->", "color": "#777777"},
        )
        annotation.set_visible(False)
        annotations[ax] = annotation

    def hide_annotations() -> Any:
        """Opis funkcji hide_annotations."""
        changed = False
        for annotation in annotations.values():
            if annotation.get_visible():
                annotation.set_visible(False)
                changed = True
        if changed:
            fig.canvas.draw_idle()

    def on_move(event: Any) -> Any:
        """Opis funkcji on_move."""
        if event.inaxes not in axes:
            hide_annotations()
            return

        best = None
        for ax in axes:
            for line in ax.get_lines():
                contains, info = line.contains(event)
                if not contains:
                    continue
                ind = info.get("ind", [0])[0]
                x_data = line.get_xdata()
                y_data = line.get_ydata()
                if len(x_data) == 0:
                    continue
                best = (ax, line, x_data[ind], y_data[ind])
                break
            if best:
                break

        if not best:
            hide_annotations()
            return

        ax, line, x_value, y_value = best
        label = line.get_label()
        for other_ax, other_annotation in annotations.items():
            if other_ax is not ax:
                other_annotation.set_visible(False)
        annotation = annotations[ax]
        annotation.xy = (x_value, y_value)
        annotation.set_text(f"{label}\n{_describe(label)}\nt={x_value:.3g}, y={y_value:.3g}")
        annotation.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)


def _style_lines(ax: Any) -> None:
    """Ustawia parametry interaktywności (picker) dla wszystkich linii na wykresie."""
    for line in ax.get_lines():
        line.set_picker(6)


def draw_activity(ax: Any, time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_activity."""
    selected = [
        "VIS", "AUD", "SAL", "ATT", "PHON", "VSWM",
        "EXEC", "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "GW"
    ]

    for name in selected:
        ax.plot(time, activity[:, idx[name]], label=name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Aktywacja modułu [0-1]")
    ax.set_title("Mezoskopowa dynamika procesów poznawczych")
    ax.legend(ncol=4, fontsize=9)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: każda linia to jeden moduł poznawczy, a skala 0-1 mówi, jak silnie "
        "jest aktywny w danej chwili. Dla osoby początkującej kluczowe są piki i momenty, "
        "w których kilka linii rośnie razem. Dla specjalisty ważna jest kolejność pobudzenia "
        "modułów, czas utrzymywania aktywacji i relacja z bodźcami scenariusza. Najpierw "
        "sprawdź, który moduł dominuje, kiedy się włącza i czy szybko wygasa.",
    )
    _style_lines(ax)
    return [ax]




def draw_simulated_brain_activity(ax: Any, time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_simulated_brain_activity."""
    selected = [
        "VIS", "AUD", "INT", "SAL", "ATT", "PHON", "VSWM",
        "EXEC", "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "GW",
    ]

    labels = [name for name in selected if name in idx]
    if not labels:
        ax.text(
            0.5, 0.5, "Brak danych modułów do wizualizacji.",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.set_title("Symulowana aktywność mózgu")
        return [ax]

    matrix = activity[:, [idx[name] for name in labels]].T
    image = ax.imshow(
        matrix,
        aspect="auto",
        origin="lower",
        extent=[float(time[0]), float(time[-1]), -0.5, len(labels) - 0.5],
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
    )

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Moduł")
    ax.set_title("Symulowana aktywność mózgu (mapa cieplna modułów)")

    colorbar = ax.figure.colorbar(image, ax=ax, pad=0.01)
    colorbar.set_label("Aktywacja [0-1]")
    _add_interpretation_box(
        ax.figure,
        "Mapa cieplna „Aktywność mózgu”. Co widzisz: wiersze to moduły mózgu, "
        "kolumny to czas, a kolor pokazuje aktywację "
        "od ciemnej niskiej do jasnej wysokiej. Dla osoby początkującej najważniejsze są "
        "jasne pasy i bloki, bo pokazują kiedy model jest najbardziej zaangażowany. Dla "
        "specjalisty kluczowa jest synchronizacja modułów, opóźnienia po bodźcach i przejścia "
        "między stanami. Zacznij od najjaśniejszych obszarów i sprawdź, które moduły świecą razem.",
    )
    return [ax]


def draw_brain_region_projections(ax: Any, time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_brain_region_projections."""
    fig = ax.figure
    ax.remove()
    axes = fig.subplots(2, 2)

    views = [
        (str(SVG_VIEW_FILES["axial"]), "Axial"),
        (str(SVG_VIEW_FILES["coronal"]), "Coronal"),
        (str(SVG_VIEW_FILES["sagittal"]), "Sagittal"),
        (str(SVG_VIEW_FILES["lateral"]), "Lateral"),
    ]

    scatter_ref = None
    for sub_ax, (svg, label) in zip(axes.flatten(), views):
        scatter = _draw_brain_projection(sub_ax, time, activity, idx, svg, f"{label}: regiony SVG")
        if scatter is not None:
            scatter_ref = scatter

    if scatter_ref is not None:
        cbar = fig.colorbar(scatter_ref, ax=axes.ravel().tolist(), fraction=0.02, pad=0.01)
        cbar.set_label("Aktywacja [0-1]")
    fig.suptitle("Aktywacja regionów mózgu na 4 rzutach (na bazie szkieletu SVG)")
    _add_interpretation_box(
        fig,
        "Rzuty SVG pokazują aktywację regionów. Co widzisz: każdy panel to inny "
        "rzut mózgu, a szare kontury dają orientacyjny kontekst "
        "anatomiczny, a kolor punktu pokazuje aktywację regionu w ostatnim kroku symulacji. "
        "Dla osoby początkującej kluczowe jest, gdzie pojawiają się najjaśniejsze punkty. "
        "Dla specjalisty ważne jest, czy aktywacja tworzy lokalne ognisko, "
        "wzorzec boczny/lewy-prawy "
        "albo rozlane pobudzenie. Zakres osi pochodzi z rzeczywistych współrzędnych danego SVG, "
        "więc widok lateral nie jest rozciągany do sztucznej skali.",
    )
    return list(axes.flatten())


def draw_region_activity_2d(ax: Any, time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_region_activity_2d."""
    region_names = sorted(REGION_TO_MODULE_WEIGHTS.keys())
    region_activity_t = _compute_region_activity_series(activity, idx, region_names)
    matrix = [region_activity_t[name] for name in region_names]
    image = ax.imshow(
        matrix,
        aspect="auto",
        origin="lower",
        extent=[float(time[0]), float(time[-1]), -0.5, len(region_names) - 0.5],
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
    )
    ax.set_yticks(range(len(region_names)))
    ax.set_yticklabels(region_names, fontsize=7)
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Region mózgu")
    ax.set_title("Aktywacja regionów mózgu w czasie (2D)")
    cbar = ax.figure.colorbar(image, ax=ax, pad=0.01)
    cbar.set_label("Aktywacja [0-1]")
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: każdy wiersz to region mózgu, a kolor pokazuje jego aktywację w czasie. "
        "Dla osoby początkującej najważniejsze są jasne pasy: długi pas oznacza "
        "utrzymaną aktywność, "
        "a krótka plama impuls. Dla specjalisty kluczowe są grupy regionów aktywujące się razem, "
        "opóźnienia między regionami i momenty przełączenia sieci. Porównuj ten "
        "wykres z rzutami SVG, "
        "żeby połączyć czas aktywacji z położeniem regionów.",
    )
    return [ax]
def draw_diagnostics(ax: Any, time: Any, diagnostics: Any) -> Any:
    """Opis funkcji draw_diagnostics."""
    ax.plot(time, diagnostics["prediction_error"], label="błąd predykcji")
    ax.plot(time, diagnostics["gw_ignition"], label="global workspace ignition")
    ax.plot(time, diagnostics["dopamine_delta"], label="błąd predykcji nagrody")
    ax.plot(time, diagnostics["noradrenaline"], label="noradrenalina")
    ax.plot(time, diagnostics["acetylcholine"], label="acetylocholina")
    ax.plot(time, diagnostics["serotonin"], label="serotonina")
    ax.plot(time, diagnostics["gaba"], label="gaba")
    ax.plot(time, diagnostics["glutamate"], label="glutaminian")
    ax.plot(time, diagnostics["endorphins"], label="endorfiny")
    ax.plot(time, diagnostics["cortisol"], label="kortyzol")

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Wartość")
    ax.set_title("Zmienne obliczeniowe i neuromodulacyjne")
    ax.legend()
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: linie pokazują zmienne pomocnicze modelu, np. błąd predykcji, zapłon "
        "global workspace i neuromodulatory. Dla osoby początkującej kluczowe są wspólne piki, "
        "bo oznaczają momenty zaskoczenia, stresu albo silnej zmiany stanu. Dla specjalisty ważne "
        "są zależności czasowe: czy noradrenalina/kortyzol rosną po błędzie, a GABA/glutaminian "
        "stabilizują pobudzenie. Nie interpretuj pojedynczej linii w oderwaniu od reszty.",
    )
    _style_lines(ax)
    return [ax]




def draw_weight_trajectories(ax: Any, time: Any, diagnostics: Any) -> Any:
    """Opis funkcji draw_weight_trajectories."""
    history = diagnostics.get("weight_history", {})
    weights = history.get("weights", {})

    if not weights:
        ax.text(
            0.5, 0.5, "Brak adaptacji wag lub brak wybranych par modułów.",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.set_title("Trajektorie wybranych wag W")
        ax.set_xlabel("Czas symulacji [s]")
        ax.set_ylabel("Waga")
        return [ax]

    for pair_name, values in sorted(weights.items()):
        ax.plot(time, values, label=pair_name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Wartość wagi")
    ax.set_title("Trajektorie adaptowanych wag W")
    ax.legend(fontsize=8, ncol=2)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: każda linia to siła wybranego połączenia między modułami. Dla osoby "
        "początkującej kluczowe jest, czy linia rośnie, spada czy pozostaje "
        "stabilna. Dla specjalisty "
        "ważne są trwałe trendy po fazach treningu, przecięcia trajektorii "
        "i pary połączeń reagujące "
        "na konkretne zdarzenia. Najwięcej znaczą zmiany utrzymujące się po bodźcu, "
        "a nie pojedynczy szum.",
    )
    _style_lines(ax)
    return [ax]


def draw_weight_deltas(ax: Any, time: Any, diagnostics: Any) -> Any:
    """Opis funkcji draw_weight_deltas."""
    history = diagnostics.get("weight_history", {})
    deltas = history.get("deltas", {})

    if not deltas:
        ax.text(
            0.5, 0.5, "Brak zmian wag do wizualizacji.",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.set_title("Zmiany wag ΔW")
        ax.set_xlabel("Czas symulacji [s]")
        ax.set_ylabel("ΔW / krok")
        return [ax]

    for pair_name, values in sorted(deltas.items()):
        ax.plot(time, values, label=pair_name)

    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("ΔW / krok")
    ax.set_title("Przyrosty adaptowanych wag")
    ax.legend(fontsize=8, ncol=2)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: ΔW pokazuje zmianę wagi w pojedynczym kroku, czyli tempo uczenia. Dla osoby "
        "początkującej wartości powyżej zera oznaczają wzmacnianie połączenia, "
        "poniżej zera osłabianie, "
        "a okolice zera brak istotnej zmiany. Dla specjalisty kluczowe są serie "
        "impulsów po bodźcach, "
        "znak zmian i moment przejścia do stabilizacji. Ten wykres mówi o zmianie, "
        "nie o samej wielkości wagi.",
    )
    _style_lines(ax)
    return [ax]
def draw_eeg_modules(ax: Any, time: Any, oscillations: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_eeg_modules."""
    selected = ["HIP", "VSWM", "VIS", "AUD", "EXEC", "ATT", "SEM", "GW"]
    eeg = oscillations["eeg"]

    available = [name for name in selected if name in idx]
    if not available:
        ax.text(
            0.5, 0.5, "Brak sygnałów EEG modułów.",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.set_title("Oscylatory Wilsona-Cowana dla wybranych modułów")
        return [ax]

    eeg_view = eeg[:, [idx[name] for name in available]]
    offset_step = max(float(eeg_view.max() - eeg_view.min()) * 1.2, 0.25)
    offsets = []
    for order, name in enumerate(available):
        offset = order * offset_step
        offsets.append(offset)
        ax.plot(time, eeg[:, idx[name]] + offset, label=name)

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Moduł EEG (serie przesunięte pionowo)")
    ax.set_yticks(offsets)
    ax.set_yticklabels(available)
    ax.set_title("Oscylatory Wilsona-Cowana dla wybranych modułów")
    ax.legend(ncol=4, fontsize=9)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: każdy wiersz to uproszczony sygnał EEG jednego modułu, przesunięty pionowo "
        "tylko po to, aby linie się nie nakładały. Dla osoby początkującej "
        "kluczowe są rytm, wysokość "
        "fal w obrębie wiersza i momenty, gdy kilka modułów ma piki jednocześnie. "
        "Dla specjalisty ważna "
        "jest synchronizacja, różnice fazy i zmiana amplitudy po bodźcach. "
        "Nie porównuj bezwzględnej "
        "wysokości między wierszami, bo przesunięcie jest sztuczne.",
    )
    _style_lines(ax)
    return [ax]




def draw_scenario_channels(ax: Any, time: Any, scenario: Any) -> Any:
    """Opis funkcji draw_scenario_channels."""
    stim = build_stimulus_fn(scenario)
    series = {
        k: []
        for k in ["visual", "auditory", "task_cue", "threat", "reward", "interoceptive"]
    }
    for t in time:
        u = stim(float(t))
        for k in series:
            series[k].append(u[k])

    for k, values in series.items():
        ax.plot(time, values, label=k)
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Amplituda bodźca")
    ax.set_title("Przebieg kanałów bodźców scenariusza")
    ax.legend(ncol=3, fontsize=9)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: linie pokazują bodźce i sygnały wejściowe scenariusza, np. wzrok, dźwięk, "
        "wskazówkę zadania, zagrożenie lub nagrodę. Dla osoby początkującej to mapa tego, co model "
        "dostaje z zewnątrz. Dla specjalisty kluczowe są amplituda, czas trwania "
        "i nakładanie się kanałów. "
        "Używaj tego wykresu jako przyczyny: sprawdzaj, czy aktywność, decyzje "
        "i diagnostyka rosną po bodźcu.",
    )
    _style_lines(ax)
    return [ax]


def draw_scenario_timeline(ax: Any, time: Any, scenario: Any) -> Any:
    """Opis funkcji draw_scenario_timeline."""
    ax.set_title("Oś czasu scenariusza: fazy i zdarzenia")
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_yticks([])

    y = 0.5
    for i, phase in enumerate(scenario.phases):
        w = phase["window"]
        ax.axvspan(w["start"], w["end"], alpha=0.18 + 0.08 * (i % 2), label=phase["name"])

    for event in scenario.events:
        t = event["time"]
        ax.axvline(t, color="black", linestyle="--", linewidth=1.0)
        ax.text(t, y, event["type"], rotation=90, va="bottom", ha="right", fontsize=8)

    ax.set_xlim(float(time[0]), float(time[-1]))
    if scenario.phases:
        ax.legend(loc="upper right", fontsize=8)
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: kolorowe obszary to fazy scenariusza, a pionowe linie "
        "to pojedyncze zdarzenia. "
        "Dla osoby początkującej to legenda czasu: pokazuje, kiedy coś miało się "
        "wydarzyć. Dla specjalisty "
        "kluczowe są granice faz, opóźnienia reakcji modelu po zdarzeniach "
        "i to, czy zmiany pojawiają się "
        "w fazie treningowej, testowej lub stresowej. Zawsze zestawiaj tę oś z innymi wykresami.",
    )
    return [ax]



def draw_behavior(ax: Any, time: Any, behavior: Any) -> Any:
    """Opis funkcji draw_behavior."""
    ax.plot(time, behavior["decision_score"], label="decision score", color="#1f77b4")
    ax.plot(time, behavior["confidence"], label="confidence", color="#2ca02c", alpha=0.9)
    ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)

    decision_times = time[behavior["decision_event"]]
    decision_scores = behavior["decision_score"][behavior["decision_event"]]
    if len(decision_times):
        ax.scatter(
            decision_times, decision_scores, marker="o", color="#d62728",
            label="decision event", zorder=3,
        )

    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Skala decyzyjna")
    ax.set_title("Przebiegi decyzyjne i punkty decyzji")
    ax.legend()
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: wynik decyzji pokazuje kierunek i siłę preferowanej odpowiedzi, "
        "a pewność mówi, "
        "jak stabilna jest ta odpowiedź. Dla osoby początkującej najważniejsze są "
        "czerwone punkty decyzji "
        "i to, czy pojawiają się wtedy, gdy pewność jest wysoka. Dla specjalisty "
        "kluczowe są przekroczenia "
        "progu, oscylacje przed decyzją i zależność od bodźców lub faz scenariusza.",
    )
    _style_lines(ax)
    return [ax]

def draw_band_power(ax: Any, time: Any, oscillations: Any) -> Any:
    """Opis funkcji draw_band_power."""
    band_power = oscillations["band_power"]
    fig = ax.figure
    ax.remove()
    axes = fig.subplots(4, 1, sharex=True)

    for band_ax, band in zip(axes, ["theta", "alpha", "beta", "gamma"]):
        band_ax.plot(time, band_power[band], label=band)
        band_ax.set_ylabel(band)
        band_ax.legend(loc="upper right")
        _style_lines(band_ax)

    axes[0].set_title("Symulowana dynamika pasm EEG")
    axes[-1].set_xlabel("Czas symulacji [s]")
    fig.supylabel("Uproszczona moc pasmowa")
    _add_interpretation_box(
        fig,
        "Co widzisz: każdy panel pokazuje uproszczoną moc jednego pasma EEG: theta, alpha, beta "
        "lub gamma. Dla osoby początkującej najważniejsze są wzrosty danego pasma i ich czas. Dla "
        "specjalisty kluczowe jest, które pasmo reaguje na bodziec: theta często "
        "wiąże się z pamięcią, "
        "alpha z hamowaniem, beta z nastawieniem zadaniowym, a gamma z lokalnym wiązaniem cech. "
        "Porównuj piki z aktywnością modułów i kanałami scenariusza.",
    )
    return list(axes)


def _show_standalone(draw_func: Any, *args: Any, figsize: tuple[int, int] = (14, 6)) -> None:
    """Tworzy nową figurę, uruchamia funkcję rysującą i wyświetla interaktywne okno wykresu."""
    fig, ax = plt.subplots(figsize=figsize)
    axes = draw_func(ax, *args) or [ax]
    _apply_interpretation_layout(fig)
    _attach_line_tooltips(fig, axes)
    plt.show()


def plot_activity(time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji plot_activity."""
    _show_standalone(draw_activity, time, activity, names, idx, figsize=(14, 8))


def plot_diagnostics(time: Any, diagnostics: Any) -> Any:
    """Opis funkcji plot_diagnostics."""
    _show_standalone(draw_diagnostics, time, diagnostics, figsize=(14, 4))


def plot_eeg_modules(time: Any, oscillations: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji plot_eeg_modules."""
    _show_standalone(draw_eeg_modules, time, oscillations, names, idx, figsize=(14, 6))


def plot_band_power(time: Any, oscillations: Any) -> Any:
    """Opis funkcji plot_band_power."""
    _show_standalone(draw_band_power, time, oscillations, figsize=(14, 8))
