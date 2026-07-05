# Kontrole statyczne: type hinty i docstringi

Ten dokument opisuje, jak uruchamiać kontrole jakości kodu oraz jak rozróżnić tryb **legacy (ostrzeżenia)** od trybu **gating PR (blokowanie nowych braków)**.

## 1) Narzędzia

- `mypy` — statyczna analiza type hintów.
- `ruff` + `pydocstyle` (`D*`) — kontrola jakości docstringów (konwencja Google).

Konfiguracja narzędzi znajduje się w `pyproject.toml`.

## 2) Poziomy rygoru

### Poziom A — legacy (tylko ostrzeżenia)

Używaj lokalnie lub podczas porządkowania starszego kodu.

```bash
python -m mypy brain_core brain_model analysis main.py main_gui.py run_gui.py || true
python -m ruff check . --exit-zero
```

Interpretacja:
- Wynik może zawierać błędy, ale nie zatrzymuje przebiegu.
- Służy do obserwacji długu technicznego w istniejących modułach.

### Poziom B — gating PR (blokowanie nowych braków)

Używaj w CI dla plików modyfikowanych w PR.

```bash
CHANGED_PY_FILES="$(git diff --name-only --diff-filter=ACMRT origin/main...HEAD | grep '\.py$' || true)"
if [ -n "$CHANGED_PY_FILES" ]; then
  python -m mypy $CHANGED_PY_FILES
  python -m ruff check $CHANGED_PY_FILES --select D
fi
```

Interpretacja:
- Jeśli nowo zmienione pliki Python mają braki typów lub docstringów, kontrola kończy się błędem.
- Legacy pozostaje poza blokadą PR, dopóki plik nie jest modyfikowany.

## 3) Zalecany workflow dla dewelopera

1. Przed commitem uruchom poziom A, aby zobaczyć pełny stan jakości.
2. Przed push/PR uruchom poziom B dla aktualnego diffu.
3. W opisie PR zawsze podaj:
   - **co uzupełniono** (np. type hinty, docstringi, poprawki konwencji),
   - **dlaczego** (np. zgodność z polityką jakości),
   - **jak zweryfikowano** (dokładne komendy i wynik).

## 4) Szablon raportowania w PR

```text
## Kontrole statyczne
- Co uzupełniono: ...
- Dlaczego: ...
- Jak zweryfikowano:
  - python -m mypy ...
  - python -m ruff check ...
```


## 5) Zakres migracji 2026-06

Migracja jakości obejmuje najpierw moduły naukowe, których wynik wpływa na
interpretację eksperymentów i raportów:

- `brain_model/oscillators.py` — dynamika oscylatorów Wilsona-Cowana;
- `brain_model/calibration.py` — sweep kalibracyjny i zapis metryk;
- `brain_model/validation.py` — heurystyczna walidacja przebiegów symulacji;
- publiczne funkcje `brain_model/plotting.py` — prezentacja aktywności,
  diagnostyki, EEG, mocy pasm i zachowania.

Dla produkcyjnych pakietów `brain_core` i `brain_model` nie wolno już wyłączać
całej rodziny reguł `D`. Etap 2026-06 rozszerzył tę zasadę na katalogi `scripts`
oraz `analysis`: one również nie mogą używać globalnego ignorowania `D`.
Przegląd 2026-07 potwierdził, że moduły `analysis/**/*.py` przechodzą kontrolę
`ruff --select D` bez wyjątków, dlatego usunięto dla nich tymczasową listę
ignorowanych reguł. Przegląd 2026-07 usunął także dług `D100` i `D416` w
zakresach `brain_core/**/*.py`, `brain_model/**/*.py` oraz `scripts/**/*.py`:
moduły produkcyjne mają docstring modułu, a nagłówki sekcji docstringów kończą
się dwukropkiem zgodnie z konwencją Google. Pozostałe jawne wyjątki są nadal
ograniczone, ponieważ ich pełne usunięcie wymagałoby masowych poprawek
stylistycznych w kodzie legacy i utrudniłoby ocenę merytorycznego diffu.

Zmiana w tym etapie oznacza, że:

- `analysis/**/*.py` nie ma już wyjątków docstringowych w `pyproject.toml`;
- `scripts/**/*.py` ma w `pyproject.toml` identyczną listę pozostałych reguł
  migracyjnych jak `brain_core/**/*.py` oraz `brain_model/**/*.py`;
