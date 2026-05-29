# AGENTS.md — wytyczne dla agentów AI w projekcie `neuro_sim`

Ten dokument definiuje obowiązkowe zasady dla agentów AI oraz ludzi wykonujących zmiany w repozytorium. Łączy reguły pracy nad projektem `neuro_sim` z zasadami pisania replikowalnego, wydajnego i czytelnego kodu naukowego w Pythonie.

Kod w tym repozytorium należy traktować jako element metody badawczej. Oznacza to, że wynik eksperymentu powinien dać się powiązać z kodem, konfiguracją, danymi, środowiskiem uruchomieniowym, logami, metrykami oraz ziarnem losowości.

---

## 1) Zasady nadrzędne

1. **KISS (Keep It Simple, Stupid)**
   - Preferuj najprostsze rozwiązanie, które spełnia wymagania.
   - Nie dodawaj nowych warstw abstrakcji bez realnej potrzeby biznesowej, badawczej lub technicznej.
   - Kod naukowy powinien być najpierw poprawny, jawny i replikowalny, a dopiero potem maksymalnie ogólny.

2. **Minimalny zakres zmian**
   - Modyfikuj wyłącznie pliki i obszary niezbędne do realizacji zadania.
   - Unikaj refaktorów „przy okazji”, jeśli nie są częścią zlecenia.
   - Nie przebudowuj całych modułów tylko po to, aby dodać lokalną funkcjonalność.

3. **Spójność z istniejącą architekturą**
   - Szanuj podział odpowiedzialności (`brain_core` vs `brain_model`, konfiguracja, I/O).
   - Nie wprowadzaj zależności cyklicznych.
   - Nie mieszaj warstw domenowych, eksperymentalnych, infrastrukturalnych i prezentacyjnych.
   - Logika eksperymentu powinna być oddzielona od GUI, wizualizacji i kodu wejścia/wyjścia.

4. **Bezpieczeństwo i przewidywalność**
   - Nie dodawaj ukrytych efektów ubocznych.
   - Nie osłabiaj walidacji wejścia i mechanizmów deterministyczności.
   - Każda losowość musi być jawna, kontrolowana i zapisana w konfiguracji eksperymentu.

5. **Replikowalność jako wymóg metodologiczny**
   - Każdy eksperyment powinien dać się odtworzyć na podstawie zapisanych artefaktów.
   - Wynik badawczy bez konfiguracji, wersji kodu, wersji danych i informacji o środowisku jest niepełny.
   - Dane surowe nie powinny być modyfikowane przez kod eksperymentalny.

---

## 2) Nakazy (MUST)

1. **Dokumentuj decyzje architektoniczne**
   - Każda zmiana strukturalna, np. nowy moduł, istotna zmiana granic odpowiedzialności, zmiana strategii konfiguracji, I/O, losowości lub integracji, **musi** zostać opisana w ADR.
   - ADR dodawaj zgodnie z zasadami w `docs/architecture_decision_records.md`: status, kontekst, decyzja, konsekwencje, alternatywy.

2. **Uzasadniaj kompromisy**
   - Jeśli wybierasz rozwiązanie mniej oczywiste, opisz dlaczego, jakie są koszty i jakie alternatywy odrzucono.
   - W kodzie naukowym szczególnie uzasadniaj kompromisy między wydajnością, deterministycznością i dokładnością obliczeń.

3. **Dbaj o testowalność**
   - Kod musi być możliwy do zweryfikowania przez testy, walidację i reprodukcję uruchomienia.
   - Przy zmianach logiki dodaj lub zaktualizuj odpowiednie testy albo artefakty weryfikacji.
   - Testuj szczególnie kształty tablic, zakresy wartości, deterministyczność wyników i brak przecieku danych.

4. **Zachowuj kompatybilność konfiguracji**
   - Przy zmianie konfiguracji lub schematu zapewnij ścieżkę migracji albo czytelny błąd walidacji.
   - Parametry eksperymentu nie mogą być zaszyte wyłącznie w kodzie.
   - Każde uruchomienie eksperymentu musi zapisać kopię użytej konfiguracji.

5. **Czytelność ponad „spryt”**
   - Nazwy mają być jednoznaczne, domenowe i konsekwentne.
   - Funkcje powinny być krótkie i mieć pojedynczą odpowiedzialność.
   - Unikaj skrótów zrozumiałych wyłącznie dla autora.

