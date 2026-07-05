"""Synchronizacja domyślnych parametrów aplikacji webowej z konfiguracją Pythona."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_dataclass_defaults(path: Path, class_name: str) -> dict[str, object]:
    """Odczytaj literalne wartości domyślne pól dataclass z pliku Pythona.

    Parameters
    ----------
    path:
        Ścieżka do modułu zawierającego definicję klasy.
    class_name:
        Nazwa klasy, której adnotowane przypisania pól mają zostać odczytane.

    Returns:
    -------
    dict[str, object]
        Płaski słownik ``{nazwa_pola: wartość_domyslna}``. Klucz jest nazwą
        adnotowanego pola klasy, a wartość jest wynikiem ``ast.literal_eval``:
        liczbą, napisem, wartością logiczną, ``None`` albo zagnieżdżoną strukturą
        literalną obsługiwaną przez AST.

    Raises:
    ------
    ValueError
        Gdy wskazana klasa nie istnieje albo co najmniej jedno pole ma wartość,
        której nie da się odczytać statycznie jako literału lub obsługiwanego
        wywołania ``field(default_factory=lambda: Constructor(...))``.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return _read_defaults_from_class(path=path, class_node=node)

    raise ValueError(f"Nie znaleziono klasy {class_name!r} w pliku {path}.")


def _read_defaults_from_class(
    path: Path, class_node: ast.ClassDef
) -> dict[str, object]:
    """Odczytaj wartości domyślne z węzła klasy i zgłoś pola nieobsługiwane.

    Parameters
    ----------
    path:
        Ścieżka do analizowanego pliku, używana w komunikatach błędów.
    class_node:
        Węzeł AST klasy dataclass.

    Returns:
    -------
    dict[str, object]
        Słownik wartości domyślnych możliwych do odczytania statycznie.

    Raises:
    ------
    ValueError
        Gdy co najmniej jedno pole ma wartość spoza zakresu ``ast.literal_eval``.
    """
    defaults: dict[str, object] = {}
    unsupported_fields: list[str] = []

    for item in class_node.body:
        if (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and item.value is not None
        ):
            field_name = item.target.id
            try:
                defaults[field_name] = _read_supported_default_value(item.value)
            except (ValueError, TypeError):
                unsupported_fields.append(field_name)

    if unsupported_fields:
        fields = ", ".join(unsupported_fields)
        raise ValueError(
            "Nie można statycznie odczytać wartości domyślnych pól "
            f"w pliku {path}, klasa {class_node.name}: {fields}."
        )

    return defaults


def _read_supported_default_value(node: ast.expr) -> object:
    """Odczytaj udokumentowany statyczny zapis wartości domyślnej pola.

    Parameters
    ----------
    node:
        Wyrażenie AST przypisane jako domyślna wartość pola dataclass.

    Returns:
    -------
    object
        Wartość literalna albo jawny opis ``field(default_factory=lambda: ...)``
        używany dla zagnieżdżonych konfiguracji dataclass.

    Raises:
    ------
    ValueError, TypeError
        Gdy wyrażenie nie jest literałem ani obsługiwanym wywołaniem
        ``dataclasses.field`` z bezargumentową fabryką lambda.
    """
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "field":
                return _read_field_default_factory(node)
            return _read_constructor_call(node)
        raise


def _read_field_default_factory(node: ast.expr) -> dict[str, object]:
    """Odczytaj jawny opis fabryki ``field(default_factory=lambda: ...)``.

    Parameters
    ----------
    node:
        Wyrażenie AST potencjalnego wywołania ``field``.

    Returns:
    -------
    dict[str, object]
        Słownik z nazwą fabryki i literalnymi argumentami kluczowymi.

    Raises:
    ------
    ValueError
        Gdy wyrażenie nie ma obsługiwanego, statycznego kształtu.
    TypeError
        Gdy argumenty fabryki nie są literalne.
    """
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise ValueError("Domyślna wartość pola nie jest obsługiwanym wywołaniem.")
    if node.func.id != "field":
        raise ValueError("Obsługiwane jest tylko wywołanie field(...).")

    default_factory = None
    for keyword in node.keywords:
        if keyword.arg == "default_factory":
            default_factory = keyword.value
            break

    if not isinstance(default_factory, ast.Lambda) or default_factory.args.args:
        raise ValueError("default_factory musi być bezargumentową funkcją lambda.")
    if not isinstance(default_factory.body, ast.Call):
        raise ValueError("default_factory musi zwracać wywołanie konstruktora.")

    factory_call = default_factory.body
    constructor = _read_constructor_call(factory_call)
    constructor["default_factory"] = constructor.pop("constructor")
    return constructor


