# Roving Oddball — od bodźca do interpretacji

Ten przewodnik dydaktyczny prowadzi przez scenariusz `roving_oddball` od
pojedynczego bodźca, przez budowę deterministycznej sekwencji, po ostrożną
interpretację raportu. Materiał jest przeznaczony dla osób uczących się pracy z
zadaniem oddball w `neuro_sim`: najpierw wyjaśnia pojęcia, potem pokazuje, co
robi konfiguracja, jak uruchomić symulację i jak czytać metryki bez nadawania im
nadmiernej wartości klinicznej.

`roving_oddball` jest scenariuszem referencyjnym do obserwacji predykcji
sensorycznej, nowości, habituacji i readaptacji po zmianie regularności bodźców.
Zadanie używa jawnego seeda, dlatego ta sama konfiguracja generuje tę samą
sekwencję triali i pozwala porównywać profile `healthy`, `disorder` oraz
`lesion` bez mieszania efektów profilu klinicznego z losowością bodźców.

> **Najważniejsza zasada dydaktyczna:** zmieniaj jeden parametr naraz. Jeśli
> jednocześnie zmienisz seed, długość runów, prawdopodobieństwo dewiantu i profil
> kliniczny, nie da się bezpiecznie wskazać, która zmiana spowodowała różnicę w
> raporcie.

## 1. Cel zadania w jednym akapicie

W klasycznym paradygmacie oddball uczestnik lub model słyszy wiele powtarzalnych
bodźców standardowych oraz rzadsze bodźce odmienne. W wariancie **roving** bodziec
odmienny nie jest tylko jednorazowym wyjątkiem: po zmianie może stać się nowym
standardem. Dzięki temu zadanie pokazuje dwa procesy naraz:

1. **budowanie przewidywania** — kolejne standardy w runie są coraz bardziej
   oczekiwane;
2. **aktualizację przewidywania** — dewiant narusza oczekiwanie, a następnie
   system musi przyjąć go jako nową regularność.

W `neuro_sim` ten scenariusz jest uproszczonym modelem edukacyjnym i regresyjnym.
Nie jest to samodzielnie zwalidowany marker diagnostyczny chorób neurologicznych
ani psychiatrycznych.

## 2. Słownik pojęć

| Pojęcie | Znaczenie w przewodniku | Pole w wynikach |
| --- | --- | --- |
| **Trial** | Pojedyncze wystąpienie bodźca w czasie; w obiekcie bodźca ma też `onset_s` i `duration_s`. | `trial_id` |
| **Standard** | Powtarzający się bodziec o tej samej częstotliwości tonu. | `condition: "standard"` |
| **Dewiant** | Bodziec odbiegający od aktualnego standardu. | `condition: "deviant"` |
| **Nowy standard** | Pierwszy standard po dewiancie; ma częstotliwość poprzedniego dewiantu. | `is_new_standard: true` |
| **Run** | Blok kolejnych standardów poprzedzających ewentualny dewiant. | `run_index` |
| **Habituacja** | Narastanie przewidywalności i osłabianie reakcji na powtarzalny bodziec. | `habituation_level` |
| **Surprise index** | Uproszczony wskaźnik zaskoczenia bodźcem. | `surprise_index` |
| **Readaptacja** | Ponowne dopasowanie do regularności po dewiancie. | `readaptation_latency` |

## 3. Jak powstaje sekwencja bodźców

Generator zadania tworzy sekwencję w kilku prostych krokach:

1. wybiera początkowy ton z puli częstotliwości;
2. losuje deterministycznie długość runu standardów na podstawie `seed`,
   `run_length_min` i `run_length_max`;
3. dodaje kolejne standardy z narastającym `habituation_level`;
4. po runie, o ile nie jest to ostatni run, decyduje na podstawie
   `deviant_probability`, czy dodać dewiant;
5. jeśli dewiant zostanie dodany, wybiera inną częstotliwość tonu i nadaje mu
   dodatni `surprise_index`;
6. w następnym runie pierwszy standard ma tę samą częstotliwość co poprzedni
   dewiant i jest oznaczony jako `is_new_standard`.

Przykład przy stałej długości runu `2` i pewnym dewiancie po każdym runie poza
ostatnim:

```text
standard → standard → deviant → nowy standard → standard → deviant → nowy standard → standard
```

Interpretacja tej osi czasu:

- pierwsze dwa bodźce budują oczekiwanie pierwszej regularności;
- trzeci bodziec łamie regularność i jest dewiantem;
- czwarty bodziec nie jest już dewiantem, tylko pierwszym standardem nowej
  regularności;
- następne standardy ponownie budują przewidywanie.

## 4. Parametry konfiguracji

Referencyjne konfiguracje znajdują się w `configs/` i mają ten sam opis zadania,
aby umożliwić porównanie profili przy identycznej sekwencji bodźców.

| Parametr | Przykład | Znaczenie dydaktyczne |
| --- | ---: | --- |
| `seed` | `21` | Ziarno deterministycznej sekwencji. Przy tym samym seedzie sekwencja triali jest powtarzalna. |
| `task.name` | `roving_oddball` | Nazwa zadania przekazywana do silnika. Alias `roving-oddball` jest wspierany w kodzie, ale w konfiguracjach używaj formy z podkreśleniem. |
| `task.duration` | `30.0` | Maksymalny czas sekwencji w sekundach. Gdy onset kolejnego trialu przekroczy czas, generator kończy sekwencję. |
| `task.n_runs` | `6` | Liczba bloków standardów. Więcej runów daje więcej okazji do obserwacji dewiantów i readaptacji. |
| `task.run_length_min` | `3` | Minimalna liczba standardów w runie. |
| `task.run_length_max` | `6` | Maksymalna liczba standardów w runie. |
| `task.deviant_probability` | `1.0` | Prawdopodobieństwo dodania dewiantu po runie, poza ostatnim runem. |
| `task.inter_stimulus_interval` | `0.8` | Bazowy odstęp między onsetami bodźców w sekundach. |
| `task.jitter` | `0.05` | Deterministyczne odchylenie od bazowego odstępu. `0.0` ułatwia naukę na idealnie równych odstępach. |

### Jak dobierać parametry na zajęciach

- **Pierwsza demonstracja:** ustaw `run_length_min = run_length_max = 2`,
  `deviant_probability = 1.0` i `jitter = 0.0`. Sekwencja będzie krótka i łatwa do
  ręcznego sprawdzenia.
- **Demonstracja habituacji:** zwiększ `run_length_min` i `run_length_max`, aby
  pokazać więcej stopni narastania `habituation_level` w obrębie runu.
- **Demonstracja niepewności:** obniż `deviant_probability`, ale zachowaj ten sam
  seed przy porównaniach. Wtedy część runów może nie kończyć się dewiantem.
- **Demonstracja osi czasu:** zwiększ `jitter`, aby pokazać, że czasy onsetów nadal
  są deterministyczne, ale nie są idealnie równoodległe.

## 5. Trzy profile referencyjne

Projekt zawiera trzy gotowe warianty, które różnią się profilem klinicznym i
patologią, a nie opisem sekwencji bodźców:

| Plik | Profil | Intencja dydaktyczna |
| --- | --- | --- |
| `configs/roving_oddball_healthy.yaml` | `healthy_v1` | Punkt odniesienia bez jawnie modelowanej patologii. |
| `configs/roving_oddball_disorder_gaba.yaml` | `gaba_dysregulation` | Przykład zaburzenia regulacji hamowania i szumu aktywacji. |
| `configs/roving_oddball_lesion_hippocampus.yaml` | `hippocampal_lesion` | Przykład ograniczenia integracji epizodycznej i przewidywania sensorycznego. |

Wszystkie trzy konfiguracje referencyjne używają `seed: 21` oraz tych samych
parametrów `task`. Dzięki temu różnice między profilami można omawiać jako efekt
profilu, o ile raport porównawczy potwierdza `same_sequence: true`.

## 6. Uruchomienie krok po kroku

### 6.1. Uruchomienie pojedynczej konfiguracji w Pythonie

Najprostszy sposób pracy dydaktycznej to uruchomienie konfiguracji przez loader i
silnik symulacji:

```python
from pathlib import Path

from brain_core.simulation.config_loader import load_config
from brain_core.simulation.engine import run_experiment

config = load_config(Path("configs/roving_oddball_healthy.yaml"))
result = run_experiment(config)
roving_report = result["analysis_report"]["roving_oddball"]
```

