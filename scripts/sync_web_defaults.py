from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def read_dataclass_defaults(path: Path, class_name: str) -> Any:
    """Odczytaj literalne wartości domyślne pól dataclass z pliku Pythona.

    Parameters
    ----------
    path:
        Ścieżka do modułu zawierającego definicję klasy.
    class_name:
        Nazwa klasy, której adnotowane przypisania pól mają zostać odczytane.

    Returns
    -------
    dict[str, object]
        Płaski słownik ``{nazwa_pola: wartość_domyslna}``. Klucz jest nazwą
        adnotowanego pola klasy, a wartość jest wynikiem ``ast.literal_eval``:
        liczbą, napisem, wartością logiczną, ``None`` albo zagnieżdżoną strukturą
        literalną obsługiwaną przez AST.

    Notes
    -----
    Nieobsługiwane wartości AST, np. wywołania funkcji, referencje do stałych,
    wyrażenia arytmetyczne lub wartości zależne od kontekstu wykonania, są
    pomijane bez przerywania synchronizacji. Dzięki temu skrypt synchronizuje
    tylko bezpiecznie odczytywalne domyślne literały i nie importuje modułu z
    potencjalnymi efektami ubocznymi.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if (
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and item.value is not None
                ):
                    try:
                        out[item.target.id] = ast.literal_eval(item.value)
                    except (ValueError, TypeError):
                        pass
    return out


def read_param_desc(path: Path) -> Any:
    """Odczytaj słownik opisów parametrów z przypisania AST.

    Parameters
    ----------
    path:
        Ścieżka do modułu, w którym szukana jest stała
        ``PARAMETER_DESCRIPTIONS``.

    Returns
    -------
    dict[str, str]
        Płaski słownik ``{nazwa_parametru: polski_opis}`` z literalnej wartości
        stałej ``PARAMETER_DESCRIPTIONS`` albo pusty słownik, gdy stała nie
        występuje. Klucze odpowiadają technicznym nazwom parametrów, a wartości
        są polskimi opisami prezentowanymi w warstwie web/GUI.

    Raises
    ------
    ValueError
        Może zostać zgłoszony przez ``ast.literal_eval``, jeśli znaleziona stała
        zawiera nieobsługiwaną wartość AST, np. wywołanie funkcji albo referencję
        do nazwy zamiast literalnego słownika. W odróżnieniu od domyślnych pól
        dataclass taki błąd nie jest pomijany, bo opisy parametrów powinny być
        w pełni literalne i walidowalne.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "PARAMETER_DESCRIPTIONS":
                    return ast.literal_eval(node.value)
    return {}


brain = read_dataclass_defaults(ROOT / "brain_model" / "params.py", "BrainParams")
osc = read_dataclass_defaults(
    ROOT / "brain_model" / "oscillators.py", "WilsonCowanParams"
)
desc = read_param_desc(ROOT / "brain_model" / "gui.py")

payload = {
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

out = ROOT / "docs" / "gui_defaults.json"
out.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("Wrote", out)
