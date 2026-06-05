from __future__ import annotations

import re
import warnings
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from textwrap import fill
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection

from .scenarios.types import CHANNELS, StimulusScenario
from .stimuli import build_stimulus_fn

SVG_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "svg"
SVG_VIEW_FILES = {
    "axial": SVG_ASSETS_DIR / "brain_axial_inline_regions.svg",
    "coronal": SVG_ASSETS_DIR / "brain_coronal_inline_regions.svg",
    "sagittal": SVG_ASSETS_DIR / "brain_sagittal_inline_regions.svg",
    "lateral": SVG_ASSETS_DIR / "brain_lateral_inline_regions.svg",
}


INTERPRETATION_WRAP_WIDTH = 90


INTERPRETATION_BOX_STYLE = {
    "facecolor": "#f8fafc",
    "edgecolor": "#94a3b8",
    "boxstyle": "round,pad=0.45",
    "alpha": 0.96,
}


def _add_interpretation_box(fig: Any, text: str) -> None:
    """Dodaj pod wykresem pojedyncze pole z opisem interpretacji."""
    existing_artist = getattr(fig, "_neuro_sim_interpretation_artist", None)
    if existing_artist is not None:
        try:
            existing_artist.remove()
        except ValueError:
            pass

    wrapped_text = fill(text, width=INTERPRETATION_WRAP_WIDTH)
    line_count = wrapped_text.count("\n") + 1
    interpretation_artist = fig.text(
        0.01,
        0.01,
        wrapped_text,
        ha="left",
        va="bottom",
        fontsize=9,
        bbox=INTERPRETATION_BOX_STYLE,
    )
    fig._neuro_sim_interpretation_artist = interpretation_artist
    fig._neuro_sim_interpretation_bottom = min(0.42, 0.10 + line_count * 0.032)


def _parse_svg_translate(transform: str | None) -> tuple[float, float]:
    """Odczytaj przesunięcie `translate(x,y)` ze ścieżek podkładu SVG.

    Parameters
    ----------
    transform:
        Wartość atrybutu `transform` z elementu SVG.

    Returns
    -------
    tuple[float, float]
        Przesunięcie x/y dodawane do współrzędnych ścieżki.
    """
    if not transform:
        return 0.0, 0.0
    match = re.search(
        r"translate\(\s*([-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)"
        r"(?:[\s,]+([-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?))?\s*\)",
        transform,
    )
    if match is None:
        return 0.0, 0.0
    x_offset = float(match.group(1))
    y_offset = float(match.group(2) or 0.0)
    return x_offset, y_offset


def _extract_svg_region_paths(svg_text: str) -> list[tuple[str, str]]:
    """Wydobądź pary region-ścieżka SVG niezależnie od kolejności atrybutów."""
    region_paths = []
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as e:
        warnings.warn(f"Niepoprawny format pliku SVG: {e}", UserWarning)
        return []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "path":
            continue
        region = element.attrib.get("data-region")
        d_attr = element.attrib.get("d")
        if region and d_attr:
            region_paths.append((region, d_attr))
    return region_paths


def _extract_svg_underlay_paths(svg_text: str) -> list[tuple[str, str, str | None]]:
    """Wydobądź nieinteraktywne ścieżki podkładu SVG używane w widoku kompaktowym.

    Parameters
    ----------
    svg_text:
        Treść pliku SVG z warstwą bazową i nakładkami regionów.

    Returns
    -------
    list[tuple[str, str, str | None]]
        Lista krotek `d`, `fill`, `transform` dla ścieżek bez `data-region`.
    """
    underlay_paths = []
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as e:
        warnings.warn(f"Niepoprawny format pliku SVG: {e}", UserWarning)
        return []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "path":
            continue
        d_attr = element.attrib.get("d")
        if element.attrib.get("data-region") or not d_attr:
            continue
        underlay_paths.append(
            (
                d_attr,
                element.attrib.get("fill", "#cbd5e1"),
                element.attrib.get("transform"),
            )
        )
    return underlay_paths


