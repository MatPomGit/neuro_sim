# Wytyczne katalogu lekcji `configs/lessons`

## Cel modułu

Katalog `configs/lessons/` opisuje gotowe przebiegi dydaktyczne dostępne w
desktopowym GUI. Plik lekcji nie jest konfiguracją eksperymentu i nie może
zawierać alternatywnej implementacji tasku, profilu klinicznego ani analizy.
Jego zadaniem jest wskazanie istniejącego pliku `configs/*.yaml` i dodanie
metadanych potrzebnych do poprowadzenia zajęć.

Źródłami prawdy pozostają:

- `configs/*.yaml` dla parametrów eksperymentu, seeda, czasu i profilu;
- `brain_core` dla logiki symulacji, walidacji oraz raportu analitycznego;
- `configs/lessons/*.yaml` dla celu, pytań i oczekiwań dydaktycznych.

Katalog jest wczytywany i walidowany przez `brain_model.lesson_catalog`.
Decyzję o takim podziale odpowiedzialności opisuje
[`ADR-0036`](adr/0036-katalog-lekcji-yaml.md).

## Obowiązkowe pola

Każdy plik `configs/lessons/<id>.yaml` musi zawierać:

| Pole | Typ | Znaczenie |
| --- | --- | --- |
| `id` | `str` | Stabilny identyfikator techniczny zapisany w `snake_case`; musi być zgodny z nazwą pliku. |
| `label_pl` | `str` | Polska etykieta GUI rozpoczynająca się od `Lekcja — `. |
| `level_pl` | `str` | Poziom zajęć, np. `podstawowy`, `średni` albo `zaawansowany`. |
| `estimated_duration_min` | `int` | Dodatni, realistyczny czas zajęć w minutach. |
| `scenario_config` | `str` | Istniejąca ścieżka względna do konfiguracji eksperymentu YAML. |
| `comparison_config` | `str \| null` | Istniejąca konfiguracja porównania profili albo `null`. |
| `learning_goal_pl` | `str` | Jeden mierzalny cel dydaktyczny zapisany po polsku. |
| `pre_run_questions_pl` | `list[str]` | Niepusta lista pytań stawianych przed uruchomieniem. |
| `expected_observations_pl` | `list[str]` | Niepusta lista obserwacji, które można sprawdzić w artefaktach wyniku. |
| `post_run_questions_pl` | `list[str]` | Niepusta lista pytań wymagających odwołania do wyniku. |
| `next_run_changes` | `list[map]` | Niepusta lista kontrolowanych zmian dla następnego przebiegu. |

Każdy wpis `next_run_changes` musi zawierać dokładnie opisane wartości:

- `element` — polska nazwa zmienianego parametru lub profilu;
- `current_value` — wartość użyta w konfiguracji bazowej;
- `next_value` — wartość proponowana do porównania;
- `reason` — dydaktyczne uzasadnienie zmiany.

Wartości liczbowe w tej sekcji zapisuj jako tekst, jeżeli mają być prezentowane
bezpośrednio w GUI lub eksporcie. Dzięki temu format, jednostki i oznaczenia nie
są zmieniane przez parser YAML.

## Zasady tworzenia lekcji

1. **Wskaż istniejący eksperyment.** Najpierw przygotuj i zwaliduj
   `scenario_config`; dopiero potem dodaj kartę lekcji.
2. **Nie duplikuj parametrów.** Seed, czas, model, profil i analiza pozostają w
   konfiguracji eksperymentu. Lekcja może się do nich odwoływać w opisie, ale
   nie może nadpisywać ich własnymi polami.
3. **Formułuj sprawdzalne obserwacje.** Każda pozycja
   `expected_observations_pl` powinna wskazywać artefakt widoczny w GUI lub
   raporcie, np. oś czasu, tabelę triali, profil, metrykę albo parametr SNN.
4. **Kontroluj porównanie.** `next_run_changes` powinno zmieniać jeden element
   naraz. Seed należy zachować, chyba że celem lekcji jest jawne badanie wpływu
   sekwencji losowej.
5. **Oddzielaj przewidywanie od wyniku.** Pytania przed uruchomieniem dotyczą
   hipotezy; pytania po uruchomieniu wymagają użycia zapisanych artefaktów.
6. **Stosuj język polski.** Treści prezentacyjne są po polsku, a identyfikatory,
   nazwy plików i pola YAML pozostają po angielsku.
7. **Unikaj interpretacji klinicznej.** Profile zaburzeń i uszkodzeń są
   scenariuszami dydaktycznymi. Nie opisuj metryk jako diagnozy, normy
   psychometrycznej ani pomiaru pacjenta.
8. **Podawaj ograniczenia modelu.** W lekcjach zaawansowanych wskaż, które
   sygnały są proxy, uproszczeniem albo demonstracją kontraktu technicznego.

## Szablon

```yaml
id: example_lesson
label_pl: Lekcja — przykładowy temat
level_pl: podstawowy
estimated_duration_min: 45
scenario_config: configs/example.yaml
comparison_config: null
learning_goal_pl: Uczestnik wyjaśnia sprawdzalny efekt modelu.
pre_run_questions_pl:
  - Jakiego kierunku zmiany oczekujesz przed uruchomieniem?
expected_observations_pl:
  - Raport pokazuje artefakt pozwalający sprawdzić przewidywanie.
post_run_questions_pl:
  - Czy wynik jest zgodny z przewidywaniem i na jakiej podstawie?
next_run_changes:
  - element: Nazwa parametru
    current_value: "wartość bazowa"
    next_value: "wartość porównawcza"
    reason: Uzasadnienie kontrolowanego porównania.
```

## Procedura dodawania nowej lekcji

1. Uruchom wskazaną konfigurację przez:

   ```bash
   python -m brain_core.simulation.run --config configs/example.yaml
   ```

2. Dodaj `configs/lessons/<id>.yaml`, zachowując zgodność `id` z nazwą pliku.
3. Jeżeli lekcja używa porównania profili, wskaż istniejący plik
   `configs/comparisons/*.yaml`.
4. Sprawdź, czy pytania i obserwacje odnoszą się do faktycznie generowanych
   artefaktów.
5. Uruchom walidację katalogu:

   ```bash
   pytest tests/test_lesson_configs_static.py
   ```

6. Uruchom testy statyczne integracji z GUI:

   ```bash
   pytest tests/test_qt_sections.py tests/test_qt_yaml_scenarios_static.py
   ```

7. Jeżeli zmieniasz kontrakt pól, zaktualizuj jednocześnie:
   `brain_model/lesson_catalog.py`, testy, ten dokument oraz ADR-0036. Taka
   zmiana wymaga jawnej ścieżki migracji lub czytelnego błędu walidacji.

## Lista kontrolna przeglądu

- [ ] `id` jest unikalny i zgodny z nazwą pliku.
- [ ] `label_pl` jest unikalne, polskie i rozpoczyna się od `Lekcja — `.
- [ ] Wskazane pliki konfiguracji istnieją.
- [ ] Cel jest mierzalny podczas jednego przebiegu zajęć.
- [ ] Oczekiwane obserwacje mają odpowiedniki w raporcie lub GUI.
- [ ] Następny przebieg zmienia jeden jawny element.
- [ ] Interpretacja nie sugeruje zastosowania diagnostycznego.
- [ ] Czas zajęć uwzględnia uruchomienie, analizę i dyskusję.
