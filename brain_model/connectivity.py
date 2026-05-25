import numpy as np


def build_connectivity(names):
    """
    Buduje macierz połączeń funkcjonalnych między modułami poznawczymi.

    W[target, source] oznacza wpływ aktywności modułu source
    na moduł target.
    """
    idx = {name: i for i, name in enumerate(names)}
    n = len(names)
    W = np.zeros((n, n))

    def c(target, source, weight):
        W[idx[target], idx[source]] = weight

    # Sensoryka -> salience / uwaga
    c("SAL", "VIS", 0.55)
    c("SAL", "AUD", 0.50)
    c("SAL", "INT", 0.45)

    c("ATT", "SAL", 0.65)
    c("ATT", "EXEC", 0.35)
    c("ATT", "GW", 0.30)

    # Podsystemy pamięci roboczej
    c("PHON", "AUD", 0.55)
    c("PHON", "LANG", 0.45)
    c("VSWM", "VIS", 0.60)
    c("VSWM", "ATT", 0.40)

    # Kontrola wykonawcza
    c("EXEC", "ATT", 0.45)
    c("EXEC", "PHON", 0.25)
    c("EXEC", "VSWM", 0.25)
    c("EXEC", "SAL", 0.35)
    c("EXEC", "DMN", -0.25)

    # Bufor epizodyczny i hipokamp
    c("EPIS", "PHON", 0.30)
    c("EPIS", "VSWM", 0.30)
    c("EPIS", "SEM", 0.25)
    c("EPIS", "HIP", 0.35)
    c("HIP", "EPIS", 0.45)
    c("HIP", "ATT", 0.25)

    # Pamięć semantyczna i język
    c("SEM", "LANG", 0.35)
    c("LANG", "AUD", 0.40)
    c("LANG", "PHON", 0.35)
    c("LANG", "SEM", 0.30)

    # Wartościowanie i działanie
    c("VAL", "SAL", 0.30)
    c("VAL", "HIP", 0.25)
    c("MOT", "EXEC", 0.45)
    c("MOT", "VAL", 0.35)
    c("MOT", "SAL", 0.20)

    # Default mode network: konkurencja z kontrolą zadaniową
    c("DMN", "SEM", 0.25)
    c("DMN", "HIP", 0.25)
    c("DMN", "EXEC", -0.35)
    c("EXEC", "DMN", -0.30)

    # Global workspace broadcast
    for module in ["ATT", "EXEC", "EPIS", "SEM", "HIP", "LANG", "MOT"]:
        c(module, "GW", 0.35)

    c("GW", "ATT", 0.40)
    c("GW", "EXEC", 0.45)
    c("GW", "EPIS", 0.35)
    c("GW", "SAL", 0.25)

    return W