6. **Jawność zmian**
   - Opisuj w PR, co zmieniono, dlaczego oraz jak zweryfikowano zmianę.
   - Nie ukrywaj istotnych zmian pod dużym, niepowiązanym diffem.
   - Jeżeli nie można uruchomić testów, opisz przyczynę.

7. **Rejestruj przebieg eksperymentów**
   - Każdy eksperyment powinien zapisywać logi, metryki, konfigurację, informacje o środowisku i identyfikator commita Git.
   - Wyniki zapisuj do jednoznacznego katalogu eksperymentu.
   - Nie używaj `print()` jako głównego mechanizmu raportowania przebiegu programu.

---

## 3) Zakazy (MUST NOT)

1. **Zakaz over-engineeringu**
   - Nie wprowadzaj wzorców, protokołów ani frameworków „na przyszłość”, jeśli nie są teraz potrzebne.

2. **Zakaz „silent breaking changes”**
   - Nie zmieniaj zachowania API, formatów danych, konfiguracji lub semantyki bez jawnej dokumentacji i migracji.

3. **Zakaz mieszania odpowiedzialności**
   - Nie przenoś logiki domenowej do warstwy technicznej i odwrotnie.
   - Nie łącz logiki eksperymentalnej, GUI, wizualizacji i zapisu artefaktów w jednej dużej funkcji.

4. **Zakaz martwego kodu**
   - Nie dodawaj nieużywanych klas, funkcji, flag, parametrów i komentarzy TODO bez właściciela lub uzasadnienia.

5. **Zakaz pseudonapraw**
   - Nie „naprawiaj” problemu przez wyciszanie wyjątków, usuwanie walidacji, ignorowanie błędów lub omijanie testów.

6. **Zakaz losowej niedeterministyczności**
   - Nie używaj niekontrolowanych źródeł losowości poza uzgodnionym mechanizmem RNG.
   - Nie twórz wyników badawczych zależnych od domyślnego, nieustalonego stanu generatora losowego.

7. **Zakaz masowych zmian formatowania bez powodu**
   - Nie przebudowuj całych plików tylko po to, by zmienić styl lub układ, jeśli zadanie tego nie wymaga.

8. **Zakaz przecieku danych**
   - Nie dopasowuj transformacji, skalowania, imputacji ani selekcji cech na całym zbiorze przed podziałem na zbiory treningowe, walidacyjne i testowe.
   - Nie wykorzystuj informacji ze zbioru testowego do doboru parametrów, preprocessingu ani selekcji modeli.

9. **Zakaz ukrytych zależności lokalnych**
   - Nie używaj bezpośrednio lokalnych ścieżek użytkownika.
   - Nie zakładaj istnienia plików poza repozytorium lub jawnie skonfigurowanym katalogiem danych.

10. **Zakaz commitowania danych wrażliwych i dużych artefaktów**
   - Nie commituj sekretów, tokenów API, danych osobowych, dużych modeli ani masywnych plików wynikowych.
   - Do dużych danych i artefaktów stosuj DVC, Git LFS albo zewnętrzne repozytorium danych.

---

## 4) Styl kodu i formatowanie

Kod powinien być zgodny z PEP 8 oraz formatowany automatycznie. Zalecane narzędzia:

- `ruff` do lintingu i częściowego formatowania;
- `black` do formatowania kodu;
- `mypy` lub `pyright` do statycznej kontroli typów;
- `pytest` do testów;
- `pre-commit` do automatycznej kontroli jakości przed commitem.

Zalecane polecenia kontrolne:

```bash
ruff check .
black .
pytest
```

Importy porządkuj w kolejności:

1. biblioteki standardowe,
2. biblioteki zewnętrzne,
3. moduły lokalne.

Przykład:

```python
from pathlib import Path

import numpy as np
import pandas as pd

from brain_core.config import ExperimentConfig
from brain_core.preprocessing import normalize_signal
```

Linie kodu powinny mieć maksymalnie 88–100 znaków, chyba że czytelność wymaga inaczej.

---

## 5) Nazewnictwo zmiennych, funkcji i klas

1. **Zmienne**
   - Stosuj `snake_case`.
   - Nazwy mają być opisowe, domenowe i jednoznaczne.
   - Jeśli jednostka ma znaczenie, umieść ją w nazwie.

Przykład:

```python
sampling_rate_hz = 250
participant_id = "sub-001"
reaction_times_ms = np.array([412, 389, 455])
simulation_duration_s = 20.0
```

