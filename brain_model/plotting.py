import matplotlib.pyplot as plt


def plot_activity(time, activity, names, idx):
    selected = [
        "VIS", "AUD", "SAL", "ATT", "PHON", "VSWM",
        "EXEC", "EPIS", "SEM", "HIP", "VAL", "MOT", "DMN", "GW"
    ]

    plt.figure(figsize=(14, 8))
    for name in selected:
        plt.plot(time, activity[:, idx[name]], label=name)

    plt.xlabel("Czas symulacji [s]")
    plt.ylabel("Aktywacja modułu [0-1]")
    plt.title("Mezoskopowa dynamika procesów poznawczych")
    plt.legend(ncol=4, fontsize=9)
    plt.tight_layout()
    plt.show()


def plot_diagnostics(time, diagnostics):
    plt.figure(figsize=(14, 4))
    plt.plot(time, diagnostics["prediction_error"], label="błąd predykcji")
    plt.plot(time, diagnostics["gw_ignition"], label="global workspace ignition")
    plt.plot(time, diagnostics["dopamine_delta"], label="błąd predykcji nagrody")
    plt.plot(time, diagnostics["noradrenaline"], label="noradrenalina")
    plt.plot(time, diagnostics["acetylcholine"], label="acetylocholina")

    plt.xlabel("Czas symulacji [s]")
    plt.ylabel("Wartość")
    plt.title("Zmienne obliczeniowe i neuromodulacyjne")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_eeg_modules(time, oscillations, names, idx):
    """Rysuje przykładowe sygnały EEG typu E-I dla wybranych modułów."""
    selected = ["HIP", "VSWM", "VIS", "AUD", "EXEC", "ATT", "SEM", "GW"]
    eeg = oscillations["eeg"]

    plt.figure(figsize=(14, 6))
    for name in selected:
        plt.plot(time, eeg[:, idx[name]], label=f"{name}")

    plt.xlabel("Czas symulacji [s]")
    plt.ylabel("Sygnał EEG aproksymowany jako E-I")
    plt.title("Oscylatory Wilsona-Cowana dla wybranych modułów")
    plt.legend(ncol=4, fontsize=9)
    plt.tight_layout()
    plt.show()


def plot_band_power(time, oscillations):
    """Rysuje chwilową moc pasm theta, alpha, beta i gamma."""
    band_power = oscillations["band_power"]

    plt.figure(figsize=(14, 4))
    for band in ["theta", "alpha", "beta", "gamma"]:
        plt.plot(time, band_power[band], label=band)

    plt.xlabel("Czas symulacji [s]")
    plt.ylabel("Uproszczona moc pasmowa")
    plt.title("Symulowana dynamika pasm EEG")
    plt.legend()
    plt.tight_layout()
    plt.show()
