"""
Moduł eksportu raportów badawczych do PDF z wykresami i opisami.
"""

from typing import Any, Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import datetime


def export_report(
    filename: str,
    simulation_params: Dict[str, Any],
    results: List[Dict[str, Any]],
    plots: List[Dict[str, Any]],
    title: str = "Raport badawczy symulacji poznawczej",
    author: str = "neuro_sim",
    description: str = "Automatycznie wygenerowany raport z symulacji."
) -> None:
    """
    Eksportuje raport badawczy do pliku PDF.

    :param filename: Ścieżka do pliku PDF.
    :param simulation_params: Słownik parametrów symulacji.
    :param results: Lista słowników z wynikami (np. statystyki, metryki).
    :param plots: Lista słowników: {'figure': plt.Figure, 'caption': str, 'how_to_read': str}
    :param title: Tytuł raportu.
    :param author: Autor raportu.
    :param description: Opis raportu.
    """
    with PdfPages(filename) as pdf:
        # Strona tytułowa
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4
        ax.axis('off')
        ax.text(0.5, 0.85, title, ha='center', va='center', fontsize=20, weight='bold')
        ax.text(0.5, 0.78, f"Autor: {author}", ha='center', va='center', fontsize=12)
        ax.text(0.5, 0.75, f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ha='center', va='center', fontsize=12)
        ax.text(0.5, 0.70, description, ha='center', va='center', fontsize=12)
        pdf.savefig(fig)
        plt.close(fig)

        # Parametry symulacji
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        y = 0.95
        ax.text(0.05, y, "Parametry symulacji:", fontsize=14, weight='bold', va='top')
        y -= 0.05
        for k, v in simulation_params.items():
            ax.text(0.07, y, f"{k}: {v}", fontsize=12, va='top')
            y -= 0.03
        pdf.savefig(fig)
        plt.close(fig)

        # Wyniki symulacji
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        y = 0.95
        ax.text(0.05, y, "Wyniki symulacji:", fontsize=14, weight='bold', va='top')
        y -= 0.05
        for result in results:
            for k, v in result.items():
                ax.text(0.07, y, f"{k}: {v}", fontsize=12, va='top')
                y -= 0.03
        pdf.savefig(fig)
        plt.close(fig)

        # Wykresy z opisami
        for plot in plots:
            fig = plot['figure']
            caption = plot.get('caption', "")
            how_to_read = plot.get('how_to_read', "")
            fig.suptitle(caption, fontsize=14)
            pdf.savefig(fig)
            plt.close(fig)
            # Strona z opisem wykresu
            fig_desc, ax_desc = plt.subplots(figsize=(8.27, 11.69))
            ax_desc.axis('off')
            ax_desc.text(0.05, 0.95, f"Opis wykresu:", fontsize=13, weight='bold', va='top')
            ax_desc.text(0.07, 0.90, how_to_read, fontsize=12, va='top', wrap=True)
            pdf.savefig(fig_desc)
            plt.close(fig_desc)
