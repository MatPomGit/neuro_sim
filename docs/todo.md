Taką rozbudowę trzeba zaplanować jako przejście od „symulatora procesów poznawczych” do wieloskalowego symulatora mózgu. Pełna symulacja biologiczna całego ludzkiego mózgu w sensie komórka-po-komórce jest obecnie praktycznie niewykonalna na typowej infrastrukturze. Realistyczny cel to architektura hybrydowa: wybrane obszary modelowane szczegółowo, reszta jako modele populacyjne, sieciowe i funkcjonalne. Tak działają współczesne podejścia typu The Virtual Brain, modele neural mass oraz współsymulacje mikro-makro. TVB jest używany do personalizowanych modeli sieci mózgowych, natomiast nowsze prace integrują TVB z symulatorami bardziej szczegółowymi, np. Arbor, aby łączyć poziom komórkowy z makroskopowym. ([EBRAINS][1])

## 1. Docelowa idea systemu

Docelowy program powinien mieć trzy warstwy:

```text
warstwa biologiczna
    neurony, synapsy, populacje neuronalne, astrocyty, neuromodulatory

warstwa sieciowa
    obszary mózgu, konektom, opóźnienia przewodzenia, oscylacje, synchronizacja

warstwa poznawcza
    uwaga, pamięć robocza, salience, kontrola wykonawcza, język, emocje, decyzje
```

Obecny program znajduje się głównie w trzeciej warstwie, z początkiem warstwy sieciowej przez oscylatory Wilsona-Cowana. Kolejnym etapem jest „podłożenie” pod każdy moduł poznawczy biologicznego mechanizmu: populacji pobudzających i hamujących, receptorów, neuroprzekaźników, plastyczności i sprzężeń międzyobszarowych.

## 2. Proponowana architektura docelowa

```text
brain_simulator/
├── apps/
│   ├── desktop_gui/
│   ├── web_gui/
│   └── notebooks/
│
├── brain_core/
│   ├── anatomy/
│   │   ├── regions.py
│   │   ├── connectome.py
│   │   ├── cortical_layers.py
│   │   └── atlases.py
│   │
│   ├── neurons/
│   │   ├── izhikevich.py
│   │   ├── adaptive_exponential.py
│   │   ├── hodgkin_huxley.py
│   │   └── cell_types.py
│   │
│   ├── synapses/
│   │   ├── ampa.py
│   │   ├── nmda.py
│   │   ├── gaba.py
│   │   ├── dopamine.py
│   │   ├── serotonin.py
│   │   ├── acetylcholine.py
│   │   └── plasticity.py
│   │
│   ├── populations/
│   │   ├── neural_mass.py
│   │   ├── wilson_cowan.py
│   │   ├── jansen_rit.py
│   │   ├── mean_field.py
│   │   └── spiking_population.py
│   │
│   ├── networks/
│   │   ├── structural_network.py
│   │   ├── functional_network.py
│   │   ├── delays.py
│   │   └── coupling.py
│   │
│   ├── cognition/
│   │   ├── attention.py
│   │   ├── working_memory.py
│   │   ├── episodic_memory.py
│   │   ├── semantic_memory.py
│   │   ├── executive_control.py
│   │   ├── salience.py
│   │   ├── language.py
│   │   ├── valuation.py
│   │   └── global_workspace.py
│   │
│   ├── physiology/
│   │   ├── eeg_forward_model.py
│   │   ├── bold_hrf.py
│   │   ├── metabolism.py
│   │   ├── neurovascular_coupling.py
│   │   └── homeostasis.py
│   │
│   ├── simulation/
│   │   ├── integrators.py
│   │   ├── scheduler.py
│   │   ├── multiscale_engine.py
│   │   ├── random_sources.py
│   │   └── state.py
│   │
│   ├── experiments/
│   │   ├── stimuli.py
│   │   ├── cognitive_tasks.py
│   │   ├── lesions.py
│   │   ├── pharmacology.py
│   │   └── protocols.py
│   │
│   └── analysis/
│       ├── eeg.py
│       ├── spectral.py
│       ├── connectivity.py
│       ├── information_flow.py
│       ├── phase_locking.py
│       └── reports.py
│
├── data/
│   ├── atlases/
│   ├── connectomes/
│   ├── parameters/
│   └── validation/
│
├── configs/
│   ├── default.yaml
│   ├── cognitive_demo.yaml
│   ├── eeg_demo.yaml
│   ├── lesion_demo.yaml
│   └── pharmacology_demo.yaml
│
└── tests/
```