Unikaj nazw ogólnych:

```python
# Źle
x = load_data()
data2 = process(x)
res = model(data2)

# Dobrze
raw_eeg_signal = load_eeg_signal(file_path)
filtered_eeg_signal = bandpass_filter(
    raw_eeg_signal,
    low_hz=1.0,
    high_hz=40.0,
)
classification_results = model.predict(filtered_eeg_signal)
```

2. **Funkcje**
   - Stosuj `snake_case`.
   - Nazwy funkcji powinny być czasownikowe.
   - Funkcja powinna mieć jedną odpowiedzialność.
   - Funkcja publiczna musi mieć type hints i docstring.

Przykłady:

```python
load_eeg_data()
filter_signal()
extract_features()
train_classifier()
evaluate_model()
save_experiment_results()
```

3. **Klasy**
   - Stosuj `PascalCase`.
   - Nazwa klasy powinna być rzeczownikowa.
   - Klasa powinna reprezentować spójną abstrakcję, a nie luźny zbiór funkcji.

Przykłady:

```python
ExperimentConfig
DataPreprocessor
FeatureExtractor
ModelTrainer
ExperimentLogger
```

Dla konfiguracji i prostych struktur danych preferuj `dataclass`:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExperimentConfig:
    """Konfiguracja pojedynczego uruchomienia eksperymentu."""

    dataset_path: Path
    output_dir: Path
    random_seed: int
    sampling_rate_hz: float
    model_name: str
    test_size: float = 0.2
```

---

## 6) Docstringi i type hints (MUST)

Każda nowa funkcja, klasa i metoda dodawana przez agenta lub człowieka musi zawierać kompletne adnotacje typów oraz docstring. Dotyczy to także funkcji pomocniczych i metod prywatnych, jeżeli ich działanie nie jest trywialne.

Docstring powinien opisywać:

- cel naukowy lub obliczeniowy;
- parametry;
- zwracane wartości;
- jednostki, jeżeli są istotne;
- wyjątki;
- założenia metodologiczne, jeżeli funkcja je wprowadza.

Przykład:

```python
def compute_mean_reaction_time(reaction_times_ms: np.ndarray) -> float:
    """Oblicz średni czas reakcji w milisekundach.

    Parameters
    ----------
    reaction_times_ms:
        Jednowymiarowa tablica czasów reakcji w milisekundach.

    Returns
    -------
    float
        Średni czas reakcji w milisekundach.

    Raises
    ------
    ValueError
        Gdy tablica wejściowa jest pusta.
    """
    if reaction_times_ms.size == 0:
        raise ValueError("reaction_times_ms must not be empty.")

    return float(np.mean(reaction_times_ms))
```

---

## 7) Konfiguracja i stałe

Stałe zapisuj wielkimi literami:

```python
DEFAULT_RANDOM_SEED = 42
DEFAULT_SAMPLING_RATE_HZ = 250
MAX_EPOCHS = 100
```

Konfiguracja eksperymentu nie powinna być zaszyta w kodzie. Parametry eksperymentalne przechowuj w plikach:

- `yaml`,
- `toml`,
- `json`,
- ewentualnie jako argumenty CLI.

Przykład pliku `config.yaml`:

```yaml
experiment_name: eeg_baseline_classification
random_seed: 42
dataset_path: data/processed/eeg_dataset.parquet
model:
  name: random_forest
  n_estimators: 500
  max_depth: 12
preprocessing:
  low_cut_hz: 1.0
  high_cut_hz: 40.0
  normalization: z_score
```

Każde uruchomienie eksperymentu powinno zapisywać kopię użytej konfiguracji do katalogu wynikowego.

---

## 8) Przetwarzanie danych

Przetwarzanie danych musi być deterministyczne, jawne i możliwe do odtworzenia.

Wymagania:

- nie modyfikuj danych surowych;
- każdy etap transformacji powinien mieć nazwę i zapisany rezultat albo możliwość ponownego wykonania;
- zapisuj wersję danych wejściowych;
- zapisuj liczbę obserwacji przed i po filtracji;
- dokumentuj kryteria wykluczenia danych;
- nie usuwaj braków danych bez jawnego uzasadnienia;
- nie mieszaj danych treningowych, walidacyjnych i testowych;
- skalowanie, imputacja i selekcja cech muszą być dopasowywane wyłącznie na zbiorze treningowym.

Przykład poprawnego przetwarzania:

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

x_train, x_test, y_train, y_test = train_test_split(
    features,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels,
)

scaler = StandardScaler()
x_train_scaled = scaler.fit_transform(x_train)
x_test_scaled = scaler.transform(x_test)
```