def _split_svg_path_coordinates(
    d_attr: str, *, x_offset: float = 0.0, y_offset: float = 0.0
) -> tuple[list[float], list[float]]:
    """Zamień liczby ze ścieżki SVG na bezpiecznie sparowane współrzędne x/y."""
    numbers = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_attr)]
    coordinate_count = len(numbers) - (len(numbers) % 2)
    paired_numbers = numbers[:coordinate_count]
    xs = [x + x_offset for x in paired_numbers[0::2]]
    ys = [y + y_offset for y in paired_numbers[1::2]]
    return xs, ys


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
def _load_svg_region_shapes(
    svg_path: str,
) -> dict[str, tuple[list[float], list[float]]]:
    """Wczytaj przybliżone kontury regionów SVG jako tło rzutów mózgu."""
    text = Path(svg_path).read_text(encoding="utf-8")
    shapes = {}
    for region, d_attr in _extract_svg_region_paths(text):
        xs, ys = _split_svg_path_coordinates(d_attr)
        if len(xs) >= 2 and len(ys) >= 2:
            shapes[region] = (xs, ys)
    return shapes


@lru_cache(maxsize=8)
def _load_svg_underlay_shapes(
    svg_path: str,
) -> tuple[tuple[tuple[float, ...], tuple[float, ...], str], ...]:
    """Wczytaj podkład anatomiczny SVG zgodny z `brain_viewer_compact.html`.

    Parameters
    ----------
    svg_path:
        Ścieżka do pliku SVG zawierającego bazowy rysunek mózgu i regiony.

    Returns
    -------
    tuple[tuple[tuple[float, ...], tuple[float, ...], str], ...]
        Niemutowalna lista ścieżek podkładu: współrzędne x, współrzędne y i kolor.
    """
    text = Path(svg_path).read_text(encoding="utf-8")
    underlay_shapes = []
    for d_attr, fill_color, transform in _extract_svg_underlay_paths(text):
        x_offset, y_offset = _parse_svg_translate(transform)
        xs, ys = _split_svg_path_coordinates(
            d_attr, x_offset=x_offset, y_offset=y_offset
        )
        if len(xs) >= 2 and len(ys) >= 2:
            underlay_shapes.append((tuple(xs), tuple(ys), fill_color))
    return tuple(underlay_shapes)


def _plot_svg_underlay_background(
    ax: Any,
    underlay_shapes: tuple[tuple[tuple[float, ...], tuple[float, ...], str], ...],
) -> None:
    """Narysuj szary podkład anatomiczny taki jak w kompaktowym viewerze SVG."""
    if not underlay_shapes:
        return
    polygons = [list(zip(xs, ys)) for xs, ys, _ in underlay_shapes]
    fill_colors = [fill_color for _, _, fill_color in underlay_shapes]
    collection = PolyCollection(
        polygons,
        facecolors=fill_colors,
        edgecolors="none",
        alpha=0.30,
        zorder=0,
    )
    ax.add_collection(collection)


def _plot_svg_region_background(
    ax: Any, shapes: dict[str, tuple[list[float], list[float]]]
) -> None:
    """Narysuj lekkie kontury regionów SVG jako nakładkę na podkład mózgu."""
    for xs, ys in shapes.values():
        ax.plot(xs, ys, color="#1f2937", linewidth=0.45, alpha=0.32, zorder=2)
        ax.fill(xs, ys, color="#e2e8f0", alpha=0.10, zorder=1)