Kluczowa zasada: kod modelu nie powinien być zaszyty w GUI. GUI powinno tylko generować konfigurację, np. YAML/JSON, a silnik symulacji powinien działać niezależnie.

## 3. Poziomy modelowania

### Poziom A: obecny model poznawczy

To zostaje jako warstwa wysokopoziomowa. Moduły typu `ATT`, `EXEC`, `HIP`, `SEM`, `DMN`, `GW` nadal istnieją, ale nie są już tylko abstrakcyjnymi zmiennymi. Każdy moduł dostaje biologiczne „ciało”.

Przykład:

```text
HIP =
    CA1
    CA3
    DG
    subiculum
    populacje pyramidalne
    interneurony GABA
    oscylacje theta
    plastyczność epizodyczna
```

```text
EXEC =
    DLPFC
    ACC
    basal ganglia loop
    populacje pobudzające/hamujące
    rytm beta
    kontrola bramkowania pamięci roboczej
```

### Poziom B: neural mass / mean field

To najbardziej praktyczny poziom dla całego mózgu. Każdy region atlasu mózgowego, np. 68, 100, 200 albo 400 regionów, jest opisany niewielkim układem równań różniczkowych. Takie podejście jest powszechne w modelowaniu whole-brain, bo jeden region można reprezentować małą liczbą zmiennych zamiast milionami neuronów. ([PLOS][2])

Minimalnie:

```text
E_r(t)  aktywność populacji pobudzającej regionu r
I_r(t)  aktywność populacji hamującej regionu r
A_r(t)  adaptacja / zmęczenie
N_r(t)  neuromodulacja
```

Równania:

```text
dE_r/dt = (-E_r + S(w_EE E_r - w_EI I_r + input_r + coupling_r)) / τ_E
dI_r/dt = (-I_r + S(w_IE E_r - w_II I_r)) / τ_I
```

### Poziom C: sieci kolczaste, czyli spiking neural networks

Dla wybranych obszarów, np. hipokampa, kory przedczołowej, wzgórza lub ciała migdałowatego, można zastosować modele neuronów kolczastych. Tutaj warto użyć Brian2, NEST, NEURON, Arbor albo NetPyNE. Brian2 jest elastycznym symulatorem sieci kolczastych w Pythonie, a NetPyNE pozwala budować wieloskalowe modele w NEURON z separacją parametrów od implementacji. ([brian2.readthedocs.io][3])

Praktyczna zasada:

```text
cały mózg        neural mass / mean field
wybrane obwody   spiking neural network
wybrane neurony  compartmental / Hodgkin-Huxley
```

### Poziom D: modele komórkowe

To najwyższy koszt obliczeniowy. Stosować tylko lokalnie, np. do demonstracji kanałów jonowych, receptorów NMDA, wpływu GABA albo dopaminy.

Modele:

```text
Hodgkin-Huxley
Morris-Lecar
Adaptive Exponential Integrate-and-Fire
Izhikevich
multi-compartment NEURON
```

## 4. Moduł anatomii i konektomu

Obecna macierz `W` powinna zostać zastąpiona przez strukturalny konektom.

Dane wejściowe:

```text
atlas mózgu
lista regionów
macierz połączeń strukturalnych
długości włókien
opóźnienia przewodzenia
typ regionu: sensoryczny, asocjacyjny, limbiczny, motoryczny
```

Model połączeń:

```text
coupling_i(t) = Σ_j C_ij · activity_j(t - delay_ij)
```

To jest istotne, bo mózg nie jest siecią natychmiastową. Opóźnienia przewodzenia są warunkiem powstawania synchronizacji, desynchronizacji, rytmów i fal aktywności.

## 5. Moduł neurochemii

Pełniejsza symulacja musi mieć neuromodulatory jako osobne pola dynamiczne, a nie pojedyncze zmienne diagnostyczne.

Proponowane systemy:

```text
dopamina        nagroda, błąd predykcji, motywacja, bramkowanie jąder podstawy
noradrenalina   czujność, stres, niepewność, wzrost gain
serotonina      stabilizacja nastroju, impulsywność, awersja, cierpliwość
acetylocholina  uwaga, uczenie sensoryczne, precyzja predykcji
GABA            hamowanie lokalne
glutaminian     pobudzenie, transmisja AMPA/NMDA
```

Każdy neuromodulator powinien wpływać na parametry regionów:

```text
gain sigmoidy
próg aktywacji
plastyczność synaptyczna
stosunek E/I
szum neuronalny
stałą czasową
```

Przykład:

```text
wysoka acetylocholina → większa precyzja sygnałów sensorycznych
wysoka noradrenalina  → większy gain, silniejsza reakcja salience
wysoka dopamina       → silniejsze uczenie wartościowania
wysoki GABA           → hamowanie, spadek pobudliwości
```

## 6. Moduł plastyczności

Bez plastyczności program będzie tylko symulatorem aktywacji. Biologiczna symulacja wymaga zmiany połączeń w czasie.

Potrzebne mechanizmy:

```text
Hebbian learning
STDP
homeostatic plasticity
synaptic scaling
reinforcement-modulated plasticity
metaplasticity
consolidation
forgetting
```

Dla poziomu neural mass wystarczy reguła:

```text
dW_ij/dt = η · pre_j · post_i · neuromodulator - λW_ij
```

Dla sieci kolczastych można stosować STDP:

```text
Δw = A+ exp(-Δt/τ+) gdy pre przed post
Δw = -A- exp(Δt/τ-) gdy post przed pre
```

## 7. Moduł EEG, LFP i fMRI/BOLD

Obecny sygnał `E-I` jest dobrym szkicem. Docelowo trzeba rozdzielić:

```text
spikes       aktywność neuronów kolczastych
LFP          lokalny potencjał polowy
EEG/MEG      projekcja aktywności źródeł korowych na elektrody
BOLD/fMRI    wolna odpowiedź hemodynamiczna
```

Minimalny model EEG:

```text
source_r(t) = gain_r · pyramidal_activity_r(t)
EEG_e(t) = Σ_r leadfield[e,r] · source_r(t)
```

Minimalny model BOLD:

```text
neural_activity → neurovascular coupling → HRF convolution → BOLD
```

Dzięki temu program może generować dane porównywalne z EEG/fMRI, a nie tylko abstrakcyjne wykresy aktywacji.

## 8. Moduł zadań poznawczych

Obecny scenariusz bodźców należy zamienić na protokoły eksperymentalne.

Przykłady:

```text
Stroop task
Go/No-Go
N-back
oddball auditory
visual search
fear conditioning
reward learning
semantic priming
working memory delay task
```

Każde zadanie powinno mieć:

```text
bodźce
czas prezentacji
reguły odpowiedzi
oczekiwane reakcje
miary behawioralne
mapowanie na moduły mózgowe
```

Wyniki:

```text
czas reakcji
trafność
błąd predykcji
siła uwagi
obciążenie pamięci roboczej
aktywność EEG
moc pasm
synchronizacja między regionami
```

## 9. Moduł uszkodzeń i zaburzeń

Bardzo wartościowy naukowo byłby moduł manipulacji patologicznych.

Typy manipulacji:

```text
lesion          usunięcie lub osłabienie regionu
disconnection   osłabienie połączeń
noise increase  wzrost szumu
E/I imbalance   zaburzenie równowagi pobudzenie-hamowanie
dopamine shift  zmiana dopaminy
GABA reduction  spadek hamowania
atrophy         spadek pojemności regionu
delay increase  spowolnienie przewodzenia
```

Przykłady symulacyjne:

```text
uszkodzenie hipokampa → deficyt kodowania epizodycznego
osłabienie DLPFC → gorsza kontrola wykonawcza
nadreaktywny salience network → błędna detekcja istotności
obniżony GABA → nadmierna synchronizacja / podatność napadowa
```

## 10. Silnik symulacyjny

Docelowy silnik powinien obsługiwać wiele solverów.

```text
Euler-Maruyama      szybki, prosty, dla SDE
Runge-Kutta RK4     dokładniejszy dla ODE
Dopri5 / RK45       adaptacyjny krok czasowy
event-based         dla sieci kolczastych
co-simulation       różne kroki czasowe dla różnych skal
GPU backend         JAX / PyTorch / CuPy
```

Najważniejszy problem to różne skale czasowe:

```text
kanały jonowe       mikrosekundy-milisekundy
spikes              milisekundy
oscylacje EEG       milisekundy-sekundy
BOLD/fMRI           sekundy
uczenie             sekundy-godziny
konsolidacja        godziny-dni
```

Dlatego potrzebny jest scheduler wieloskalowy.

## 11. Architektura obliczeniowa

Docelowo:

```text
Python core
NumPy/SciPy dla wersji bazowej
JAX albo PyTorch dla przyspieszenia GPU
Brian2/NEST/NEURON/Arbor jako backendy opcjonalne
HDF5/Zarr do zapisu dużych wyników
YAML/JSON do konfiguracji eksperymentów
Plotly/Dash albo web GUI do interfejsu
```

Wersja GitHub Pages z Pyodide może nadal istnieć, ale tylko jako wersja demonstracyjna. Pełna biologiczna symulacja powinna działać lokalnie albo na serwerze/HPC. Pyodide nie jest właściwym środowiskiem dla ciężkich modeli wieloskalowych.

## 12. Etapy rozbudowy

### Etap 1: uporządkowanie obecnego modelu

Cel: stabilna baza.

Dodać:

```text
konfiguracje YAML
zapis wyników do CSV/HDF5
testy jednostkowe
walidację parametrów
moduł eksperymentów
rozdzielenie GUI od silnika
```

### Etap 2: pełne modele populacyjne

Cel: biologicznie interpretowalne moduły.

Dodać:

```text
Wilson-Cowan dla każdego regionu
Jansen-Rit dla sygnałów EEG
opóźnienia przewodzenia
osobne populacje E/I
oscylacje theta/alpha/beta/gamma
sprzężenie między regionami
```

### Etap 3: konektom i atlas

Cel: przejście z 16 modułów poznawczych na regiony anatomiczne.

Dodać:

```text
atlas Desikan-Killiany albo Schaefer
macierz konektomu
mapowanie regionów na funkcje poznawcze
projekcję regionów na moduły poznawcze
```

Przykład:

```text
ATT  = FEF + IPS + pulvinar
EXEC = DLPFC + ACC + basal ganglia
EPIS = hippocampus + parahippocampal cortex
SAL  = anterior insula + dACC + amygdala
DMN  = mPFC + PCC + angular gyrus
```

### Etap 4: neuromodulacja

Cel: biologiczne sterowanie parametrami.

Dodać:

```text
dopamina
noradrenalina
serotonina
acetylocholina
GABA/glutaminian
farmakologiczne manipulacje parametrów
```

### Etap 5: plastyczność i uczenie

Cel: model ma się zmieniać w wyniku doświadczenia.

Dodać:

```text
Hebbian learning
STDP
reinforcement learning
consolidation
forgetting
homeostatic regulation
```

### Etap 6: backend SNN dla wybranych obwodów

Cel: lokalnie szczegółowa symulacja biologiczna.

Dodać backend:

```text
Brian2 dla szybkich prototypów
NEST dla dużych SNN
NEURON/NetPyNE dla modeli biokomórkowych
Arbor dla symulacji wielkoskalowych/HPC
```

### Etap 7: walidacja

Cel: model nie tylko generuje wykresy, ale daje porównywalne dane.

Porównać z:

```text
EEG: moc pasm, ERP, phase locking
fMRI: BOLD, functional connectivity
behawior: czas reakcji, trafność, błędy
neuropsychologia: profile deficytów po uszkodzeniach
```

## 13. Proponowany docelowy przepływ działania

```text
1. Użytkownik wybiera eksperyment poznawczy.
2. System ładuje konfigurację mózgu.
3. System generuje bodźce.
4. Silnik symuluje dynamikę neuronalną i poznawczą.
5. Moduł fizjologii generuje EEG/BOLD.
6. Moduł zachowania generuje odpowiedzi.
7. Moduł analizy oblicza metryki.
8. GUI pokazuje wykresy, sieci, raport i eksport danych.
```

## 14. Najważniejsza decyzja projektowa

Nie próbowałbym od razu budować „pełnego mózgu” na poziomie neuronów. To byłoby obliczeniowo i metodologicznie niekontrolowane. Najlepsza architektura to:

```text
whole brain = neural mass / mean field
selected circuits = spiking neural networks
selected cells = biophysical compartment models
cognition = symbolic/functional control layer
```

To daje kompromis: biologiczna interpretowalność, wykonalność obliczeniowa i możliwość demonstracji procesów psychologii poznawczej oraz neuropsychologii.

[1]: https://ebrains.eu/data-tools-services/modelling-simulation/whole-brain-simulation?utm_source=chatgpt.com "Whole Brain Simulation"
[2]: https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012647&utm_source=chatgpt.com "Insights from next generation neural mass modelling ..."
[3]: https://brian2.readthedocs.io/?utm_source=chatgpt.com "Brian 2 documentation — Brian 2 2.10.1 documentation"