- `D100` i `D416` nie są już dozwolone jako wyjątki produkcyjne;
- nie wolno zastępować żadnej jawnej listy skrótem `D`, ponieważ ukrywałoby to
  nowe klasy naruszeń docstringów;
- kolejne PR-y dotykające tych katalogów powinny usuwać konkretne wyjątki
  lokalnie, gdy poprawiają odpowiadające im docstringi;
- pozostałe obszary legacy, np. pojedyncze punkty wejścia i moduły
  kompatybilności, pozostają poza tym etapem do czasu osobnej migracji.

Tymczasowe wyjątki w `pyproject.toml` są ograniczone do jawnie wymienionych
reguł długu migracyjnego:

- `D104` — brak docstringa pakietu;
- `D107` — brak docstringa metody `__init__`, gdy klasa lub metoda publiczna ma
  osobny opis semantyki;
- `D200`, `D202`, `D205`, `D212`, `D214`, `D301`, `D401`, `D405`,
  `D411`, `D413`, `D415`, `D417` — istniejące niespójności
  stylu docstringów w starszych modułach, usuwane partiami bez masowego
  formatowania całego repozytorium.

Wyjątki te są migracyjne: nie zwalniają nowych funkcji, klas ani metod z
obowiązku posiadania docstringów zgodnych z konwencją Google.

## 6) Zaostrzone typowanie modułów naukowych

`mypy` ma włączone `disallow_untyped_defs` oraz `disallow_incomplete_defs` dla:

- `brain_model.oscillators`;
- `brain_model.calibration`;
- `brain_model.validation`.

Konfiguracja `tool.mypy.python_version` jest ustawiona na `3.12`, aby lokalna
kontrola typów była zgodna z aktualnym środowiskiem narzędziowym i stubami
NumPy/Matplotlib używanymi przez mypy. Zgodność składniowa kodu z minimalnym
Pythonem projektu pozostaje pilnowana osobno przez `requires-python` oraz
`ruff.target-version = "py310"`.

Pełne włączenie dla całego repozytorium pozostaje osobnym etapem, ponieważ kod
GUI i integracje Matplotlib/Qt nadal używają dynamicznych obiektów bibliotek
zewnętrznych. Do czasu zakończenia migracji każda nowa funkcja w modułach
naukowych powinna mieć kompletne adnotacje typów, a użycie `Any` musi wynikać z
rzeczywistej granicy z biblioteką dynamiczną lub strukturą danych o zmiennym
schemacie.

## 7) Dodatkowy test statyczny polityki jakości

Test `tests/test_quality_policy_static.py` pilnuje, aby:

- produkcyjne moduły `brain_core`, `brain_model`, `scripts` i `analysis` nie
  wróciły do globalnego ignorowania `D`;
- `analysis/**/*.py` pozostał bez wyjątków docstringowych po zakończeniu lokalnej
  migracji;
- zakresy nadal objęte etapową migracją miały wyłącznie jawnie zaakceptowane
  reguły `D*`, dzięki czemu dodanie nowego wyjątku wymaga świadomej aktualizacji
  polityki jakości;
- zaostrzone opcje `mypy` pozostały włączone dla kluczowych modułów naukowych;
- wybrane moduły naukowe nie zawierały nieuzasadnionego importu ani użycia
  `typing.Any`.
- testy nie zwiększały liczby funkcji testowych z adnotacją zwrotu `-> Any`;
  pozostały dług legacy jest opisany jako licznik bazowy w teście statycznym i
  powinien maleć przy kolejnych lokalnych migracjach.

Po każdej zmianie w `pyproject.toml` dotyczącej `tool.ruff.lint.per-file-ignores`
należy uruchomić:

```bash
pytest tests/test_quality_policy_static.py -q
```

Kryterium zakończenia migracji: wszystkie jawnie wymienione wyjątki
`D*` zostaną usunięte z wyjątków produkcyjnych, a `disallow_untyped_defs` oraz
`disallow_incomplete_defs` zostaną włączone globalnie po przejściu `mypy` i
`ruff check --select D` dla `brain_core`, `brain_model`, `analysis`, `scripts`,
`main.py`, `main_gui.py` i `run_gui.py` bez błędów.

