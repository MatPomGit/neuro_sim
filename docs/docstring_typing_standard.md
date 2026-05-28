# Standard docstringów i adnotacji typów

## 1. Wybrany styl

W projekcie `neuro_sim` obowiązuje styl **Google** dla docstringów.

Powód wyboru:
- jest czytelny przy krótkich i średnich funkcjach,
- dobrze wspiera sekcje `Args`, `Returns`, `Raises`,
- jest szeroko wspierany przez narzędzia lintujące i generatory dokumentacji.

## 2. Minimalne wymagania

### 2.1 Każda funkcja i metoda
Każda funkcja/metoda musi zawierać docstring opisujący:
- **cel** (co robi i w jakim kontekście domenowym),
- **parametry** (`Args`),
- **zwracaną wartość** (`Returns`),
- **wyjątki** (`Raises`) — jeśli funkcja może je zgłosić.

Jeśli funkcja nic nie zwraca (zwraca None), sekcja Returns nie jest wymagana, chyba że opisuje istotny efekt uboczny.

### 2.2 Każda klasa
Każda klasa musi zawierać docstring z:
- opisem **odpowiedzialności klasy**,
- opisem **kluczowych atrybutów** (sekcja `Attributes`),
- opcjonalnie opisem ważnych założeń użycia.

### 2.3 Publiczne API i type hinty
Każda publiczna funkcja (oraz metoda publiczna) musi mieć pełne type hinty:
- wszystkie parametry,
- typ zwracany,
- typy generyczne doprecyzowane (np. `list[str]`, nie samo `list`).

## 3. Przypadki specjalne

### 3.1 `Optional`, `Union` i typy generyczne
- Stosuj jawne typy, np. `str | None` (Python 3.10+) lub `Optional[str]` tam, gdzie to konieczne dla kompatybilności.
- Dla alternatyw używaj `A | B` lub `Union[A, B]` konsekwentnie w obrębie modułu.
- Dla kolekcji zawsze podawaj typy elementów: `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T1, T2]`.
- W docstringu doprecyzuj semantykę wartości `None` (np. „brak filtra”, „użyj wartości domyślnej”).

### 3.2 `Protocol`, `TypedDict`, `dataclass`
- **Protocol**: dokumentuj wymagany kontrakt zachowania (metody, własności, oczekiwania domenowe).
- **TypedDict**: dokumentuj znaczenie pól, wymagane/opcjonalne klucze i jednostki wartości, jeśli dotyczy.
- **dataclass**: dokumentuj rolę modelu danych oraz znaczenie pól; gdy jest walidacja w `__post_init__`, opisz możliwe wyjątki.

### 3.3 Funkcje asynchroniczne i generatory
- **`async def`**: w `Returns` opisuj finalny typ wyniku po `await`.
- Jeśli asynchroniczna funkcja może anulować operację lub propagować wyjątki I/O, opisz to w `Raises`.
- **Generatory** (`Generator`/`Iterator`/`AsyncIterator`): opisz, co jest emitowane, w jakiej kolejności i kiedy kończy się iteracja.

## 4. Zasady językowe

- Komentarze i docstringi piszemy **po polsku**.
- Identyfikatory techniczne (nazwy zmiennych, funkcji, klas, modułów, plików i API) pozostają **po angielsku**.
- Jeżeli nazwa techniczna jest prezentowana użytkownikowi, stosujemy mapowanie EN→PL zgodnie z `docs/english_polish_glossary.md`.

## 5. Skrócony szablon docstringa (Google)

```python
def example_function(data: list[str], limit: int | None = None) -> dict[str, int]:
    """Buduje mapę częstości wystąpień tokenów.

    Args:
        data: Lista tokenów wejściowych.
        limit: Maksymalna liczba elementów wyniku; `None` oznacza brak limitu.

    Returns:
        Mapa token -> liczba wystąpień.

    Raises:
        ValueError: Gdy `limit` jest mniejsze od zera.
    """
```