def _set_svg_data_limits(
    ax: Any,
    shapes: dict[str, tuple[list[float], list[float]]],
    underlay_shapes: tuple[tuple[tuple[float, ...], tuple[float, ...], str], ...],
) -> None:
    """Dopasuj zakres osi do rzeczywistych współrzędnych regionów i podkładu SVG."""
    all_x = [x for xs, _ in shapes.values() for x in xs]
    all_y = [y for _, ys in shapes.values() for y in ys]
    all_x.extend(x for xs, _, _ in underlay_shapes for x in xs)
    all_y.extend(y for _, ys, _ in underlay_shapes for y in ys)
    if not all_x or not all_y:
        ax.set_xlim(0, 2048)
        ax.set_ylim(2048, 0)
        return
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    ax.set_xlim(
        x_min - max((x_max - x_min) * 0.06, 1.0),
        x_max + max((x_max - x_min) * 0.06, 1.0),
    )
    ax.set_ylim(
        y_max + max((y_max - y_min) * 0.06, 1.0),
        y_min - max((y_max - y_min) * 0.06, 1.0),
    )


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
    centroids = {}
    for region, d_attr in _extract_svg_region_paths(text):
        xs, ys = _split_svg_path_coordinates(d_attr)
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
    underlay_shapes = _load_svg_underlay_shapes(svg_path)
    if not centroids:
        ax.text(
            0.5,
            0.5,
            "Brak regionów SVG do wizualizacji.",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_title(title)
        return None

    _plot_svg_underlay_background(ax, underlay_shapes)
    _plot_svg_region_background(ax, shapes)
    region_activity_t = _compute_region_activity_series(activity, idx, centroids.keys())
    region_activity = {
        region: float(values[-1]) for region, values in region_activity_t.items()
    }

    xs, ys, vals, labels = [], [], [], []
    for region, (x, y) in centroids.items():
        xs.append(x)
        ys.append(y)
        vals.append(region_activity.get(region, 0.0))
        labels.append(region)

    scatter = ax.scatter(
        xs,
        ys,
        c=vals,
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
        s=95,
        edgecolors="#111827",
        linewidths=0.4,
        zorder=3,
    )
    _set_svg_data_limits(ax, shapes, underlay_shapes)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title)
    ax.text(
        0.02,
        0.02,
        f"T={float(time[-1]):.2f}s\nwartość w ostatnim kroku",
        transform=ax.transAxes,
        fontsize=8,
        bbox={
            "facecolor": "white",
            "alpha": 0.8,
            "edgecolor": "#d1d5db",
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
            numerator = (
                values * weight if numerator is None else numerator + values * weight
            )
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
            bbox={
                "boxstyle": "round,pad=0.3",
                "fc": "#ffffe0",
                "ec": "#777777",
                "alpha": 0.95,
            },
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
        annotation.set_text(
            f"{label}\n{_describe(label)}\nt={x_value:.3g}, y={y_value:.3g}"
        )
        annotation.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)


def _style_lines(ax: Any) -> None:
    """Ustawia parametry interaktywności (picker) dla wszystkich linii na wykresie."""
    for line in ax.get_lines():
        line.set_picker(6)


ACTIVITY_MODULE_LABELS = [
    "VIS",
    "AUD",
    "SAL",
    "ATT",
    "PHON",
    "VSWM",
    "EXEC",
    "EPIS",
    "SEM",
    "HIP",
    "VAL",
    "MOT",
    "DMN",
    "GW",
]


def _draw_activity_lines(
    ax: Axes, time: Any, activity: Any, idx: dict[str, int]
) -> dict[Any, Any]:
    """Narysuj linie aktywacji i zwróć mapowanie wpisów legendy na sygnały."""
    lines_by_label: dict[str, Any] = {}
    for name in ACTIVITY_MODULE_LABELS:
        if name in idx:
            (line,) = ax.plot(time, activity[:, idx[name]], label=name)
            lines_by_label[name] = line

    legend = ax.legend(ncol=4, fontsize=9)
    legend_map: dict[Any, Any] = {}
    if legend is None:
        return legend_map

    for legend_line, legend_text in zip(legend.get_lines(), legend.get_texts()):
        label = legend_text.get_text()
        if label in lines_by_label:
            legend_line.set_picker(6)
            legend_line.set_alpha(1.0)
            legend_map[legend_line] = lines_by_label[label]
    return legend_map


def _connect_activity_legend_picker(fig: Any, legend_map: dict[Any, Any]) -> None:
    """Podłącz przełączanie widoczności linii przez kliknięcie wpisu legendy."""

    def on_pick(event: Any) -> None:
        legend_line = event.artist
        line = legend_map.get(legend_line)
        if line is None:
            return

        is_visible = not line.get_visible()
        line.set_visible(is_visible)
        legend_line.set_alpha(1.0 if is_visible else 0.25)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)