## 8) Instrukcje operacyjne dla agentów AI

Agent AI wprowadzający kod w repozytorium musi stosować poniższą sekwencję.
Jeżeli zadanie ma węższy zakres, nadal obowiązuje minimalny wariant kontroli dla
modyfikowanych plików.

### 8.1 Przed edycją

1. Sprawdź, czy modyfikowany plik znajduje się w module objętym ostrzejszym
   typowaniem w `pyproject.toml`.
2. Jeżeli zmieniasz kod naukowy lub eksperymentalny, zaplanuj test dla:
   - kształtów tablic;
   - zakresów wartości;
   - deterministyczności przy tym samym ziarnie;
   - braku przecieku danych;
   - zapisu artefaktów, jeśli funkcja zapisuje wyniki.
3. Nie uruchamiaj automatycznego formatowania na całym repozytorium, jeśli
   zadanie dotyczy tylko kilku plików. Formatowanie ogranicz do plików, które
   rzeczywiście edytujesz.

### 8.2 Podczas pisania kodu

1. Każda nowa lub zmieniana funkcja publiczna musi mieć kompletne adnotacje
   typów i docstring opisujący cel, parametry, wynik oraz wyjątki.
2. Funkcje prywatne również wymagają adnotacji typów. Docstring jest wymagany,
   gdy funkcja wykonuje nietrywialną walidację, transformację danych,
   obliczenia numeryczne, operacje I/O albo obsługuje losowość.
3. Nie używaj `typing.Any` jako sposobu na wyciszenie `mypy`. Dopuszczalne
   przypadki to wyłącznie:
   - granica z dynamiczną biblioteką zewnętrzną, np. Matplotlib, Qt albo
     nieztypowany payload z pliku konfiguracyjnego;
   - stopniowo migrowany kod legacy, jeśli obok użycia istnieje zawężenie typu,
     walidacja lub komentarz wyjaśniający powód.
4. Jeżeli potrzebujesz typu elastycznego, najpierw rozważ `object`, `Protocol`,
   `TypedDict`, `Mapping[str, object]`, `Sequence[...]`, `Callable[...]` albo
   typ domenowy zamiast `Any`.
5. Nie dodawaj pustych, zastępczych docstringów typu „Opis funkcji”. Docstring
   ma wyjaśniać znaczenie obliczeniowe lub metodologiczne, a nie tylko
   powtarzać nazwę funkcji.
6. Nie dodawaj nowych globalnych ignorowań `D`, `type: ignore`, `# noqa` ani
   wyłączeń testów bez uzasadnienia w komentarzu lub dokumentacji migracyjnej.
7. W plikach z `scripts` i `analysis` traktuj istniejące wyjątki `D*` jako limit
   długu legacy: nowe lub istotnie zmieniane funkcje powinny otrzymać kompletne
   docstringi zamiast polegać na per-file-ignore.

### 8.3 Po edycji

Uruchom najwęższy zestaw kontroli, który pokrywa zmianę, a przy zmianach
polityki jakości także pełną kontrolę lintingu:

```bash
python -m ruff check .
python -m mypy --follow-imports=silent brain_model/oscillators.py brain_model/calibration.py brain_model/validation.py brain_model/plotting.py
python -m pytest tests/test_quality_policy_static.py
```

Dla zmian w logice naukowej uruchom dodatkowo testy domenowe dla zmienionego
modułu, np. `tests/test_oscillators.py`, `tests/test_calibration.py` albo testy
walidacji i raportowania. Jeśli testu nie da się uruchomić z powodu środowiska,
opisz konkretną przyczynę w PR.

### 8.4 Kryteria akceptacji PR

PR dotyczący jakości statycznej jest gotowy dopiero wtedy, gdy:

- nie przywraca globalnego ignorowania `D` dla kodu produkcyjnego;
- nie dodaje nieuzasadnionego `Any` w modułach naukowych;
- nie zawiera masowego formatowania niezwiązanego z zadaniem;
- dokumentuje nowe wyjątki migracyjne, jeśli są konieczne;
- zawiera wynik komend weryfikacyjnych w opisie PR;
- zmienione funkcje mają kompletne type hints i docstringi zgodne z polityką
  językową projektu.
