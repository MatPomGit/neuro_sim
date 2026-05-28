# Raport postępu: type hinty i docstringi

## Stan bazowy (2026-05-28)

Źródło metryk: lokalny skan AST wszystkich plików `*.py` w repozytorium.

- Łączna liczba plików Python: **86**.
- Pokrycie funkcji pełnymi type hintami (parametry + typ zwracany): **49.83%** (145/291).
- Pokrycie klas docstringami: **59.21%** (45/76).
- Pokrycie metod docstringami: **33.56%** (50/149).
- Pokrycie klas i metod docstringami łącznie: **42.22%** (95/225).

## Wielkość partii (liczba plików do zamknięcia)

- **Partia A (`brain_core`)**: 49 plików.
- **Partia B (`brain_model`)**: 19 plików.
- **Partia C (konfiguracja i I/O)**: 9 pozycji zadaniowych, w tym 5 plików poza partiami A/B.
- **Partia D (narzędzia i skrypty)**: 2 pliki.
- **Partia E (testy)**: 11 plików.

Uwaga: partie A–E obejmują łącznie **86 unikalnych** plików Python. Prosta suma
liczebności partii daje 90, ponieważ Partia C celowo powtarza 4 pliki
ujęte już w Partiach A/B (`brain_core/simulation/config_loader.py`,
`brain_core/simulation/config_schema.py`, `brain_model/io.py`,
`brain_model/validation.py`) jako przekrojowy zakres konfiguracji i I/O.

## Plan iteracji tygodniowych

> Cel końcowy projektu: wszystkie pliki `*.py` spełniają wymaganie MUST (docstringi + type hinty dla funkcji i klas istniejących oraz nowych).

| Iteracja | Daty (czwartek–środa) | Zakres | Cel ilościowy | Właściciel |
|---|---|---|---|---|
| I1 | 2026-05-28 → 2026-06-03 | Partia A start | Zamknięcie 16/49 plików `brain_core`; +15 pp pokrycia metod docstringami w `brain_core` | Codex (brain_core: analysis/anatomy/cognition) |
| I2 | 2026-06-04 → 2026-06-10 | Partia A kontynuacja | Zamknięcie 17/49 plików `brain_core`; +15 pp pokrycia funkcji type hintami w `brain_core` | Codex (brain_core: experiments/networks/physiology) |
| I3 | 2026-06-11 → 2026-06-17 | Partia A domknięcie + B start | Zamknięcie ostatnich 16/49 plików `brain_core` i 6/19 plików `brain_model` | Codex (brain_core: populations/simulation/synapses) + Tomasz (brain_model: core) |
| I4 | 2026-06-18 → 2026-06-24 | Partia B | Zamknięcie 7/19 plików `brain_model`; pokrycie funkcji type hintami globalnie min. 75% | Tomasz (brain_model: GUI/model/io) |
| I5 | 2026-06-25 → 2026-07-01 | Partia B + C start | Zamknięcie 6/19 plików `brain_model` i 4/9 plików partii C | Ewa (brain_model: scenarios/report) + Codex (config/I/O) |
| I6 | 2026-07-02 → 2026-07-08 | Partie C + D | Zamknięcie 5/9 plików partii C i 2/2 plików partii D | Codex (config/I/O) + Olga (tools/scripts) |
| I7 | 2026-07-09 → 2026-07-15 | Partia E start | Zamknięcie 6/11 plików testowych; pokrycie klas+metod docstringami globalnie min. 90% | Codex (tests A–M) |
| I8 | 2026-07-16 → 2026-07-22 | Partia E domknięcie + finalizacja | Zamknięcie 5/11 plików testowych; osiągnięcie 100% MUST dla całego repo | Codex (tests N–Z) + Lead: Codex |

## Przypisanie właścicieli obszarów (moduł/plik) i terminy

- `brain_core/analysis`, `brain_core/anatomy`, `brain_core/cognition` — **Codex**, termin: **2026-06-03**.
- `brain_core/experiments`, `brain_core/networks`, `brain_core/physiology` — **Codex**, termin: **2026-06-10**.
- `brain_core/populations`, `brain_core/simulation`, `brain_core/synapses` — **Codex**, termin: **2026-06-17**.
- `brain_model/model.py`, `brain_model/modules.py`, `brain_model/behavior.py`, `brain_model/gui.py` — **Tomasz**, termin: **2026-06-24**.
- `brain_model/scenarios/*`, `brain_model/report.py`, `brain_model/plotting.py` — **Ewa**, termin: **2026-07-01**.
- `brain_core/simulation/config_loader.py`, `brain_core/simulation/config_schema.py`,
  `brain_model/io.py`, `brain_model/validation.py`,
  `analysis/reports.py` (katalog najwyższego poziomu; nie `brain_core/analysis/reports.py`),
  `main.py`, `main_gui.py`, `run_gui.py`, `brain_model.py` — **Codex**, termin: **2026-07-08**.
- `scripts/sync_web_defaults.py`, `brain_viewer/mapping.py` — **Olga**, termin: **2026-07-08**.
- `tests/*.py` — **Codex**, termin: **2026-07-22**.

## Aktualizacja raportu po każdej iteracji

Po zakończeniu każdej iteracji należy uzupełnić sekcję poniżej:

- data zamknięcia iteracji,
- liczba zamkniętych plików / plan,
- zaktualizowane metryki (% type hintów, % docstringów klas i metod),
- lista zablokowanych plików i ryzyk,
- decyzja: kontynuacja / korekta planu.

### Dziennik iteracji

#### Iteracja I1 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-06-03_.

#### Iteracja I2 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-06-10_.

#### Iteracja I3 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-06-17_.

#### Iteracja I4 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-06-24_.

#### Iteracja I5 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-07-01_.

#### Iteracja I6 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-07-08_.

#### Iteracja I7 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-07-15_.

#### Iteracja I8 (planowana)
- Status: planowana.
- Wynik: _do uzupełnienia po 2026-07-22_.

- [x] brain_core/cognition — docstringi i type hinty uzupełnione (2026-05-28)
- [x] brain_core/experiments — docstringi i type hinty uzupełnione (2026-05-28)
- [x] brain_core/networks — docstringi i type hinty uzupełnione (2026-05-28)
- [x] brain_core/physiology — docstringi i type hinty uzupełnione (2026-05-28)
- [x] brain_core/populations — docstringi i type hinty uzupełnione (2026-05-28)
