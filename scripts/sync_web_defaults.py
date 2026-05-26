from __future__ import annotations
import ast, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_dataclass_defaults(path: Path, class_name: str):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.value is not None:
                    try:
                        out[item.target.id] = ast.literal_eval(item.value)
                    except Exception:
                        pass
    return out


def read_param_desc(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'PARAMETER_DESCRIPTIONS':
                    return ast.literal_eval(node.value)
    return {}

brain = read_dataclass_defaults(ROOT/'brain_model'/'params.py', 'BrainParams')
osc = read_dataclass_defaults(ROOT/'brain_model'/'oscillators.py', 'WilsonCowanParams')
desc = read_param_desc(ROOT/'brain_model'/'gui.py')

payload = {
    'simulation': {'T': 45.0, 'seed': 7},
    'brain': {k: brain[k] for k in ['dt','noise','gw_threshold','gw_gain','learning_rate_semantic','learning_rate_value','decay_semantic','enable_oscillators'] if k in brain},
    'osc': {k: osc[k] for k in ['w_ee','w_ei','w_ie','w_ii','baseline_e','baseline_i','cognitive_drive_gain','coupling_gain','oscillator_noise','phase_drive_gain'] if k in osc},
    'descriptions': {k: desc[k] for k in ['T','seed','dt','noise','gw_threshold','gw_gain','learning_rate_semantic','learning_rate_value','decay_semantic','enable_oscillators','w_ee','w_ei','w_ie','w_ii','baseline_e','baseline_i','cognitive_drive_gain','coupling_gain','oscillator_noise','phase_drive_gain'] if k in desc}
}

out = ROOT/'docs'/'gui_defaults.json'
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Wrote', out)