def _read_constructor_call(node: ast.Call) -> dict[str, object]:
    """Odczytaj statyczny opis nazwanego konstruktora z argumentami literalnymi.

    Parameters
    ----------
    node:
        Wywołanie AST konstruktora konfiguracji.

    Returns:
    -------
    dict[str, object]
        Nazwa konstruktora oraz słownik literalnych argumentów kluczowych.

    Raises:
    ------
    ValueError
        Gdy konstruktor nie jest nazwą albo używa argumentów pozycyjnych.
    TypeError
        Gdy argumenty konstruktora nie są literalne lub obsługiwane statycznie.
    """
    if not isinstance(node.func, ast.Name) or node.args:
        raise ValueError("Konstruktor musi być nazwany i bez argumentów pozycyjnych.")

    kwargs = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            raise ValueError(
                "Rozpakowywanie słownika (**kwargs) nie jest obsługiwane statycznie."
            )
        kwargs[keyword.arg] = _read_supported_default_value(keyword.value)

    return {
        "constructor": node.func.id,
        "kwargs": kwargs,
    }


def read_param_desc(path: Path) -> dict[str, str]:
    """Odczytaj słownik opisów parametrów z przypisania AST.

    Parameters
    ----------
    path:
        Ścieżka do modułu, w którym szukana jest stała
        ``PARAMETER_DESCRIPTIONS``.

    Returns:
    -------
    dict[str, str]
        Płaski słownik ``{nazwa_parametru: polski_opis}`` z literalnej wartości
        stałej ``PARAMETER_DESCRIPTIONS`` albo pusty słownik, gdy stała nie
        występuje. Klucze odpowiadają technicznym nazwom parametrów, a wartości
        są polskimi opisami prezentowanymi w warstwie web/GUI.

    Raises:
    ------
    ValueError
        Może zostać zgłoszony przez ``ast.literal_eval``, jeśli znaleziona stała
        zawiera nieobsługiwaną wartość AST, np. wywołanie funkcji albo referencję
        do nazwy zamiast literalnego słownika. W odróżnieniu od domyślnych pól
        dataclass taki błąd nie jest pomijany, bo opisy parametrów powinny być
        w pełni literalne i walidowalne.
    TypeError
        Gdy ``PARAMETER_DESCRIPTIONS`` nie jest słownikiem albo zawiera wartość
        niezgodną z oczekiwanym typem zwracanym.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "PARAMETER_DESCRIPTIONS":
                    descriptions = ast.literal_eval(node.value)
                    if not isinstance(descriptions, dict):
                        raise TypeError("PARAMETER_DESCRIPTIONS musi być słownikiem.")
                    return descriptions
    return {}


def build_payload() -> dict[str, object]:
    """Zbuduj dane domyślne GUI na podstawie statycznej analizy modułów."""
    brain = read_dataclass_defaults(ROOT / "brain_model" / "params.py", "BrainParams")
    osc = read_dataclass_defaults(
        ROOT / "brain_model" / "oscillators.py", "WilsonCowanParams"
    )
    desc = read_param_desc(ROOT / "brain_model" / "gui.py")

    return {
        "simulation": {"T": 45.0, "seed": 7},
        "brain": {
            k: brain[k]
            for k in [
                "dt",
                "noise",
                "gw_threshold",
                "gw_gain",
                "learning_rate_semantic",
                "learning_rate_value",
                "decay_semantic",
                "enable_oscillators",
                "decision_threshold",
                "confidence_gain",
            ]
            if k in brain
        },
        "osc": {
            k: osc[k]
            for k in [
                "w_ee",
                "w_ei",
                "w_ie",
                "w_ii",
                "baseline_e",
                "baseline_i",
                "cognitive_drive_gain",
                "coupling_gain",
                "oscillator_noise",
                "phase_drive_gain",
            ]
            if k in osc
        },
        "descriptions": {
            k: desc[k]
            for k in [
                "T",
                "seed",
                "dt",
                "noise",
                "gw_threshold",
                "gw_gain",
                "learning_rate_semantic",
                "learning_rate_value",
                "decay_semantic",
                "enable_oscillators",
                "decision_threshold",
                "confidence_gain",
                "w_ee",
                "w_ei",
                "w_ie",
                "w_ii",
                "baseline_e",
                "baseline_i",
                "cognitive_drive_gain",
                "coupling_gain",
                "oscillator_noise",
                "phase_drive_gain",
            ]
            if k in desc
        },
    }


def main() -> None:
    """Zapisz plik JSON z domyślną konfiguracją GUI."""
    out = ROOT / "docs" / "gui_defaults.json"
    out.write_text(
        json.dumps(build_payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote", out)


if __name__ == "__main__":
    main()