def _style_activity_axis(ax: Axes) -> None:
    """Ustaw wspólne etykiety i opis osi aktywacji modułów poznawczych."""
    ax.set_xlabel("Czas symulacji [s]")
    ax.set_ylabel("Aktywacja modułu [0-1]")
    ax.set_title("Mezoskopowa dynamika procesów poznawczych")
    _add_interpretation_box(
        ax.figure,
        "Co widzisz: każda linia to jeden moduł poznawczy, a skala 0-1 mówi, jak silnie "
        "jest aktywny w danej chwili. Dla osoby początkującej kluczowe są piki i momenty, "
        "w których kilka linii rośnie razem. Dla specjalisty ważna jest kolejność pobudzenia "
        "modułów, czas utrzymywania aktywacji i relacja z bodźcami scenariusza. Najpierw "
        "sprawdź, który moduł dominuje, kiedy się włącza i czy szybko wygasa.",
    )


def draw_activity(ax: Any, time: Any, activity: Any, names: Any, idx: Any) -> Any:
    """Opis funkcji draw_activity."""
    legend_map = _draw_activity_lines(ax, time, activity, idx)
    _style_activity_axis(ax)
    _connect_activity_legend_picker(ax.figure, legend_map)
    _style_lines(ax)
    return [ax]


def draw_activity_with_stimulus_channels(
    ax: Axes,
    time: Any,
    activity: Any,
    names: list[str],
    idx: dict[str, int],
    scenario: StimulusScenario,
) -> list[Axes]:
    """Narysuj aktywacje modułów wraz z kanałami bodźców scenariusza.

    Parameters
    ----------
    ax:
        Tymczasowa oś utworzona przez panel Qt; funkcja usuwa ją i zastępuje
        układem dwóch osi we wspólnej figurze.
    time:
        Sekwencja znaczników czasu symulacji w sekundach.
    activity:
        Macierz aktywacji modułów o kształcie ``(czas, moduł)``.
    names:
        Nazwy modułów modelu, zachowane dla zgodności z innymi funkcjami
        rysującymi.
    idx:
        Mapowanie nazwy modułu na indeks kolumny w macierzy aktywacji.
    scenario:
        Scenariusz bodźców używany do odtworzenia kanałów wejściowych.

    Returns
    -------
    list[Axes]
        Lista zawierająca górną oś aktywacji i dolną oś kanałów bodźców.
    """
    del names
    fig = ax.figure
    ax.remove()
    activity_ax, stimulus_ax = fig.subplots(
        2, 1, sharex=True, gridspec_kw={"height_ratios": [5, 1]}
    )

    legend_map = _draw_activity_lines(activity_ax, time, activity, idx)
    _style_activity_axis(activity_ax)
    _style_lines(activity_ax)
    _connect_activity_legend_picker(fig, legend_map)

    draw_scenario_channels(stimulus_ax, time, scenario)

    time_start = float(time[0])
    time_end = float(time[-1])

    def synchronize_stimulus_xlim(changed_ax: Axes) -> None:
        stimulus_ax.set_xlim(changed_ax.get_xlim())
        fig.canvas.draw_idle()

    def on_scroll(event: Any) -> None:
        if event.inaxes not in (
            activity_ax,
            activity_ax.xaxis,
            stimulus_ax,
            stimulus_ax.xaxis,
        ):
            return
        if event.xdata is None:
            return

        left, right = activity_ax.get_xlim()
        width = right - left
        if width <= 0:
            return

        event_step = getattr(event, "step", 0)
        scale_factor = 0.8 if event.button == "up" or event_step > 0 else 1.25
        new_width = min(time_end - time_start, max(width * scale_factor, 1e-9))
        cursor_ratio = (float(event.xdata) - left) / width
        new_left = float(event.xdata) - cursor_ratio * new_width
        new_right = new_left + new_width

        if new_left < time_start:
            new_left = time_start
            new_right = time_start + new_width
        if new_right > time_end:
            new_right = time_end
            new_left = time_end - new_width

        activity_ax.set_xlim(new_left, new_right)
        stimulus_ax.set_xlim(new_left, new_right)
        fig.canvas.draw_idle()

    activity_ax.callbacks.connect("xlim_changed", synchronize_stimulus_xlim)
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    return [activity_ax, stimulus_ax]


