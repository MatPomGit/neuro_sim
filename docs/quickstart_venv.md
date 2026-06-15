# Quickstart venv

## Cel przewodnika

Ten przewodnik pokazuje, jak uruchomić aplikację lokalnie w środowisku
wirtualnym `venv` bez modyfikacji kodu źródłowego. Kroki obejmują utworzenie
środowiska, instalację pakietu, uruchomienie symulacji CLI oraz start
aplikacji desktopowej GUI.

## Wymagania

Projekt wymaga wersji Pythona zgodnej z deklaracją w `pyproject.toml`:
`>=3.10,<3.13`. Przed rozpoczęciem sprawdź wersję interpretera:

```bash
python --version
```

Jeżeli systemowe polecenie `python` wskazuje nieobsługiwaną wersję, użyj
odpowiedniego interpretera, np. `python3.10`, `python3.11` albo `python3.12`.

## Utworzenie venv

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Po aktywacji środowiska polecenia `python` i `pip` powinny wskazywać pliki z
katalogu `.venv`.

## Instalacja aplikacji

Z aktywnym środowiskiem `venv` zainstaluj aplikację i zależności runtime z
`pyproject.toml`:

```bash
python -m pip install .
```

Ta instalacja udostępnia między innymi komendy `neuro-sim-run` i
`neuro-sim-gui`.

## Uruchomienie symulacji CLI

Przykład uruchomienia domyślnej konfiguracji:

```bash
python -m brain_core.simulation.run --config configs/default.yaml
```

Przykład uruchomienia konfiguracji demonstracyjnej poznawczej:

```bash
python -m brain_core.simulation.run --config configs/cognitive_demo.yaml
```

Po instalacji pakietu można użyć także skryptu konsolowego:

```bash
neuro-sim-run --config configs/cognitive_demo.yaml
```

## Uruchomienie GUI

Desktopowe GUI można uruchomić bezpośrednio z pliku wejściowego:

```bash
python main_gui.py
```

Po instalacji pakietu dostępny jest również skrypt konsolowy:

```bash
neuro-sim-gui
```

## Scenariusze dydaktyczne

Do demonstracji efektów w protokole roving oddball służą przykładowe pliki
konfiguracyjne:

- `configs/roving_oddball_healthy.yaml` — scenariusz referencyjny,
- `configs/roving_oddball_disorder_gaba.yaml` — scenariusz z zaburzeniem
  hamowania GABA,
- `configs/roving_oddball_lesion_hippocampus.yaml` — scenariusz z lezją
  hipokampa.

Przykład uruchomienia jednego ze scenariuszy:

```bash
python -m brain_core.simulation.run --config configs/roving_oddball_healthy.yaml
```

## Ograniczenia interpretacyjne

Wyniki generowane przez projekt mają charakter dydaktyczny i symulacyjny. Nie
stanowią diagnozy klinicznej, rekomendacji terapeutycznej ani narzędzia do
oceny stanu zdrowia konkretnej osoby. Interpretuj je wyłącznie jako ilustrację
zależności modelowych i założeń eksperymentalnych opisanych w konfiguracji.

## Rozwiązywanie problemów

### Brak PySide6

Jeżeli GUI zgłasza brak modułu `PySide6`, upewnij się, że aplikacja została
zainstalowana w aktywnym środowisku:

```bash
python -m pip install .
```

Możesz też sprawdzić, czy pakiet jest widoczny dla bieżącego interpretera:

```bash
python -m pip show PySide6
```

### Nieaktywne venv

Jeżeli polecenia konsolowe nie są dostępne albo zależności nie są znajdowane,
sprawdź aktywację środowiska:

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Po aktywacji ponownie uruchom `python -m pip install .`.

### Niezgodna wersja Pythona

Jeżeli instalacja kończy się błędem dotyczącym wersji Pythona, sprawdź:

```bash
python --version
```

Wymagana jest wersja `>=3.10,<3.13`. Utwórz środowisko `venv` przy użyciu
obsługiwanego interpretera, na przykład:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```
