# Kontrakty danych `brain_core`: anatomia, sieci, populacje, synapsy i fizjologia

Dokument stabilizuje kontrakty danych między modułami `brain_core/anatomy`,
`brain_core/networks`, `brain_core/populations`, `brain_core/synapses` i
`brain_core/physiology`. Kontrakty są warstwą graniczną: nowe profile
neuromodulacji, opóźnienia przewodzenia oraz metryki EEG/BOLD można dodawać
dopiero wtedy, gdy zachowują poniższe jednostki, kształty, pola konfiguracji i
zasady deterministyczności.

## Wspólne założenia

- `n_regions` oznacza liczbę regionów w atlasie; kolejność regionów jest jedynym
  poprawnym indeksem dla macierzy konektomu, sieci, populacji i wektorów
  neuromodulacji.
- Wszystkie tablice numeryczne przekazywane między modułami są konwertowalne do
  `numpy.ndarray` typu `float`, chyba że kontrakt jawnie wymaga liczb
  całkowitych, np. `delays_steps`.
- Czas w konfiguracji i API jest podawany w sekundach `[s]`, częstotliwość w
  hercach `[Hz]`, a długości włókien w milimetrach `[mm]`.
- Aktywności neuronalne, EEG proxy i BOLD proxy są wielkościami syntetycznymi,
  bez kalibracji do jednostek klinicznych takich jak mikrovolty.
- Losowość musi pochodzić z `rng_seed`/`seed` konfiguracji albo jawnie
  przekazanego `numpy.random.Generator`. Brak jawnego generatora jest
  dopuszczalny tylko w ścieżkach zgodności, które nie tworzą artefaktów
  badawczych.

## Kontrakt A: `anatomy` → `networks`

Źródłem kontraktu są `RegionAtlas` i `Connectome` ładowane przez
`brain_core.anatomy.atlases`.

| Pole | Jednostka | Kształt / typ | Zakres i semantyka |
| --- | --- | --- | --- |
| `atlas.names` | — | `tuple[str, ...]`, długość `n_regions` | Niepuste, unikalne nazwy regionów w kolejności indeksowania. |
| `region.tau` | `[s]` | skalar `float` dla każdego regionu | Wartość dodatnia; domyślny atlas używa stałych czasowych regionów. |
| `connectome.region_names` | — | `tuple[str, ...]`, długość `n_regions` | Musi być identyczne z `atlas.names`. |
| `connectome.weights` | bezwymiarowa waga strukturalna | `[n_regions, n_regions]` | Wartości skończone; znak określa pobudzający lub hamujący wkład strukturalny; przekątna reprezentuje brak autopołączeń w danych domyślnych. |
| `connectome.fiber_lengths` | `[mm]` | `[n_regions, n_regions]` | Wartości nieujemne; kształt zgodny z `weights`; zero oznacza brak długości dla braku połączenia albo przekątnej. |

Wymagane pola konfiguracji:

- `connectome.atlas` — identyfikator atlasu, np. `default_regions`;
- `connectome.weights` — ścieżka do macierzy wag CSV;
- `connectome.fiber_lengths` — ścieżka do macierzy długości włókien CSV.

Deterministyczność: ładowanie atlasu i konektomu jest deterministyczne względem
zawartości plików CSV. Funkcje walidujące nie używają losowości.

## Kontrakt B: `networks` → `populations`

Warstwa `brain_core/networks` przekazuje do populacji sprzężenie strukturalne
jako wektor wejścia zewnętrznego albo macierz aktywności opóźnionej.

| Pole | Jednostka | Kształt / typ | Zakres i semantyka |
| --- | --- | --- | --- |
| `StructuralNetwork.region_names` | — | `list[str]`, długość `n_regions` | Ta sama kolejność co `atlas.names`. |
| `StructuralNetwork.connectivity` | bezwymiarowa waga strukturalna | `[n_regions, n_regions]` | Macierz wag używana w mnożeniu `connectivity @ activity`. |
| `delayed_activity` | aktywność proxy | `[n_regions]` | Aktywność regionów z poprzednich kroków symulacji. |
| `delays_steps` | liczba kroków integratora | `[n_regions, n_regions]`, `int` | Wartości całkowite nieujemne; opóźnienie `i, j` dotyczy wpływu regionu `j` na region `i`. |
| `delayed_matrix` | aktywność proxy | `[n_regions, n_regions]` | Element `i, j` zawiera aktywność regionu `j` opóźnioną dla połączenia `i ← j`. |
| `coupling` | aktywność proxy ważona | `[n_regions]` | Suma `Σ_j connectivity[i, j] * delayed_matrix[i, j]`. |