Nie wolno dopasowywać transformacji na całym zbiorze przed podziałem:

```python
# Źle: przeciek informacji ze zbioru testowego
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)
```

---

## 9) Wydajność przetwarzania danych

Kod powinien unikać niepotrzebnych kopii danych oraz pętli Pythona tam, gdzie dostępne są operacje wektorowe.

Zalecenia:

- preferuj `numpy`, `pandas`, `polars`, `scipy`, `numba` lub operacje tensorowe zamiast ręcznych pętli;
- używaj formatów kolumnowych, np. `parquet`, dla dużych tabel;
- unikaj wielokrotnego czytania tych samych danych z dysku;
- cache'uj kosztowne etapy obliczeń;
- przetwarzaj duże dane strumieniowo lub partiami;
- ogranicz liczbę konwersji między `list`, `DataFrame`, `ndarray` i tensorami;
- profiluj kod przed optymalizacją;
- nie optymalizuj kosztem poprawności naukowej.

Przykład:

```python
# Źle
normalized_values = []
for value in values:
    normalized_values.append((value - np.mean(values)) / np.std(values))

# Dobrze
normalized_values = (values - np.mean(values)) / np.std(values)
```

Dla dużych zbiorów danych unikaj `DataFrame.apply`, jeśli można użyć operacji wektorowej:

```python
# Gorzej
df["rt_s"] = df["reaction_time_ms"].apply(lambda value: value / 1000)

# Lepiej
df["rt_s"] = df["reaction_time_ms"] / 1000
```

---

## 10) Replikowalność eksperymentów

Każdy eksperyment musi być możliwy do odtworzenia na podstawie zapisanych artefaktów.

Minimalny zestaw informacji zapisywany dla eksperymentu:

- nazwa eksperymentu;
- data i czas uruchomienia;
- identyfikator commita Git;
- status repozytorium, w tym informacja o niezacommitowanych zmianach;
- wersja Pythona;
- wersje bibliotek;
- system operacyjny;
- parametry konfiguracji;
- ziarna losowości;
- ścieżki i wersje danych;
- metryki;
- logi;
- artefakty wynikowe;
- ewentualne błędy i ostrzeżenia.

Zalecana struktura katalogu eksperymentu:

```text
results/
└── 2026-05-29_1430_eeg_baseline_rf/
    ├── config.yaml
    ├── metrics.json
    ├── environment.txt
    ├── git_info.json
    ├── run.log
    ├── predictions.parquet
    ├── figures/
    └── models/
```

---

## 11) Kontrola losowości

Każde użycie losowości musi być jawne i kontrolowane. Wartość ziarna powinna pochodzić z konfiguracji.

Przykład podstawowy:

```python
import random

import numpy as np


def set_random_seed(seed: int) -> None:
    """Ustaw ziarna losowości dla replikowalnych eksperymentów."""
    random.seed(seed)
    np.random.seed(seed)
```

Przykład dla scikit-learn:

```python
model = RandomForestClassifier(
    n_estimators=500,
    random_state=config.random_seed,
)
```

Przykład dla PyTorch:

```python
import random

import numpy as np
import torch


def set_torch_seed(seed: int) -> None:
    """Ustaw ziarna losowości dla Python, NumPy i PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

Pełna deterministyczność na GPU może obniżyć wydajność i nie zawsze jest gwarantowana dla wszystkich operacji.

---

## 12) Logowanie

Nie używaj `print()` jako podstawowego mechanizmu raportowania przebiegu eksperymentu. Do logów stosuj moduł `logging` albo dedykowane narzędzie eksperymentalne.

Minimalne poziomy logowania:

- `DEBUG` — szczegółowe informacje diagnostyczne;
- `INFO` — główne etapy działania programu;
- `WARNING` — sytuacje nietypowe, ale nieprzerywające działania;
- `ERROR` — błędy uniemożliwiające wykonanie części operacji;
- `CRITICAL` — błędy uniemożliwiające dalszą pracę programu.

Przykład konfiguracji:

```python
import logging
from pathlib import Path