def draw_simulated_brain_activity(
    ax: Any, time: Any, activity: Any, names: Any, idx: Any
) -> Any:
    """Opis funkcji draw_simulated_brain_activity."""
    selected = [
        "VIS",
        "AUD",
        "INT",
        "SAL",
        "ATT",
        "PHON",
        "VSWM",
        "EXEC",
        "EPIS",
        "SEM",
        "HIP",
        "VAL",
        "MOT",
        "DMN",
        "GW",
    ]

    labels = [name for name in selected if name in idx]
    if not labels:
        ax.text(
            0.5,
            0.5,
            "Brak danych modułów do wizualizacji.",
            ha="center",
            va="center",
            transform=ax.transAxes,
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


def draw_brain_region_projections(
    ax: Any, time: Any, activity: Any, names: Any, idx: Any
) -> Any:
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
        scatter = _draw_brain_projection(
            sub_ax, time, activity, idx, svg, f"{label}: regiony SVG"
        )
        if scatter is not None:
            scatter_ref = scatter

    if scatter_ref is not None:
        cbar = fig.colorbar(
            scatter_ref, ax=axes.ravel().tolist(), fraction=0.02, pad=0.01
        )
        cbar.set_label("Aktywacja [0-1]")
    fig.suptitle("Aktywacja regionów mózgu na 4 rzutach (na bazie szkieletu SVG)")
    _add_interpretation_box(
        fig,
        "Rzuty SVG pokazują aktywację regionów. Co widzisz: każdy panel to inny "
        "rzut mózgu z podkładem anatomicznym zgodnym z kompaktowym viewerem SVG, "
        "a kolor punktu pokazuje aktywację regionu w ostatnim kroku symulacji. "
        "Dla osoby początkującej kluczowe jest, gdzie pojawiają się najjaśniejsze punkty. "
        "Dla specjalisty ważne jest, czy aktywacja tworzy lokalne ognisko, "
        "wzorzec boczny/lewy-prawy "
        "albo rozlane pobudzenie. Zakres osi pochodzi z rzeczywistych współrzędnych "
        "regionów i podkładów danego SVG.",
    )
    return list(axes.flatten())


def draw_region_activity_2d(
    ax: Any, time: Any, activity: Any, names: Any, idx: Any
) -> Any:
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
    """Narysuj diagnostykę modelu w dwóch panelach ze wspólną osią czasu.

    Parameters
    ----------
    ax:
        Tymczasowa oś utworzona przez panel Qt albo funkcję pomocniczą; zostaje
        usunięta, aby figura mogła zawierać dwa pionowe panele.
    time:
        Wektor czasu symulacji w sekundach.
    diagnostics:
        Słownik serii diagnostycznych modelu.

    Returns
    -------
    list[Any]
        Lista osi: panel zmiennych teoretycznych i panel neuromodulatorów.
    """
    fig = ax.figure
    ax.remove()
    axes = fig.subplots(2, 1, sharex=True)
    theoretical_ax, neuromodulator_ax = axes

    if diagnostics and "prediction_error" in diagnostics:
        theoretical_ax.plot(
            time, diagnostics["prediction_error"], label="błąd predykcji"
        )
    if diagnostics and "gw_ignition" in diagnostics:
        theoretical_ax.plot(
            time, diagnostics["gw_ignition"], label="zapłon global workspace"
        )
    if diagnostics and "dopamine_delta" in diagnostics:
        theoretical_ax.plot(
            time, diagnostics["dopamine_delta"], label="błąd predykcji nagrody"
        )

    if diagnostics and "noradrenaline" in diagnostics:
        neuromodulator_ax.plot(
            time, diagnostics["noradrenaline"], label="noradrenalina"
        )
    if diagnostics and "acetylcholine" in diagnostics:
        neuromodulator_ax.plot(
            time, diagnostics["acetylcholine"], label="acetylocholina"
        )
    if diagnostics and "serotonin" in diagnostics:
        neuromodulator_ax.plot(time, diagnostics["serotonin"], label="serotonina")
    if diagnostics and "gaba" in diagnostics:
        neuromodulator_ax.plot(time, diagnostics["gaba"], label="gaba")
    if diagnostics and "glutamate" in diagnostics:
        neuromodulator_ax.plot(time, diagnostics["glutamate"], label="glutaminian")
    if diagnostics and "endorphins" in diagnostics:
        neuromodulator_ax.plot(time, diagnostics["endorphins"], label="endorfiny")
    if diagnostics and "cortisol" in diagnostics:
        neuromodulator_ax.plot(time, diagnostics["cortisol"], label="kortyzol")

    theoretical_ax.set_ylabel("Wartość")
    theoretical_ax.set_title("Zmienne teoretyczne modelu")
    theoretical_ax.legend()
    neuromodulator_ax.set_xlabel("Czas symulacji [s]")
    neuromodulator_ax.set_ylabel("Wartość")
    neuromodulator_ax.set_title("Neuromodulatory mózgowe")
    neuromodulator_ax.legend()
    _add_interpretation_box(
        fig,
        "Co widzisz: diagnostyka jest rozdzielona na dwa pionowe panele ze wspólną osią czasu. "
        "Górny panel pokazuje wyłącznie zmienne teoretyczne modelu: błąd predykcji, zapłon "
        "global workspace i błąd predykcji nagrody. Dolny panel pokazuje wyłącznie "
        "neuromodulatory mózgowe. Dla osoby początkującej kluczowe jest porównanie momentów "
        "pików między panelami, bo pozwala odróżnić obliczeniowe zaskoczenie od reakcji "
        "neuromodulacyjnej. Dla specjalisty ważne są zależności czasowe: czy noradrenalina "
        "i kortyzol rosną po błędzie, a GABA/glutaminian stabilizują pobudzenie.",
    )
    for current_ax in axes:
        _style_lines(current_ax)
    return list(axes)


def draw_weight_trajectories(ax: Any, time: Any, diagnostics: Any) -> Any:
    """Opis funkcji draw_weight_trajectories."""
    history = diagnostics.get("weight_history", {})
    weights = history.get("weights", {})

    if not weights:
        ax.text(
            0.5,
            0.5,
            "Brak adaptacji wag lub brak wybranych par modułów.",
            ha="center",
            va="center",
            transform=ax.transAxes,
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
            0.5,
            0.5,
            "Brak zmian wag do wizualizacji.",
            ha="center",
            va="center",
            transform=ax.transAxes,
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


def draw_eeg_modules(
    ax: Any, time: Any, oscillations: Any, names: Any, idx: Any
) -> Any:
    """Opis funkcji draw_eeg_modules."""
    selected = ["HIP", "VSWM", "VIS", "AUD", "EXEC", "ATT", "SEM", "GW"]
    eeg = oscillations["eeg"]

    available = [name for name in selected if name in idx]
    if not available:
        ax.text(
            0.5,
            0.5,
            "Brak sygnałów EEG modułów.",
            ha="center",
            va="center",
            transform=ax.transAxes,
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
    series = {k: [] for k in CHANNELS}
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
        ax.axvspan(
            w["start"], w["end"], alpha=0.18 + 0.08 * (i % 2), label=phase["name"]
        )

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
    """Narysuj pełne i powiększone przebiegi decyzyjne modelu."""
    fig = ax.figure
    ax.remove()
    axes = fig.subplots(2, 1, sharex=False, gridspec_kw={"height_ratios": [3, 1]})
    full_ax, window_ax = axes

    full_ax.plot(
        time, behavior["decision_score"], label="decision score", color="#1f77b4"
    )
    full_ax.plot(
        time, behavior["confidence"], label="confidence", color="#2ca02c", alpha=0.9
    )
    full_ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)

    decision_mask = behavior["decision_event"]
    decision_times = time[decision_mask]
    decision_scores = behavior["decision_score"][decision_mask]
    if len(decision_times):
        full_ax.scatter(
            decision_times,
            decision_scores,
            marker="o",
            color="#d62728",
            label="decision event",
            zorder=3,
        )
        for decision_time, decision_score in zip(decision_times, decision_scores):
            full_ax.annotate(
                f"t={float(decision_time):.2f} s",
                xy=(decision_time, decision_score),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#7f1d1d",
            )

    time_window_mask = (time >= 0.0) & (time <= 1.0)
    window_ax.plot(
        time[time_window_mask],
        behavior["decision_score"][time_window_mask],
        label="decision score",
        color="#1f77b4",
    )
    window_ax.plot(
        time[time_window_mask],
        behavior["confidence"][time_window_mask],
        label="confidence",
        color="#2ca02c",
        alpha=0.9,
    )
    window_ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.5)

    window_decision_mask = decision_mask & time_window_mask
    window_decision_times = time[window_decision_mask]
    window_decision_scores = behavior["decision_score"][window_decision_mask]
    if len(window_decision_times):
        window_ax.scatter(
            window_decision_times,
            window_decision_scores,
            marker="o",
            color="#d62728",
            label="decision event",
            zorder=3,
        )
        for decision_time, decision_score in zip(
            window_decision_times, window_decision_scores
        ):
            window_ax.annotate(
                f"t={float(decision_time):.2f} s",
                xy=(decision_time, decision_score),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#7f1d1d",
            )

    full_ax.set_xlabel("Czas symulacji [s]")
    full_ax.set_ylabel("Skala decyzyjna")
    full_ax.set_title("Przebiegi decyzyjne i punkty decyzji")
    full_ax.legend()

    window_ax.set_xlabel("Czas symulacji [s]")
    window_ax.set_ylabel("Skala decyzyjna")
    window_ax.set_title("Wycinek decyzji 0–1 s")
    window_ax.set_xlim(0.0, 1.0)
    window_ax.legend()

    _add_interpretation_box(
        fig,
        "Co widzisz: wynik decyzji pokazuje kierunek i siłę preferowanej odpowiedzi, "
        "a pewność mówi, "
        "jak stabilna jest ta odpowiedź. Dla osoby początkującej najważniejsze są "
        "czerwone punkty decyzji "
        "i to, czy pojawiają się wtedy, gdy pewność jest wysoka. Dla specjalisty "
        "kluczowe są przekroczenia "
        "progu, oscylacje przed decyzją i zależność od bodźców lub faz scenariusza.",
    )
    _style_lines(full_ax)
    _style_lines(window_ax)
    return [full_ax, window_ax]


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


def _show_standalone(
    draw_func: Any, *args: Any, figsize: tuple[int, int] = (14, 6)
) -> None:
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