W kodzie produkcyjnym i eksperymentalnym nie używaj `print()` jako głównego
mechanizmu raportowania. Powyższy fragment pozostawia raport w zmiennej
`roving_report`, którą można obejrzeć w konsoli interaktywnej, notebooku albo
zapisać przez istniejące mechanizmy raportowania.

### 6.2. Minimalna konfiguracja tworzona w kodzie

```python
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_experiment

config = ExperimentConfig(
    seed=21,
    task={
        "name": "roving_oddball",
        "scenario": "roving_oddball",
        "duration": 8.0,
        "n_runs": 3,
        "run_length_min": 2,
        "run_length_max": 2,
        "deviant_probability": 1.0,
        "inter_stimulus_interval": 0.5,
        "jitter": 0.0,
    },
    output={"save_results": False},
)

result = run_experiment(config)
trial_results = result["trial_results"]
roving_report = result["analysis_report"]["roving_oddball"]
```

Taki wariant jest dobry do testów i ćwiczeń, ale pełne eksperymenty powinny
korzystać z plików konfiguracyjnych, aby zachować replikowalność.

### 6.3. Porównanie profili przy tej samej sekwencji

```python
from brain_core.simulation.config_schema import ExperimentConfig
from brain_core.simulation.engine import run_task_across_clinical_profiles

base_config = ExperimentConfig(
    seed=21,
    task={
        "name": "roving_oddball",
        "scenario": "roving_oddball",
        "duration": 30.0,
        "n_runs": 6,
        "run_length_min": 3,
        "run_length_max": 6,
        "deviant_probability": 1.0,
        "inter_stimulus_interval": 0.8,
        "jitter": 0.05,
    },
    output={"save_results": False},
)

batch = run_task_across_clinical_profiles(
    base_config,
    [healthy_profile, disorder_profile, lesion_profile],
)
comparison = batch["roving_profile_comparison"]
```

Pole `comparison["same_sequence"]` musi mieć wartość `True`, jeśli chcesz omawiać
różnice jako porównanie profili przy tej samej sekwencji bodźców.

## 7. Jak czytać wyniki trial po trialu

Każdy wynik trialu powinien być czytany jako mała obserwacja o strukturze:

| Pole | Jak je czytać |
| --- | --- |
| `trial_id` | Kolejny numer trialu. Pomaga odtworzyć porządek sekwencji. |
| `condition` | `standard` albo `deviant`. To podstawowa etykieta bodźca. |
| `tone_hz` | Częstotliwość tonu użyta w trialu. |
| `previous_standard_hz` | Dla dewiantu: częstotliwość standardu, względem którego bodziec był odmienny. |
| `run_index` | Numer runu, w którym znajduje się trial. |
| `repetition_index` | Pozycja standardu w runie albo pozycja dewiantu po runie. |
| `is_new_standard` | `True`, gdy standard jest pierwszym standardem po dewiancie. |
| `surprise_index` | Wartość bliska `0.0` dla standardów; dodatnia dla dewiantów. |
| `habituation_level` | Narasta w standardach od początku do końca runu. |
| `readaptation_latency` | Dodatnia po dewiancie i na początku readaptacji; agregowana w raporcie. |

Ćwiczenie dla studentów:

1. wypisz pierwszych 8 triali;
2. zaznacz dewianty;
3. znajdź pierwszy standard po każdym dewiancie;
4. sprawdź, czy `tone_hz` nowego standardu jest taki sam jak `tone_hz`
   poprzedniego dewiantu;
5. porównaj `habituation_level` w obrębie każdego runu.

## 8. Raport dla pojedynczego uruchomienia

Dla zadania `roving_oddball` raport analizy zawiera sekcję **Raport roving
oddball**. Sekcja agreguje:

1. liczbę triali `standard`, `deviant` i `nowy standard`;
2. średni `surprise_index` po całej sekwencji;
3. tempo habituacji (`habituation_rate`), liczone jako średni dodatni przyrost
   `habituation_level` między kolejnymi standardami tego samego runu;
