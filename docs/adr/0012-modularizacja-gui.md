# ADR-0012: Modularizacja GUI modelu poznawczego

**Status:** proposed  
**Data:** 2026-05-28

### Kontekst

Moduł `brain_model/gui.py` skupiał w jednym pliku główne okno Tkinter, formularze parametrów, budowę układu, zapis i odczyt konfiguracji JSON oraz logikę uruchamiania symulacji. Utrudniało to bezpieczne rozwijanie GUI, ponieważ zmiany w układzie widoku mieszały się z konfiguracją i wykonywaniem eksperymentów.

Wymagane jest zachowanie kompatybilnego punktu wejścia `brain_model.gui:run_gui` oraz dotychczasowego formatu zapisu konfiguracji GUI.

### Decyzja

Dzielimy GUI na wyspecjalizowane moduły w pakiecie `brain_model`:

- `gui_app.py` zawiera główną klasę okna `BrainModelGUI` i funkcję `run_gui`,
- `gui_forms.py` zawiera `Tooltip`, `ParameterForm` oraz stałe opisujące pola formularzy,
- `gui_layout.py` zawiera budowę zakładek, sekcji widoku, menu i aktualizację panelu wykresów,
- `gui_config.py` zawiera zbieranie, stosowanie oraz zapis i odczyt konfiguracji JSON,
- `gui_runner.py` zawiera walidację parametrów skalarnych, uruchamianie symulacji i batchy oraz podsumowania metryk,
- `gui.py` pozostaje cienką warstwą kompatybilności importującą `BrainModelGUI` i `run_gui` z `gui_app.py`.

Format JSON pozostaje `brain-model-gui-config-v1`; nie wprowadzamy migracji, ponieważ klucze i semantyka konfiguracji nie zostały zmienione.

### Konsekwencje

**Pozytywne:**

- łatwiejsza nawigacja po kodzie GUI według odpowiedzialności,
- mniejsze ryzyko regresji przy zmianach formularzy, układu albo mechaniki uruchamiania,
- zachowana kompatybilność importów dla istniejących skryptów i użytkowników.

**Negatywne / koszty:**

- więcej plików modułów do utrzymania,
- metody głównego okna są rozdzielone między mixiny, więc przy zmianach należy pilnować zależności atrybutów inicjalizowanych w `BrainModelGUI`.

### Alternatywy rozważane

- Pozostawienie monolitycznego `gui.py`: najmniejszy diff, ale nie rozwiązuje problemu rosnącego pliku i mieszania odpowiedzialności.
- Wydzielenie samych formularzy: prostsze, lecz nadal pozostawia konfigurację i runner w module widoku.
- Pełna przebudowa na klasy usługowe bez mixinów: czytelniejsza granica zależności, ale zbyt duży refaktor względem wymaganego minimalnego zakresu zmian.

### Powiązane

- `brain_model/gui.py`
- `brain_model/gui_app.py`
- `brain_model/gui_forms.py`
- `brain_model/gui_layout.py`
- `brain_model/gui_config.py`
- `brain_model/gui_runner.py`
