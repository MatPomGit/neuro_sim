import ast
from pathlib import Path

import numpy as np

from brain_model.oscillators import WilsonCowanOscillatorBank


def test_oscillator_bank_reproduces_state_and_trajectory_for_equal_seeds() -> None:
    """Sprawdza identyczny stan i przebieg oscylatorów dla jednakowych seedów."""
    connectivity = np.array([[0.0, 0.3], [0.2, 0.0]])
    first_bank = WilsonCowanOscillatorBank(["VIS", "EXEC"], connectivity)
    second_bank = WilsonCowanOscillatorBank(["VIS", "EXEC"], connectivity)
    first_rng = np.random.default_rng(1234)
    second_rng = np.random.default_rng(1234)

    first_state = first_bank.initial_state(first_rng)
    second_state = second_bank.initial_state(second_rng)
    assert np.array_equal(first_state, second_state)

    cognitive_activity = np.array([0.25, 0.75])
    for _ in range(10):
        first_state, first_eeg, first_power = first_bank.step(
            first_state, cognitive_activity, 0.001, first_rng
        )
        second_state, second_eeg, second_power = second_bank.step(
            second_state, cognitive_activity, 0.001, second_rng
        )

        assert np.array_equal(first_state, second_state)
        assert np.array_equal(first_eeg, second_eeg)
        assert first_power == second_power


def test_oscillator_bank_requires_rng_and_does_not_create_local_generator() -> None:
    """Chroni kontrakt RNG przed przywróceniem opcjonalnego lub lokalnego generatora."""
    source_path = Path("brain_model/oscillators.py")
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    oscillator_class = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "WilsonCowanOscillatorBank"
    )

    methods = {
        node.name: node
        for node in oscillator_class.body
        if isinstance(node, ast.FunctionDef)
    }
    for method_name in ("initial_state", "step"):
        method = methods[method_name]
        rng_argument = next(
            argument for argument in method.args.args if argument.arg == "rng"
        )
        assert rng_argument.annotation is not None
        assert len(method.args.defaults) < len(method.args.args) - 1

    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "default_rng"
        for node in ast.walk(oscillator_class)
    )