4. latency readaptacji (`mean_readaptation_latency`), liczone jako średnia
   dodatnich wartości `readaptation_latency`.

### Interpretacja agregatów

| Metryka | Pytanie dydaktyczne | Bezpieczna interpretacja | Czego nie wolno wnioskować |
| --- | --- | --- | --- |
| `standard_count` | Ile było bodźców przewidywalnych? | Pokazuje strukturę sekwencji. | Nie mówi sama w sobie o jakości modelu. |
| `deviant_count` | Ile razy naruszono regularność? | Pozwala sprawdzić, czy scenariusz faktycznie zawierał oddballe. | Nie jest automatycznie miarą trudności klinicznej. |
| `new_standard_count` | Ile razy dewiant stał się nową regularnością? | Pokazuje liczbę epizodów readaptacji. | Nie oznacza liczby poprawnych detekcji. |
| `mean_surprise_index` | Jak dużo zaskoczenia było średnio w sekwencji? | Wyższa wartość zwykle oznacza większy udział lub wagę dewiantów. | Nie jest zwalidowaną amplitudą MMN/P300. |
| `habituation_rate` | Jak szybko narastała przewidywalność w runach? | Dodatnia wartość potwierdza narastanie `habituation_level`. | Nie dowodzi rzeczywistej adaptacji neuronalnej bez walidacji. |
| `mean_readaptation_latency` | Jak długi był średni okres ponownego dopasowania? | Ułatwia porównanie sekwencji i profili w symulacji. | Nie jest klinicznym czasem reakcji pacjenta. |

## 9. Porównanie profili

Porównanie `healthy`/`disorder`/`lesion` powinno zachowywać ten sam `seed` i tę samą
sekcję `task`, aby każdy profil otrzymał identyczną sekwencję standardów,
dewiantów i nowych standardów. W kodzie zapewnia to funkcja
`run_task_across_clinical_profiles`, która uruchamia wspólną konfigurację bazową
dla kolejnych profili klinicznych i dodaje `roving_profile_comparison` dla zadania
`roving_oddball`.

Wynik `batch["roving_profile_comparison"]` zawiera:

- `seed` — ziarno sekwencji;
- `same_seed` — informację, czy porównanie zostało zbudowane na wspólnym seedzie;
- `same_sequence` — informację, czy sygnatury triali są identyczne między profilami;
- `profiles` — listę agregatów dla profili;
- `profile_group` — etykietę `healthy`, `disorder` albo `lesion` dla każdego
  profilu;
- `mean_surprise_index`, `habituation_rate` i `mean_readaptation_latency` dla
  każdego profilu.

### Reguła interpretacyjna

- Jeśli `same_sequence == True`, można omawiać różnice agregatów jako wynikające z
  modelowanego profilu i dynamiki symulacji.
- Jeśli `same_sequence == False`, najpierw wyjaśnij różnice w sekwencji. W takim
  przypadku porównanie profili nie jest czystym porównaniem mechanizmu
  klinicznego.
- Jeśli `same_seed == True`, ale `same_sequence == False`, sprawdź, czy profile nie
  zmieniły parametrów `task` albo czy nie użyto innej wersji kodu.

## 10. Najczęstsze pułapki interpretacyjne

1. **Mylenie dewiantu z nowym standardem.** Dewiant jest naruszeniem aktualnej
   regularności. Nowy standard to pierwszy bodziec następnej regularności.
2. **Interpretowanie metryk jako biomarkerów.** Metryki są wskaźnikami
   dydaktycznymi i regresyjnymi. Nie zastępują walidacji EEG, fMRI ani danych
   behawioralnych.
3. **Porównywanie profili przy różnych sekwencjach.** Różny seed lub różne
   parametry `task` mogą wprowadzić różnice niezależne od profilu.
4. **Ignorowanie `duration`.** Zbyt krótki czas może uciąć końcówkę sekwencji, więc
   liczba triali będzie mniejsza od intuicyjnie oczekiwanej.
5. **Zbyt wiele zmian naraz.** W dydaktyce i analizie regresyjnej zmieniaj jeden
   parametr, zapisz konfigurację i dopiero wtedy porównuj raport.

## 11. Proponowany scenariusz zajęć

### Etap A — rozpoznanie sekwencji

