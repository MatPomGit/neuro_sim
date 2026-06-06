"""Testy odporności parsowania SVG i pola interpretacji wykresów."""

from __future__ import annotations

import matplotlib.pyplot as plt

from brain_model.model import CognitiveBrainModel
from brain_model.plotting import (
    INTERPRETATION_WRAP_WIDTH,
    _add_interpretation_box,
    _calculate_scroll_zoom_limits,
    _load_svg_region_centroids,
    _load_svg_region_labels,
    _load_svg_region_shapes,
    _load_svg_underlay_shapes,
    _parse_svg_translate,
    _plot_svg_region_background,
    _plot_svg_underlay_background,
    draw_weight_deltas,
    draw_weight_trajectories,
)


def test_svg_region_loading_accepts_d_before_data_region(tmp_path) -> None:
    """Regiony SVG powinny ładować się niezależnie od kolejności atrybutów."""
    svg_path = tmp_path / "regions.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path d="M 1 2 L 3 4 Z" data-region="VIS" />'
        '<path data-region="AUD" d="M 10 20 L 30 40 Z" />'
        "</svg>",
        encoding="utf-8",
    )

    _load_svg_region_shapes.cache_clear()
    _load_svg_region_centroids.cache_clear()

    shapes = _load_svg_region_shapes(str(svg_path))
    centroids = _load_svg_region_centroids(str(svg_path))

    assert shapes["VIS"] == ([1.0, 3.0], [2.0, 4.0])
    assert shapes["AUD"] == ([10.0, 30.0], [20.0, 40.0])
    assert centroids["VIS"] == (2.0, 3.0)


def test_svg_region_background_ignores_unpaired_coordinate(tmp_path) -> None:
    """Nieparzysta liczba wartości w ścieżce SVG nie może psuć rysowania konturu."""
    svg_path = tmp_path / "regions.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path data-region="VIS" d="M 1 2 L 3 4 L 5" />'
        "</svg>",
        encoding="utf-8",
    )

    _load_svg_region_shapes.cache_clear()
    shapes = _load_svg_region_shapes(str(svg_path))
    fig, ax = plt.subplots()

    try:
        _plot_svg_region_background(ax, shapes)
    finally:
        plt.close(fig)

    assert shapes["VIS"] == ([1.0, 3.0], [2.0, 4.0])


def test_svg_region_loading_respects_relative_lateral_commands(tmp_path) -> None:
    """Względne komendy SVG powinny ustawiać punkty na rzucie lateral bez przesunięcia."""
    svg_path = tmp_path / "relative_regions.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path data-region="OFC_L" data-label="Orbitofrontal cortex left" '
        'd="m 360,1090 c 95,-72 205,-100 345,-90 '
        '90,6 145,38 173,95 z" />'
        "</svg>",
        encoding="utf-8",
    )

    _load_svg_region_shapes.cache_clear()
    _load_svg_region_centroids.cache_clear()
    _load_svg_region_labels.cache_clear()

    shapes = _load_svg_region_shapes(str(svg_path))
    centroids = _load_svg_region_centroids(str(svg_path))
    labels = _load_svg_region_labels(str(svg_path))

    xs, ys = shapes["OFC_L"]
    assert min(xs) >= 360.0
    assert max(xs) == 878.0
    assert min(ys) >= 1000.0
    assert centroids["OFC_L"][0] > 500.0
    assert labels["OFC_L"] == "lewa kora oczodołowo-czołowa"


def test_scroll_zoom_limits_zoom_around_cursor_and_keep_home_bounds() -> None:
    """Zoom kółkiem powinien przybliżać wokół kursora i nie oddalać poza widok bazowy."""
    zoomed_limits = _calculate_scroll_zoom_limits(
        current_limits=(0.0, 100.0),
        home_limits=(0.0, 100.0),
        cursor_value=25.0,
        scale_factor=0.8,
    )
    capped_limits = _calculate_scroll_zoom_limits(
        current_limits=zoomed_limits,
        home_limits=(0.0, 100.0),
        cursor_value=25.0,
        scale_factor=2.0,
    )
    inverted_limits = _calculate_scroll_zoom_limits(
        current_limits=(100.0, 0.0),
        home_limits=(100.0, 0.0),
        cursor_value=75.0,
        scale_factor=0.8,
    )

    assert zoomed_limits == (5.0, 85.0)
    assert capped_limits == (0.0, 100.0)
    assert inverted_limits == (95.0, 15.0)


