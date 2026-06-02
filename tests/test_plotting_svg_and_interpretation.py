"""Testy odporności parsowania SVG i pola interpretacji wykresów."""

from __future__ import annotations

import matplotlib.pyplot as plt

from brain_model.plotting import (
    INTERPRETATION_WRAP_WIDTH,
    _add_interpretation_box,
    _load_svg_region_centroids,
    _load_svg_region_shapes,
    _plot_svg_region_background,
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
        '<path data-region="VIS" d="M 1 2 L 3 4 H 5" />'
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
