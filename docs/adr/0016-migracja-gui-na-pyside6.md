# ADR-0016: Migracja GUI z `tkinter` na PySide6

**Status:** proposed  
**Data:** 2026-05-29

### Kontekst

Dotychczasowe GUI modelu poznawczego było oparte o `tkinter` oraz `ttk`. Interfejs zawierał sekcje szybkiego startu, opcji zaawansowanych, wyboru wykresów, zapis/odczyt konfiguracji JSON oraz uruchamianie symulacji w tle. Dalszy rozwój wymaga docelowych modułów Qt, aby łatwiej osadzać wykresy Matplotlib, rozdzielić wątek obliczeń od wątku interfejsu i przygotować bazę pod bogatsze widoki.

### Decyzja

Wprowadzamy docelową implementację GUI w PySide6 w modułach `brain_model/qt_*.py`:

- `qt_app.py` utrzymuje `QApplication`, `QMainWindow`, menu, zakładki i kompatybilne `run_gui`,
- `qt_state.py` przechowuje stan formularza niezależny od widżetów,
- `qt_sections.py` buduje sekcje „Szybki start”, „Opcje zaawansowane” oraz „Wyniki i wykresy”,
- `qt_config.py` zachowuje kompatybilny zapis i odczyt konfiguracji JSON,
- `qt_runner.py` uruchamia symulację przez `QThread`,
- `qt_results.py` osadza figury Matplotlib w widżetach Qt,
- `qt_styles.py` centralizuje style QSS.

Kompatybilny punkt wejścia `brain_model.gui:run_gui` pozostaje bez zmian dla użytkowników i deleguje do implementacji PySide6. Zależność `PySide6` dodajemy do `pyproject.toml`, `requirements.txt` oraz `environment.yml` obok `numpy`, `matplotlib` i `PyYAML`.

### Konsekwencje

**Pozytywne:**

- zachowany jest publiczny punkt wejścia `neuro-sim-gui`,
- GUI korzysta z natywnych odpowiedników Qt (`QMainWindow`, `QWidget`, `QTabWidget`, `QGroupBox`, `QPushButton`, `QCheckBox`, `QComboBox`, `QLineEdit`, `QLabel`),
- symulacja działa przez `QThread`, więc główna pętla interfejsu pozostaje responsywna,
- wykresy Matplotlib są osadzane przez backend Qt zamiast backendu Tk.

**Negatywne / koszty:**

- środowisko uruchomieniowe musi instalować większą zależność `PySide6`,
- przez okres przejściowy stare moduły `gui_*` pozostają w repozytorium jako kod historyczny i testowany statycznie,
- przyszłe rozszerzenia GUI powinny trafiać do modułów `qt_*`, aby nie dublować rozwoju dwóch toolkitów.

### Alternatywy rozważane

- Dalszy rozwój `tkinter`: najniższy koszt krótkoterminowy, ale słabsze wsparcie dla bogatszych widoków i osadzania nowoczesnych komponentów.
- Web GUI: dobre dla dystrybucji przez przeglądarkę, ale większy zakres zmian i inny model uruchamiania niż lokalna aplikacja desktopowa.
- Natychmiastowe usunięcie modułów `gui_*`: mniejszy dług techniczny, ale większe ryzyko regresji testów statycznych i trudniejszy review migracji.

### Powiązane

- `brain_model/gui.py`
- `brain_model/qt_app.py`
- `brain_model/qt_state.py`
- `brain_model/qt_sections.py`
- `brain_model/qt_config.py`
- `brain_model/qt_runner.py`
- `brain_model/qt_results.py`
- `brain_model/qt_styles.py`
- `pyproject.toml`
- `requirements.txt`
- `environment.yml`
