# Plan wdrożenia: docstringi i type hinty (A–E)

## Cel

Wdrożyć uzupełnienia docstringów i adnotacji typów sekwencyjnie, małymi partiami, bez refaktoryzacji „przy okazji”.

## Zasady wykonania (wspólne dla wszystkich partii)

1. Zakres zmian ograniczony wyłącznie do:
   - dopisania docstringów,
   - dopisania type hintów,
   - minimalnych korekt sygnatur koniecznych do poprawnego typowania.
2. Bez zmian logiki biznesowej i bez zmian architektury.
3. Bez masowego formatowania niezwiązanego z zadaniem.
4. Każda partia kończy się osobnym PR.

## Partia A — moduły domenowe (`brain_core`)

### Zakres
- Wszystkie moduły pod `brain_core/`.
- Priorytet: elementy wskazane w `docs/typing_docstring_audit.md` dla `brain_core`.

### Lista plików
- `brain_core/analysis/*.py`
- `brain_core/anatomy/*.py`
- `brain_core/cognition/*.py`
- `brain_core/experiments/*.py`
- `brain_core/networks/*.py`
- `brain_core/physiology/*.py`
- `brain_core/populations/*.py`
- `brain_core/simulation/*.py`
- `brain_core/synapses/*.py`
- `brain_core/__init__.py` i `__init__.py` w podmodułach (jeśli wymagane)

### PR
- Tytuł: `Partia A: docstringi i type hinty w brain_core`
- Opis:
  - Co: uzupełnienie docstringów/type hintów w warstwie domenowej.
  - Dlaczego: poprawa czytelności i testowalności bez zmiany logiki.
  - Weryfikacja: uruchomione testy dla `brain_core` i mypy/pyright (jeśli używane).

## Partia B — model/symulacja (`brain_model`)

### Zakres
- Wszystkie moduły pod `brain_model/`.
- Obejmuje także `brain_model/scenarios/`.

### Lista plików
- `brain_model/*.py`
- `brain_model/scenarios/*.py`

### PR
- Tytuł: `Partia B: docstringi i type hinty w brain_model`
- Opis analogiczny do Partii A.

## Partia C — konfiguracja i I/O

### Zakres
- Moduły odpowiedzialne za konfigurację, walidację, ładowanie i zapis danych.

### Lista plików
- `brain_core/simulation/config_loader.py`
- `brain_core/simulation/config_schema.py`
- `brain_model/io.py`
- `brain_model/validation.py`
- `analysis/reports.py` (katalog najwyższego poziomu; nie `brain_core/analysis/reports.py`)
- Pliki wejściowe/launcherowe, jeśli zawierają funkcje Python wymagające uzupełnień:
  - `main.py`, `main_gui.py`, `run_gui.py`, `brain_model.py`

### PR
- Tytuł: `Partia C: docstringi i type hinty w konfiguracji oraz I/O`

## Partia D — narzędzia pomocnicze i skrypty

### Zakres
- Skrypty i moduły narzędziowe poza głównym silnikiem.

### Lista plików
- `scripts/sync_web_defaults.py`
- `brain_viewer/mapping.py`

### PR
- Tytuł: `Partia D: docstringi i type hinty w narzędziach i skryptach`

## Partia E — testy

### Zakres
- Wyłącznie pliki testowe w `tests/`.
- Uzupełnienia typu: adnotacje helperów testowych oraz docstringi tam, gdzie zwiększają czytelność scenariusza.

### Lista plików
- `tests/*.py`

### PR
- Tytuł: `Partia E: docstringi i type hinty w testach`

## Kolejność i kryteria przejścia

1. A → B → C → D → E.
2. Kolejna partia startuje dopiero po:
   - zielonych testach adekwatnych do zmienionego obszaru,
   - potwierdzeniu braku zmian logiki (przegląd diffu),
   - zamknięciu poprzedniego PR.

## Minimalny zestaw weryfikacji per partia

- Testy celowane dla zmienionych modułów.
- Pełny `pytest` po Partii E.
- Kontrola, że diff nie zawiera zmian funkcjonalnych poza sygnaturami.
