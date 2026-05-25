# Cognitive Brain Model

Mezoskopowy model dynamiki procesów poznawczych w Pythonie.

Model nie symuluje pojedynczych neuronów. Reprezentuje aktywność modułów poznawczych oraz sprzężone oscylatory Wilsona-Cowana dla pasm EEG.

## Moduły poznawcze

- przetwarzanie wzrokowe i słuchowe,
- interocepcja,
- salience network,
- uwaga,
- pamięć robocza,
- pamięć semantyczna i epizodyczna,
- hipokampalne wiązanie epizodów,
- wartościowanie,
- planowanie działania,
- default mode network,
- global workspace.

## Oscylatory Wilsona-Cowana

Każdy moduł poznawczy ma osobny oscylator Wilsona-Cowana z populacją pobudzającą `E` i hamującą `I`.
Sygnał EEG jest aproksymowany jako:

```text
EEG_module(t) = E_module(t) - I_module(t)
```

Domyślne przypisanie pasm:

- `theta`: HIP, EPIS, PHON, VSWM,
- `alpha`: VIS, AUD, INT, DMN,
- `beta`: EXEC, ATT, SAL, MOT, LANG,
- `gamma`: SEM, VAL, GW.

Interpretacja:

- theta: hipokamp, bufor epizodyczny i pamięć robocza,
- alpha: hamowanie i bramkowanie sensoryczne,
- beta: kontrola wykonawcza i utrzymanie nastawienia zadaniowego,
- gamma: lokalne wiązanie cech i reprezentacji.

## Instalacja

```bash
pip install numpy matplotlib
```

## Uruchomienie

```bash
python main.py
```

## Struktura

```text
cognitive_brain_model/
├── main.py
├── brain_model/
│   ├── __init__.py
│   ├── params.py
│   ├── activations.py
│   ├── modules.py
│   ├── connectivity.py
│   ├── stimuli.py
│   ├── oscillators.py
│   ├── model.py
│   └── plotting.py
└── README.md
```

## Wyniki symulacji

`model.simulate()` zwraca:

```python
time, activity, diagnostics, oscillations = model.simulate(T=45.0)
```

- `activity`: aktywacje modułów poznawczych,
- `diagnostics`: błąd predykcji, neuromodulacja, global workspace,
- `oscillations["eeg"]`: sygnały E-I dla modułów,
- `oscillations["band_power"]`: chwilowa moc theta/alpha/beta/gamma.