Wymagane pola konfiguracji:

- `timestep` — dodatni krok integracji `[s]`;
- `integrator.method` — metoda integracji, obecnie np. `euler`;
- pola `connectome.*` z kontraktu A;
- jeśli konfiguracja definiuje opóźnienia przewodzenia, muszą być wyrażone jako
  liczba kroków albo jednoznacznie przeliczalne z `[s]` lub `[mm]` przez
  udokumentowaną prędkość przewodzenia.

Deterministyczność: `StructuralNetwork.coupling`, `DelayBuffer.push`,
`DelayBuffer.delayed_activity_matrix` i `delayed_coupling` są deterministyczne
względem historii bufora i macierzy wejściowych.

## Kontrakt C: `populations` ↔ `synapses`

Model Wilsona-Cowana przyjmuje stan neuromodulacji jako osiem nazwanych wektorów
w kolejności regionów. Moduł `synapses` pozostaje odpowiedzialny za aktualizację
poziomów neuromodulatorów, a `populations` za ich wpływ na parametry populacji.

| Pole | Jednostka | Kształt / typ | Zakres i semantyka |
| --- | --- | --- | --- |
| `E`, `I` | aktywność proxy | `[n_regions]` | Stany populacji pobudzającej i hamującej ograniczone do `[0, 1]`. |
| `external_e`, `external_i` | aktywność proxy / napęd zewnętrzny | `[n_regions]` | Skończone wartości wejściowe dla populacji E/I. |
| `RegionWilsonCowanParams.tau_E`, `tau_I` | `[s]` | skalar na region | Dodatnie stałe czasowe populacji. |
| `RegionWilsonCowanParams.w_*` | bezwymiarowa waga lokalna | skalar na region | Skończone wagi lokalnych interakcji E/I. |
| `RegionWilsonCowanParams.gain_*`, `threshold_*` | bezwymiarowe | skalar na region | Parametry sigmoidy aktywacji. |
| `neuromodulators[name]` | poziom względny | `[n_regions]` | Wymagane nazwy: `dopamine`, `noradrenaline`, `acetylcholine`, `serotonin`, `gaba`, `glutamate`, `cortisol`, `adrenaline`; typowo zakres `[0, 1]`. |
| `NeuromodulationState` | poziom względny | osiem skalarów | Stan pojedynczego regionu; wartości powinny pozostać interpretowalne jako poziomy względne. |
| `NeuromodulationConfig.update_rate` | bezwymiarowe | skalar | Efektywnie obcinany do `[0, 1]`; określa udział celu w aktualizacji stanu. |

Wymagane pola konfiguracji:

- `model` — parametry lokalnego modelu populacyjnego lub ich profil bazowy;
- `brain_profile.id` — identyfikator bazowego profilu mózgu;
- `clinical_profile.id` i metadane profilu, jeśli wyniki mają być porównywane
  dydaktycznie;
- `rng_seed` albo `seed` — źródło deterministyczności szumu neuromodulacyjnego;
- `pathology.enabled`, `pathology.mutations`, `pathology.scenario` — jawne
  wskazanie zmian patologicznych, jeśli są używane.

Deterministyczność: krok Wilsona-Cowana bez `neuromodulators` jest w pełni
deterministyczny. Krok z neuromodulatorami dodaje szum zależny od
neuromodulacji; do replikowalnych eksperymentów należy przekazać generator
utworzony z `rng_seed`/`seed` i zapisać tę wartość w artefaktach uruchomienia.
Aktualizacje `NeuromodulationState` są deterministyczne względem stanu, sygnałów
wejściowych i `update_rate`.

## Kontrakt D: `populations` → `physiology`

Warstwa fizjologii obserwacyjnej przyjmuje aktywność populacji albo regionów i
zwraca syntetyczne sygnały EEG/BOLD proxy.