1. Uruchom konfigurację z krótkimi runami (`2–2`) i bez jittera.
2. Poproś uczestników o ręczne oznaczenie: standard, dewiant, nowy standard.
3. Sprawdźcie wspólnie `tone_hz`, `previous_standard_hz` i `is_new_standard`.

### Etap B — habituacja

1. Zwiększ długość runów do `4–6`.
2. Porównaj `habituation_level` na początku i końcu runu.
3. Omów, dlaczego `habituation_rate` jest agregatem, a nie pojedynczym wynikiem
   jednego trialu.

### Etap C — readaptacja

1. Ustaw `deviant_probability = 1.0`, aby każdy run poza ostatnim kończył się
   dewiantem.
2. Znajdź pierwszy standard po dewiancie.
3. Omów, dlaczego stary dewiant staje się nowym standardem.

### Etap D — porównanie profili

1. Uruchom trzy konfiguracje referencyjne z tym samym seedem.
2. Sprawdź `same_sequence` w raporcie porównawczym.
3. Porównaj agregaty profili.
4. Zapisz wniosek z zastrzeżeniem, że to interpretacja symulacyjna, a nie diagnoza.

## 12. Mini-checklista przed interpretacją

Przed zapisaniem wniosku odpowiedz na pytania:

- [ ] Czy konfiguracja eksperymentu była zapisana w pliku albo jawnie pokazana?
- [ ] Czy seed był taki sam w porównywanych warunkach?
- [ ] Czy parametry `task` były takie same w porównywanych profilach?
- [ ] Czy raport porównawczy ma `same_sequence: true`?
- [ ] Czy liczba `deviant_count` jest większa od zera, jeśli interpretujesz
      reakcję na nowość?
- [ ] Czy rozróżniasz `deviant` i `nowy standard`?
- [ ] Czy unikasz języka diagnostycznego bez walidacji klinicznej?
- [ ] Czy wynik odnosisz do wersji kodu, konfiguracji i środowiska?

## 13. Krótki wzorzec opisu wyniku

Bezpieczny opis dydaktyczny może wyglądać tak:

> W konfiguracji `roving_oddball_healthy` z seedem `21` sekwencja zawierała
> standardy, dewianty i nowe standardy. Raport pokazał dodatnie tempo habituacji,
> co potwierdza, że w obrębie runów narastał `habituation_level`. Średni
> `surprise_index` odzwierciedla obecność dewiantów w sekwencji. Wynik traktujemy
> jako wskaźnik symulacyjny i materiał dydaktyczny, a nie marker kliniczny.

Dla porównania profili dodaj:

> Porównanie profili jest interpretowane tylko dlatego, że użyto tego samego seeda
> i raport potwierdził `same_sequence: true`. Różnice agregatów opisują zachowanie
> modelu przy wspólnej sekwencji bodźców.

## 14. Powiązane pliki w projekcie

- `brain_core/experiments/protocols.py` — definicja `RovingOddballTask`, generowanie
  bodźców, oczekiwana odpowiedź i ocena trialu.
- `brain_core/simulation/engine.py` — uruchamianie zadania, dołączanie raportu
  `roving_oddball` i budowa porównania profili.
- `brain_core/analysis/reports.py` — agregacja metryk roving oddball i renderowanie
  sekcji raportu Markdown.
- `configs/roving_oddball_healthy.yaml` — referencyjny wariant zdrowy.
- `configs/roving_oddball_disorder_gaba.yaml` — wariant dysregulacji GABA.
- `configs/roving_oddball_lesion_hippocampus.yaml` — wariant lezji hipokampa.
- `tests/test_task_protocols_and_engine.py` — testy deterministyczności sekwencji,
  obecności metryk trial-level oraz sekcji raportu.

## 15. Podsumowanie

`roving_oddball` uczy, jak z powtarzalnego bodźca powstaje oczekiwanie, jak
dewiant narusza to oczekiwanie i jak nowa regularność zostaje przyjęta jako
standard. Największa wartość scenariusza leży w kontrolowanej, replikowalnej osi
czasu: przy tym samym seedzie można oddzielić strukturę bodźców od efektów profilu
klinicznego i bezpiecznie omawiać różnice w metrykach symulacyjnych.
