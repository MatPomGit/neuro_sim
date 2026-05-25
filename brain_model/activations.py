import numpy as np


def sigmoid(z, beta=4.0):
    """
    Funkcja aktywacji populacyjnej.

    W modelu oznacza nieliniowe przejście od pobudzenia wejściowego
    do średniej aktywacji modułu poznawczego.
    """
    return 1.0 / (1.0 + np.exp(-beta * z))
