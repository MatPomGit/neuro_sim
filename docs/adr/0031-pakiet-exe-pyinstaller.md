# ADR-0031: Pakiet wykonywalny EXE budowany przez PyInstaller

**Status:** proposed  
**Data:** 2026-06-10

## Kontekst

Użytkownicy niebędący programistami nie mają zainstalowanego Pythona
ani wymaganych bibliotek. Aby umożliwić uruchamianie aplikacji bez
znajomości środowiska programistycznego, projekt potrzebuje samodzielnego
pliku wykonywalnego, który można uruchomić bez wcześniejszej instalacji.

Aplikacja NeuroSim GUI:

- korzysta z `PySide6` i backendu Matplotlib `QtAgg`;
- wczytuje dane konfiguracyjne z katalogów `configs/` i `assets/svg/`
  za pomocą ścieżek względem lokalizacji pakietu Pythona;
- punkt wejścia to `main_gui.py` → `brain_model.gui.run_gui`.

## Decyzja

Do budowania samodzielnego pliku wykonywalnego stosujemy **PyInstaller**
w trybie katalogu (`--onedir`). Specyfikacja budowania przechowywana jest
w pliku `neuro_sim_gui.spec` w katalogu głównym repozytorium. Skrypt
pomocniczy `scripts/build_exe.py` automatyzuje wywołanie PyInstaller.

Wybór trybu `--onedir` zamiast `--onefile`:

- PySide6 zawiera dziesiątki bibliotek Qt; w trybie `--onefile` każde
  uruchomienie aplikacji wypakowuje je do katalogu tymczasowego, co
  znacząco wydłuża czas startu;
- tryb `--onedir` pozwala na jednorazowe zbudowanie katalogu `dist/NeuroSim/`
  i uruchamianie aplikacji wielokrotnie bez narzutu dekompresji;
- debugowanie i weryfikacja zawartości paczki jest łatwiejsza.

Pliki danych dołączone do paczki:

| Katalog źródłowy | Docelowy w paczce | Cel                              |
|------------------|-------------------|----------------------------------|
| `configs/`       | `configs/`        | Presety YAML scenariuszy         |
| `assets/svg/`    | `assets/svg/`     | Pliki SVG widoków mózgu          |

Rozdzielczość ścieżek w kodzie (np.
`Path(__file__).resolve().parents[1]` w `brain_model/qt_config.py`)
jest spójna z lokalizacją `sys._MEIPASS` w środowisku PyInstaller, więc
nie wymaga zmian w kodzie źródłowym.

## Konsekwencje

Pozytywne:

- użytkownicy bez Pythona mogą uruchamiać aplikację na Windows, macOS
  i Linux;
- istniejący kod nie wymaga modyfikacji;
- budowanie jest powtarzalne i zautomatyzowane jednym poleceniem;
- `dist/` i artefakty budowania są wykluczone z repozytorium przez
  `.gitignore`.

Negatywne / koszty:

- `pyinstaller` i `pyinstaller-hooks-contrib` muszą być zainstalowane
  w środowisku deweloperskim przed wywołaniem skryptu budującego;
- paczka z PySide6 zajmuje zwykle 150–400 MB;
- budowanie należy powtarzać po każdej aktualizacji zależności lub
  zmianie kodu;
- `neuro_sim_gui.spec` musi być utrzymywany wraz z ewentualnymi zmianami
  struktury projektu (nowe moduły, nowe pliki danych).

## Alternatywy rozważane

- **cx_Freeze**: analogiczne możliwości, ale słabsza obsługa haków PySide6
  i mniejsza społeczność;
- **Nuitka**: kompiluje Python do C, daje mniejszy rozmiar i szybszy
  start, ale wymaga dłuższego czasu budowania i bardziej złożonej
  konfiguracji;
- **Briefcase (BeeWare)**: ukierunkowane na aplikacje mobilne i macOS;
  wymagałoby reorganizacji struktury projektu;
- **Plik .whl + installer**: wymaga od użytkownika zainstalowanego Pythona
  — nie spełnia wymagania „uruchamialne bez Pythona".

## Powiązane dokumenty / issue / PR

- `neuro_sim_gui.spec` — plik specyfikacji PyInstaller
- `scripts/build_exe.py` — skrypt budujący EXE
- `docs/architecture_decision_records.md`
- `docs/adr/0016-migracja-desktop-gui-na-pyside6.md`
- `main_gui.py` — punkt wejścia GUI
- `brain_model/qt_config.py` — rozdzielczość ścieżek konfiguracji
- `brain_model/plotting.py` — rozdzielczość ścieżek SVG