| Pole | Jednostka | Kształt / typ | Zakres i semantyka |
| --- | --- | --- | --- |
| `source_activity` | aktywność źródłowa proxy | `[n_sources]` albo `[n_samples, n_sources]` | `n_sources` powinno odpowiadać liczbie regionów albo jawnie udokumentowanej liczbie źródeł. |
| `leadfield` | względna projekcja liniowa | `[n_sensors, n_sources]` | Niepusta macierz 2D operatora forward EEG. |
| `eeg` | amplituda syntetyczna proxy | `[n_sensors]` albo `[n_samples, n_sensors]` | Wynik projekcji forward; przy referencji average średnia po sensorach wynosi zero. |
| `sensor_noise_std` | amplituda proxy | skalar `float` | `0.0` oznacza brak szumu; dodatnia wartość wymaga jawnego generatora RNG dla replikowalności. |
| `activity` dla BOLD | aktywność proxy | dowolny kształt numeryczny | Po odjęciu `baseline` wartości ujemne są obcinane do zera. |
| `neural_drive` | nieujemny napęd BOLD proxy | `[n_samples]` albo `[n_samples, n_regions]` | Wejście do splotu HRF. |
| `hrf` | bezwymiarowe | `[length]` | Znormalizowany wektor odpowiedzi hemodynamicznej; `length > 0`, `dt > 0`. |
| `bold` | amplituda BOLD proxy | `[n_samples]` albo `[n_samples, n_regions]` | Wynik splotu zachowuje kształt `neural_drive`. |

Wymagane pola konfiguracji:

- `analysis.sets` — lista zestawów analiz, np. `spectral`, `phase_locking`,
  `connectivity`, `information_flow`;
- `timestep` lub jawne `fs` — do przeliczenia osi czasu i pasm `[Hz]`;
- konfiguracja kanału EEG, jeżeli jest używany: `leadfield`, `reference`,
  `sensor_noise_std` oraz `rng_seed`/`seed` dla szumu;
- konfiguracja BOLD, jeżeli jest używany: `baseline`, parametry HRF (`length`,
  `dt`, `peak_latency`, `undershoot_latency`, `ratio`).

Deterministyczność: projekcja EEG bez szumu, referencja average, transformacja
neuro-naczyniowa, HRF i splot BOLD są deterministyczne. Projekcja EEG z szumem
jest replikowalna tylko z jawnie przekazanym `numpy.random.Generator` utworzonym
z zapisanego ziarna.

## Kontrakt E: `physiology` → metryki sygnałowe

Metryki sygnałowe przyjmują syntetyczne sygnały EEG/BOLD lub aktywność regionów
po stronie obserwacyjnej. Ten kontrakt blokuje dodawanie nowych metryk, dopóki
nowa metryka nie zadeklaruje jednostki, kształtu wejścia i zakresu wyniku.

| Metryka / wejście | Jednostka | Kształt / typ | Zakres i semantyka |
| --- | --- | --- | --- |
| `compute_band_powers(signal, fs)` | wejście: amplituda proxy; wynik: moc proxy `[amplituda²]` | `signal`: `[n_samples]`, `fs > 0` | Podsumowania pasm są nieujemne; `frequencies` i `power_spectrum` mają kształt `rfft`. |
| `compute_phase_locking(signal_a, signal_b)` | bezwymiarowe | dwa sygnały `[n_samples]` tego samego kształtu | `plv` w zakresie `[0, 1]`; `phase_diff` ma kształt wejścia. |
| `compute_connectivity(signals)` | korelacja / proxy PLI | `[n_samples, n_channels]` | Macierze `[n_channels, n_channels]`; korelacja w `[-1, 1]`, PLI-proxy w `[0, 1]`. |
| `compute_information_flow(signals)` | różnica korelacji opóźnionych | `[n_samples, n_channels]`, minimum 3 próbki | Macierz kierunkowa `[n_channels, n_channels]`; przekątna pozostaje zerowa. |

Wymagane pola konfiguracji:

- `analysis.sets` musi jawnie wskazywać, które grupy metryk mają być liczone;
- `fs` albo `timestep` muszą być zapisane dla metryk spektralnych;
- metryki raportowe muszą mieć polskie `interpretation_pl`, `limitations_pl`,
  `unit` i przypisanie do grup profili.

Deterministyczność: metryki są deterministyczne względem tablic wejściowych.
Jeżeli dane wejściowe pochodzą z kanału szumowego, deterministyczność zależy od
kontraktu źródłowego RNG.
