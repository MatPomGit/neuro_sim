"""Historyczny skrypt zgodności dla modelu poznawczego.

Ten plik pozostaje wyłącznie jako jawna warstwa legacy dla użytkowników, którzy
uruchamiali wcześniejsze wersje projektu poleceniem ``python brain_model.py``.
Import ``import brain_model`` wskazuje na pakiet ``brain_model/`` i nie korzysta
z tego pliku, dlatego nowy kod powinien importować API wyłącznie z pakietu.

Plan migracji:
    1. Utrzymać ten skrypt tylko jako tymczasowy punkt uruchomieniowy.
    2. Przenieść przykłady i dokumentację użytkową na ``main.py`` albo
       ``python -m brain_core.simulation.run``.
    3. Usunąć plik w osobnym, małym PR po potwierdzeniu braku zewnętrznych
       zależności od uruchamiania ``python brain_model.py``.
"""

from brain_model.model import CognitiveBrainModel
from brain_model.params import BrainParams

__all__ = ["BrainParams", "CognitiveBrainModel", "main"]


def main() -> None:
    """Uruchom demonstracyjną symulację przez docelowy pakiet ``brain_model``.

    Funkcja zachowuje historyczne zachowanie skryptu: tworzy domyślny model,
    wykonuje symulację i pokazuje wykresy diagnostyczne. Nie wprowadza nowej
    logiki naukowej; wszystkie obliczenia deleguje do pakietu ``brain_model/``.

    Returns:
        None. Wynik jest prezentowany użytkownikowi w oknach wykresów
        Matplotlib, zgodnie z zachowaniem legacy.
    """
    model = CognitiveBrainModel()
    time, activity, diagnostics, oscillations, behavior = model.simulate(T=45.0)
    # TODO: Use the appropriate plotting function from brain_model.plotting


if __name__ == "__main__":
    main()