def configure_logging(log_file: Path, level: int = logging.INFO) -> None:
    """Skonfiguruj logowanie do konsoli i pliku."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
```

Logi powinny zawierać informacje o:

- rozpoczęciu i zakończeniu eksperymentu;
- wczytanych danych;
- liczbie próbek i cech;
- parametrach przetwarzania;
- konfiguracji modelu;
- uzyskanych metrykach;
- ścieżkach zapisanych artefaktów;
- błędach i ostrzeżeniach.

---

## 13) Monitorowanie eksperymentów

Dla większych projektów należy stosować narzędzia do monitorowania eksperymentów, np.:

- MLflow,
- Weights & Biases,
- TensorBoard,
- Sacred,
- DVC Experiments.

Monitorowanie powinno obejmować:

- parametry eksperymentu;
- metryki treningowe i walidacyjne;
- artefakty, np. wykresy, modele, predykcje;
- czas wykonania;
- informacje o środowisku;
- wersję kodu;
- wersję danych.

Przykład z MLflow:

```python
import mlflow


def log_experiment_to_mlflow(
    experiment_name: str,
    parameters: dict[str, object],
    metrics: dict[str, float],
    artifact_dir: str,
) -> None:
    """Zapisz parametry, metryki i artefakty eksperymentu w MLflow."""
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        mlflow.log_params(parameters)
        mlflow.log_metrics(metrics)
        mlflow.log_artifacts(artifact_dir)
```

Jeżeli projekt nie używa dedykowanego narzędzia, zapisuj co najmniej `metrics.json`, `config.yaml`, `run.log`, `environment.txt` i `git_info.json`.

---

## 14) Dokumentowanie środowiska

Repozytorium powinno zawierać jednoznaczny sposób odtworzenia środowiska.

Dopuszczalne opcje:

- `requirements.txt`,
- `environment.yml`,
- `pyproject.toml`,
- `poetry.lock`,
- `uv.lock`,
- `conda-lock`.

Wyniki eksperymentów powinny zapisywać dokładne wersje bibliotek:

```bash
python --version > results/current_run/environment.txt
pip freeze >> results/current_run/environment.txt
```

Dodatkowo warto zapisać informacje systemowe:

```python
import platform
import sys


def collect_environment_info() -> dict[str, str]:
    """Zbierz podstawowe informacje o środowisku uruchomieniowym."""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }
```

---

## 15) Testowanie kodu naukowego

Kod naukowy wymaga testów szczególnie tam, gdzie łatwo o błędy numeryczne lub metodologiczne.

Testować należy:

- poprawność kształtów tablic;
- zakresy wartości;
- zachowanie funkcji dla danych brzegowych;
- brak przecieku danych między zbiorem treningowym i testowym;
- deterministyczność wyników przy tym samym ziarnie;
- poprawność metryk;
- stabilność zapisu i odczytu artefaktów.

Przykład:

```python
import numpy as np

from brain_core.features import compute_band_power


def test_compute_band_power_returns_non_negative_value() -> None:
    """Moc pasmowa powinna być nieujemna dla poprawnego sygnału."""
    signal = np.array([0.1, 0.2, 0.3, 0.2, 0.1])
    sampling_rate_hz = 250.0

    band_power = compute_band_power(
        signal=signal,
        sampling_rate_hz=sampling_rate_hz,
        low_hz=8.0,
        high_hz=12.0,
    )

    assert band_power >= 0.0
```

Testy powinny być małe, szybkie i możliwe do uruchomienia lokalnie.

---

## 16) Notebooki

Notebooki są dopuszczalne, ale nie powinny zastępować modularnego kodu w `src/`.

Zasady:

- notebook powinien mieć numer i opisową nazwę, np. `01_exploratory_analysis.ipynb`;
- notebook powinien być możliwy do uruchomienia od początku do końca;
- długie funkcje przenoś do modułów w `src/`;
- wyniki z notebooków traktuj jako eksploracyjne, dopóki nie zostaną przeniesione do skryptów lub pipeline'u;
- przed commitem usuń niepotrzebne wyniki, błędy i tymczasowe komórki.

Przykładowe nazwy:

```text
01_data_inspection.ipynb
02_signal_preprocessing.ipynb
03_feature_extraction.ipynb
04_model_comparison.ipynb
```

---

## 17) Obsługa błędów

Błędy powinny być obsługiwane jawnie. Nie stosuj pustych bloków `except`.

```python
# Źle
try:
    data = load_data(path)
except Exception:
    pass
```

Lepsze rozwiązanie:

```python
try:
    data = load_data(path)
except FileNotFoundError as error:
    logger.error("Dataset file not found: %s", path)
    raise error
```

Komunikaty błędów powinny zawierać kontekst pozwalający zdiagnozować problem.

---

## 18) Stos desktopowego GUI (MUST)

1. **PySide6/Qt jako docelowa biblioteka GUI**
   - Nowe elementy desktopowego GUI buduj w oparciu o `PySide6` i wzorce Qt używane w modułach `brain_model/qt_*`.
   - Nie dodawaj nowych ekranów, widżetów ani przepływów użytkownika opartych na `tkinter`.
   - Istniejące moduły `tkinter` traktuj jako kod legacy/kompatybilności, którego nie należy rozwijać bez osobnej decyzji architektonicznej.

2. **Wykresy w GUI**
   - Osadzanie wykresów w desktopowym GUI realizuj przez backend Matplotlib dla Qt (`matplotlib.backends.backend_qtagg`) oraz komponenty zgodne z `brain_model/qt_plotting.py`.
   - Nie mieszaj backendów GUI w jednym nowym przepływie użytkownika.

3. **Spójność zależności**
   - Każdą zmianę zależności wymaganych przez GUI synchronizuj w `pyproject.toml`, `requirements.txt`, `environment.yml` i dokumentacji użytkowej.
   - `PySide6` jest zależnością uruchomieniową desktopowego GUI.
   - Punktami wejścia pozostają `main_gui.py`, `brain_model.gui:run_gui` oraz skrypt `neuro-sim-gui`.

---

## 19) Polityka językowa (MUST)

1. **Interfejs i opisy dla użytkownika w języku polskim**
   - Wszystkie treści prezentowane użytkownikowi końcowemu, w tym GUI, CLI, raporty, logi użytkowe, opisy scenariuszy i dokumentacja użytkowa, twórz po polsku.

2. **Komentarze w kodzie w języku polskim**
   - Komentarze inline, docstringi objaśniające implementację oraz komentarze projektowe zapisuj po polsku.

3. **Kod i nazewnictwo techniczne w języku angielskim**
   - Nazwy zmiennych, funkcji, klas, modułów, plików konfiguracyjnych i identyfikatorów API muszą pozostać angielskie.
   - Nie tłumacz nazw technicznych używanych w kodzie na polski.

4. **Mapowanie nazw EN→PL dla warstwy prezentacji**
   - Gdy nazwa techniczna po angielsku jest pokazywana użytkownikowi, udostępnij czytelny odpowiednik polski w warstwie UI lub opisu.
   - Jako źródło mapowania stosuj słownik: `docs/english_polish_glossary.md`.

5. **Spójność terminologiczna**
   - Dla tego samego pojęcia używaj jednej, konsekwentnej formy polskiej we wszystkich interfejsach i dokumentach.

---

## 20) Minimalny szablon funkcji

Każda funkcja dodawana do kodu naukowego powinna być zbliżona do poniższego wzorca:

```python
def function_name(input_value: InputType, parameter: float) -> OutputType:
    """Opisz naukowy lub obliczeniowy cel funkcji.

    Parameters
    ----------
    input_value:
        Opis wartości wejściowej.
    parameter:
        Opis parametru, wraz z jednostką, jeśli dotyczy.

    Returns
    -------
    OutputType
        Opis zwracanej wartości.

    Raises
    ------
    ValueError
        Opis niepoprawnych warunków wejściowych.
    """
    if parameter <= 0:
        raise ValueError("parameter must be positive.")

    result = ...
    return result
```

---

## 21) Minimalny szablon eksperymentu

Skrypt eksperymentalny powinien mieć wyraźny punkt wejścia:

```python
from pathlib import Path

from brain_core.config import load_config
from brain_core.logging_utils import configure_logging
from brain_core.reproducibility import set_random_seed


def main(config_path: Path) -> None:
    """Uruchom pełny eksperyment na podstawie konfiguracji."""
    config = load_config(config_path)

    run_dir = create_run_directory(
        base_dir=config.output_dir,
        experiment_name=config.experiment_name,
    )

    configure_logging(run_dir / "run.log")
    set_random_seed(config.random_seed)

    save_config(config, run_dir / "config.yaml")
    save_environment_info(run_dir / "environment.json")
    save_git_info(run_dir / "git_info.json")

    # 1. Wczytanie danych
    # 2. Preprocessing
    # 3. Trenowanie modelu
    # 4. Ewaluacja modelu
    # 5. Zapis metryk i artefaktów


if __name__ == "__main__":
    main(config_path=Path("configs/default.yaml"))
```

---

## 22) Checklist przed zakończeniem zadania

Agent AI ma obowiązek sprawdzić:

- [ ] Czy rozwiązanie jest najprostsze możliwe (KISS)?
- [ ] Czy zakres diffu jest minimalny i zgodny z zadaniem?
- [ ] Czy nie wprowadzono zmian ubocznych poza zakresem?
- [ ] Czy zmiany strukturalne zostały opisane w ADR?
- [ ] Czy konfiguracja/schemat pozostają spójne i walidowalne?
- [ ] Czy testy/weryfikacja potwierdzają działanie?
- [ ] Czy opis PR jasno tłumaczy: **co**, **dlaczego**, **jak sprawdzono**?
- [ ] Czy nowe funkcje, klasy i metody mają type hints oraz docstringi?
- [ ] Czy losowość jest jawnie kontrolowana?
- [ ] Czy zapisują się logi, metryki i konfiguracja eksperymentu?
- [ ] Czy nie doszło do przecieku danych?
- [ ] Czy nie dodano lokalnych ścieżek, sekretów ani dużych artefaktów?

---

## 23) Preferowany styl pracy agenta

1. Najpierw zrozum wymaganie, potem koduj.
2. Najpierw lokalna poprawka, potem ewentualna generalizacja.
3. Jeśli niepewność jest wysoka, zaproponuj 2–3 warianty i wybierz rekomendowany.
4. Przy zmianach architektury: najpierw ADR (`proposed`), potem implementacja.
5. Przy zmianach eksperymentalnych: najpierw konfiguracja i kryteria weryfikacji, potem kod.
6. Po zmianach uruchom testy, linting i formatowanie, jeżeli środowisko na to pozwala.

---

## 24) Checklist przed uruchomieniem eksperymentu

Przed uruchomieniem eksperymentu sprawdź:

- [ ] Czy konfiguracja eksperymentu jest zapisana w pliku?
- [ ] Czy ustawiono ziarno losowości?
- [ ] Czy dane wejściowe są wersjonowane lub jednoznacznie opisane?
- [ ] Czy dane treningowe, walidacyjne i testowe są rozdzielone poprawnie?
- [ ] Czy preprocessing jest dopasowywany tylko na danych treningowych?
- [ ] Czy zapisują się logi?
- [ ] Czy zapisują się metryki?
- [ ] Czy zapisuje się konfiguracja?
- [ ] Czy zapisuje się informacja o środowisku?
- [ ] Czy zapisuje się identyfikator commita Git?
- [ ] Czy wyniki trafiają do jednoznacznego katalogu eksperymentu?

---

## 25) Checklist przed commitem

Przed commitem sprawdź:

- [ ] `ruff check .`
- [ ] `black .`
- [ ] `pytest`
- [ ] brak sekretów i tokenów API;
- [ ] brak dużych plików wynikowych;
- [ ] brak lokalnych ścieżek bezpośrednio w kodzie;
- [ ] docstringi i type hints w nowych funkcjach;
- [ ] aktualna dokumentacja;
- [ ] jasny opis zmian w commicie.

---

## 26) Reguła rozstrzygania konfliktów zasad

Jeżeli występuje konflikt między wytycznymi, obowiązuje następująca hierarchia:

1. Bezpieczeństwo, poprawność systemu i integralność danych.
2. Replikowalność oraz poprawność metodologiczna badań.
3. Polecenie użytkownika.
4. Ten dokument (`AGENTS.md`).
5. Lokalna wygoda implementacyjna.

Agent ma zawsze wybrać opcję bezpieczniejszą, bardziej przewidywalną i lepiej udokumentowaną.

---

## 27) Zasada nadrzędna kodu naukowego

Kod naukowy powinien umożliwiać odpowiedź na pytanie:

> Co dokładnie zostało uruchomione, na jakich danych, z jakimi parametrami, w jakim środowisku i dlaczego uzyskano taki wynik?

Jeżeli repozytorium nie pozwala odpowiedzieć na to pytanie, nie spełnia minimalnego standardu replikowalności badań.