def test_interpretation_box_replaces_previous_artist() -> None:
    """Ponowne rysowanie figury powinno zostawiać jedno pole interpretacji."""
    fig = plt.figure()

    try:
        _add_interpretation_box(fig, "Pierwszy opis interpretacyjny.")
        first_artist = fig._neuro_sim_interpretation_artist
        _add_interpretation_box(fig, "Drugi opis interpretacyjny po odświeżeniu.")

        interpretation_artists = [
            artist
            for artist in fig.texts
            if artist.get_bbox_patch() is not None
            and artist.get_position() == (0.01, 0.01)
        ]
        assert len(interpretation_artists) == 1
        assert first_artist not in fig.texts
        assert fig._neuro_sim_interpretation_artist is interpretation_artists[0]
    finally:
        plt.close(fig)


def test_interpretation_wrap_width_fits_default_qt_panel() -> None:
    """Szerokość łamania opisu powinna być czytelna dla domyślnego panelu Qt."""
    assert INTERPRETATION_WRAP_WIDTH <= 100


def test_svg_underlay_uses_non_region_paths_and_translate(tmp_path) -> None:
    """Podkład SVG ma brać bazowe ścieżki z przesunięciem jak viewer kompaktowy."""
    svg_path = tmp_path / "regions.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<path fill="#2E2E2E" transform="translate(10,20)" '
        'd="M 0 0 L 4 0 L 4 4 Z" />'
        '<path data-region="VIS" d="M 100 100 L 120 100 L 120 120 Z" />'
        "</svg>",
        encoding="utf-8",
    )
    _load_svg_underlay_shapes.cache_clear()

    underlay_shapes = _load_svg_underlay_shapes(str(svg_path))

    assert len(underlay_shapes) == 1
    xs, ys, fill_color = underlay_shapes[0]
    assert fill_color == "#2E2E2E"
    assert xs[0] == 10.0
    assert ys[0] == 20.0


def test_svg_underlay_background_adds_polycollection() -> None:
    """Podkład anatomiczny powinien trafiać do osi jako warstwa pod regionami."""
    fig, ax = plt.subplots()

    try:
        _plot_svg_underlay_background(
            ax, (((0.0, 1.0, 1.0), (0.0, 0.0, 1.0), "#333333"),)
        )
        assert len(ax.collections) == 1
    finally:
        plt.close(fig)


def test_svg_translate_parser_accepts_single_and_pair_values() -> None:
    """Parser transformacji SVG powinien obsłużyć wariant jedno- i dwuargumentowy."""
    assert _parse_svg_translate("translate(10)") == (10.0, 0.0)
    assert _parse_svg_translate("translate(10, 20)") == (10.0, 20.0)


def test_default_simulation_produces_weight_plots() -> None:
    """Domyślna symulacja powinna dawać niepuste trajektorie i przyrosty wag."""
    model = CognitiveBrainModel(seed=7, stimulus="baseline")
    time, _activity, diagnostics, _oscillations, _behavior = model.simulate(T=0.1)
    fig, (trajectory_ax, delta_ax) = plt.subplots(2, 1)

    try:
        draw_weight_trajectories(trajectory_ax, time, diagnostics)
        draw_weight_deltas(delta_ax, time, diagnostics)

        assert trajectory_ax.lines
        assert len(delta_ax.lines) > 1
    finally:
        plt.close(fig)


def test_report_metric_bars_are_presentation_only_with_polish_text() -> None:
    """Wykres raportowy Qt jest statycznie opisany jako prezentacja gotowych metryk."""
    from pathlib import Path

    source = Path("brain_model/qt_plotting.py").read_text(encoding="utf-8")

    assert "def draw_report_metric_bars" in source
    assert "eeg_bold_sections" in source
    assert "nie liczy metryk analitycznych" in source
    assert "warstwą prezentacji" in source
    assert "Gotowe metryki EEG/BOLD" in source
    assert "brain_core" not in source.split("def draw_report_metric_bars", 1)[0]
