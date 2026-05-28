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

