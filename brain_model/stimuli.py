def experimental_stimulus(t):
    """
    Scenariusz eksperymentalny:
    1. bodziec wzrokowy,
    2. bodziec słuchowo-językowy,
    3. bodziec zagrażający,
    4. sygnał nagrody.

    Zwraca słownik wejść zewnętrznych w chwili t.
    """
    u = {
        "visual": 0.0,
        "auditory": 0.0,
        "interoceptive": 0.15,
        "task_cue": 0.0,
        "threat": 0.0,
        "reward": 0.0,
    }

    if 2.0 < t < 18.0:
        u["visual"] = 0.9

    if 8.0 < t < 24.0:
        u["auditory"] = 0.75

    if 1.0 < t < 35.0:
        u["task_cue"] = 0.65

    if 22.0 < t < 30.0:
        u["threat"] = 0.85
        u["interoceptive"] = 0.55

    if 34.0 < t < 38.0:
        u["reward"] = 1.0

    return u
