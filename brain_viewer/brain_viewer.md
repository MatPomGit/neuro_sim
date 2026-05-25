Tak. Ten moduł powinien być osobną warstwą wizualizacji neuroanatomicznej, niezależną od samego silnika symulacji. Symulator generuje aktywność regionów w czasie, a moduł mapuje te wartości na powierzchnię lub przekroje mózgu.

Docelowa nazwa modułu:

```text
brain_viewer/
```

## 1. Cel modułu

Moduł ma pokazywać aktywność mózgu w czterech rzutach:

```text
1. rzut strzałkowy        sagittal
2. rzut czołowy           coronal
3. rzut poprzeczny        axial / transverse
4. rzut powierzchniowy    lateral / cortical surface
```

Użytkownik powinien móc:

```text
odtworzyć symulację jako animację
zatrzymać odtwarzanie
ręcznie przesuwać czas suwakiem
wybrać moduł poznawczy albo region anatomiczny
zmieniać skalę koloru
wyświetlać wartości liczbowe aktywności
eksportować klatkę PNG
eksportować animację GIF/MP4
```

Do wersji webowej najlepiej użyć NiiVue albo własnej uproszczonej wizualizacji SVG/Canvas. NiiVue jest przeglądarkowym narzędziem WebGL do wizualizacji danych neuroobrazowych, w tym wolumenów, powierzchni, statystycznych nakładek i konektomów. ([niivue.com][1]) Alternatywnie BrainBrowser oferuje webowe narzędzia JavaScript do wizualizacji danych 2D/3D neuroobrazowania, w tym surface viewer i volume viewer. ([PMC][2]) Do wersji Pythonowej przydatny jest Nilearn, który ma gotowe funkcje do rzutów ortogonalnych i map statystycznych na przekrojach mózgu. ([nilearn.github.io][3])

## 2. Docelowa architektura

```text
brain_model/
    model.py
    oscillators.py
    modules.py
    connectivity.py

brain_viewer/
    __init__.py
    atlas.py
    mapping.py
    frames.py
    colormaps.py
    playback.py
    export.py

docs/
    index.html
    viewer.js
    viewer.css
    assets/
        brain/
            brain_sagittal.svg
            brain_coronal.svg
            brain_axial.svg
            brain_lateral.svg
            region_masks.json
```

Wersja Pythonowa i webowa powinny korzystać z tego samego formatu danych wyjściowych.

## 3. Format danych wejściowych

Symulator powinien zwracać nie tylko aktywność modułów poznawczych, ale też aktywność regionów mózgu.

Obecnie masz:

```python
activity[t, module]
```

Docelowo trzeba dodać:

```python
regional_activity[t, region]
```

Przykład struktury:

```python
simulation_output = {
    "time": time,
    "module_activity": X,
    "regional_activity": R,
    "region_names": region_names,
    "module_names": module_names,
    "diagnostics": D,
    "oscillations": oscillations
}
```

Dla wersji webowej można eksportować to jako JSON:

```json
{
  "time": [0.00, 0.01, 0.02],
  "regions": ["V1", "A1", "DLPFC", "ACC", "Hippocampus", "Amygdala"],
  "activity": [
    [0.12, 0.05, 0.18, 0.20, 0.10, 0.07],
    [0.13, 0.05, 0.19, 0.21, 0.11, 0.07]
  ]
}
```

## 4. Mapowanie modułów poznawczych na regiony mózgu

Na początku można zastosować uproszczone mapowanie funkcjonalne:

```text
VIS   → V1, V2, occipital cortex
AUD   → A1, superior temporal gyrus
INT   → insula, somatosensory cortex
SAL   → anterior insula, dACC, amygdala
ATT   → frontal eye fields, intraparietal sulcus, pulvinar
PHON  → superior temporal gyrus, inferior frontal gyrus
VSWM  → parietal cortex, occipital cortex, DLPFC
EXEC  → DLPFC, ACC, basal ganglia
EPIS  → hippocampus, parahippocampal cortex
SEM   → temporal cortex, angular gyrus
HIP   → hippocampus
VAL   → ventral striatum, orbitofrontal cortex, VTA
MOT   → premotor cortex, M1, basal ganglia
DMN   → mPFC, PCC, angular gyrus
LANG  → Broca, Wernicke, temporal cortex
GW    → frontoparietal network, thalamus
```

Technicznie będzie to macierz:

```text
M[region, module]
```

Wtedy:

```text
regional_activity[t, region] = Σ module_activity[t, module] · M[region, module]
```

## 5. Cztery rzuty mózgu

Najprostsza wersja dydaktyczna powinna używać konturowych grafik SVG mózgu z maskami regionów. Każdy region jest osobnym elementem SVG z identyfikatorem.

Przykład:

```html
<path id="region_DLPFC_left" data-region="DLPFC_L" d="..." />
<path id="region_ACC" data-region="ACC" d="..." />
<path id="region_HIP_L" data-region="HIP_L" d="..." />
```

W czasie symulacji JavaScript zmienia kolor regionów:

```javascript
regionElement.style.fill = colorScale(activityValue);
```

To jest znacznie lżejsze niż pełna wizualizacja NIfTI i dobrze pasuje do GitHub Pages.

Docelowo można mieć dwa tryby:

```text
tryb prosty       SVG / Canvas, szybki, dydaktyczny
tryb zaawansowany NiiVue / WebGL, atlas 3D, dane NIfTI
```

## 6. Panel sterowania

Interfejs powinien mieć:

```text
Play / Pause
Stop
suwak czasu
pole aktualnego czasu symulacji
prędkość odtwarzania: 0.25x, 0.5x, 1x, 2x, 4x
wybór źródła aktywności:
    aktywność poznawcza
    EEG E-I
    moc theta
    moc alpha
    moc beta
    moc gamma
tryb normalizacji:
    globalna
    dla regionu
    dla aktualnej klatki
threshold aktywacji
opacity overlay
```

Układ strony:

```text
+--------------------------------------------------+
| Panel parametrów symulacji                       |
+--------------------------------------------------+
| [Play] [Pause] [Stop] [time slider] [speed]      |
+--------------------------------------------------+
| Sagittal       | Coronal                         |
| Axial          | Lateral surface                 |
+--------------------------------------------------+
| Wykres czasowy aktywności wybranego regionu       |
+--------------------------------------------------+
| Legenda koloru + eksport                          |
+--------------------------------------------------+
```

## 7. Proponowany moduł Python

```python
# brain_viewer/mapping.py

import numpy as np


class BrainRegionMapper:
    def __init__(self, module_names, region_names, mapping_matrix):
        self.module_names = module_names
        self.region_names = region_names
        self.M = mapping_matrix

    def modules_to_regions(self, module_activity):
        """
        module_activity: array [time, module]
        return: regional_activity [time, region]
        """
        R = module_activity @ self.M.T
        R = np.clip(R, 0.0, 1.0)
        return R
```

Przykład macierzy:

```python
def default_module_region_mapping(module_names, region_names):
    M = np.zeros((len(region_names), len(module_names)))

    def link(region, module, weight):
        r = region_names.index(region)
        m = module_names.index(module)
        M[r, m] = weight

    link("V1_L", "VIS", 1.0)
    link("V1_R", "VIS", 1.0)
    link("A1_L", "AUD", 1.0)
    link("A1_R", "AUD", 1.0)
    link("DLPFC_L", "EXEC", 0.9)
    link("DLPFC_R", "EXEC", 0.9)
    link("ACC", "SAL", 0.6)
    link("ACC", "EXEC", 0.5)
    link("HIP_L", "HIP", 1.0)
    link("HIP_R", "HIP", 1.0)
    link("AMY_L", "SAL", 0.7)
    link("AMY_R", "SAL", 0.7)

    row_sum = M.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return M / row_sum
```

## 8. Proponowany moduł JavaScript

```javascript
class BrainActivityPlayer {
  constructor(simulationData, regionMasks, options = {}) {
    this.data = simulationData;
    this.regionMasks = regionMasks;
    this.frame = 0;
    this.playing = false;
    this.speed = options.speed || 1.0;
    this.fps = options.fps || 30;
    this.valueMin = 0.0;
    this.valueMax = 1.0;
  }

  setFrame(frameIndex) {
    this.frame = Math.max(0, Math.min(frameIndex, this.data.time.length - 1));
    this.renderFrame();
    this.updateTimeLabel();
    this.updateSlider();
  }

  renderFrame() {
    const values = this.data.regional_activity[this.frame];

    for (let i = 0; i < this.data.region_names.length; i++) {
      const region = this.data.region_names[i];
      const value = values[i];
      const color = this.colorScale(value);

      document
        .querySelectorAll(`[data-region="${region}"]`)
        .forEach(el => {
          el.style.fill = color;
          el.style.opacity = value > 0.05 ? 0.95 : 0.20;
        });
    }
  }

  colorScale(value) {
    const x = Math.max(0, Math.min(1, value));
    const r = Math.round(255 * x);
    const g = Math.round(80 * (1 - x));
    const b = Math.round(255 * (1 - x));
    return `rgb(${r},${g},${b})`;
  }

  play() {
    if (this.playing) return;
    this.playing = true;

    const loop = () => {
      if (!this.playing) return;
      this.setFrame(this.frame + Math.round(this.speed));

      if (this.frame >= this.data.time.length - 1) {
        this.playing = false;
        return;
      }

      setTimeout(loop, 1000 / this.fps);
    };

    loop();
  }

  pause() {
    this.playing = false;
  }

  stop() {
    this.playing = false;
    this.setFrame(0);
  }

  updateTimeLabel() {
    document.getElementById("timeLabel").textContent =
      `${this.data.time[this.frame].toFixed(2)} s`;
  }

  updateSlider() {
    document.getElementById("timeSlider").value = this.frame;
  }
}
```

## 9. Integracja z obecnym `docs/index.html`

Do istniejącej strony dodałbym sekcję:

```html
<section class="panel">
  <h2>Mapa aktywności mózgu</h2>

  <div class="playback-controls">
    <button id="playBrain">Play</button>
    <button id="pauseBrain">Pause</button>
    <button id="stopBrain">Stop</button>
    <input id="timeSlider" type="range" min="0" max="0" value="0">
    <span id="timeLabel">0.00 s</span>
  </div>

  <div class="brain-grid">
    <div id="viewSagittal" class="brain-view"></div>
    <div id="viewCoronal" class="brain-view"></div>
    <div id="viewAxial" class="brain-view"></div>
    <div id="viewLateral" class="brain-view"></div>
  </div>
</section>
```

CSS:

```css
.brain-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.brain-view {
  background: #ffffff;
  border: 1px solid #d7dce5;
  border-radius: 14px;
  padding: 12px;
  min-height: 320px;
}

.brain-view svg {
  width: 100%;
  height: 100%;
}
```

## 10. Dane regionów

Na początek wystarczy około 30 regionów:

```text
V1_L, V1_R
V2_L, V2_R
A1_L, A1_R
S1_L, S1_R
M1_L, M1_R
DLPFC_L, DLPFC_R
OFC_L, OFC_R
ACC
PCC
mPFC
IPS_L, IPS_R
IFG_L, IFG_R
STG_L, STG_R
Angular_L, Angular_R
HIP_L, HIP_R
AMY_L, AMY_R
Insula_L, Insula_R
Thalamus
BasalGanglia_L, BasalGanglia_R
Cerebellum_L, Cerebellum_R
```

To wystarczy do sensownej demonstracji neuropsychologicznej.

## 11. Kolejność implementacji

Etap 1: dane i mapowanie.

```text
dodać region_names
dodać module_to_region_mapping
generować regional_activity
eksportować regional_activity do JSON
```

Etap 2: prosta wizualizacja SVG.

```text
przygotować 4 konturowe SVG mózgu
każdy region jako osobny path
kolorowanie regionów według aktywności
suwak czasu
play/pause
```

Etap 3: integracja z symulatorem.

```text
po kliknięciu „Uruchom symulację”
    model generuje aktywność
    mapper tworzy regional_activity
    viewer pokazuje animację
```

Etap 4: analiza interaktywna.

```text
kliknięcie regionu pokazuje nazwę
wykres aktywności regionu w czasie
porównanie dwóch regionów
wybór pasma EEG
wybór modułu poznawczego
```

Etap 5: wersja zaawansowana.

```text
NiiVue/WebGL
atlas NIfTI
powierzchnia kory
projekcja aktywności na siatkę 3D
eksport animacji
```

## 12. Najlepsza decyzja projektowa

Na tym etapie nie zaczynałbym od pełnych danych MRI/NIfTI. Zrobiłbym najpierw szybką, dydaktyczną wizualizację SVG w czterech rzutach. Będzie lekka, szybka i dobrze zadziała na GitHub Pages. Dopiero później warto dodać tryb zaawansowany oparty o NiiVue.

Docelowy przepływ powinien wyglądać tak:

```text
symulacja poznawcza
    ↓
aktywność modułów
    ↓
mapowanie moduły → regiony mózgu
    ↓
regional_activity[t, region]
    ↓
cztery rzuty mózgu
    ↓
animacja / suwak / analiza regionu
```

[1]: https://niivue.com/docs/?utm_source=chatgpt.com "Getting started"
[2]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4292582/?utm_source=chatgpt.com "BrainBrowser: distributed, web-based neurological data ..."
[3]: https://nilearn.github.io/dev/modules/generated/nilearn.plotting.plot_stat_map.html?utm_source=chatgpt.com "nilearn.plotting.plot_stat_map"
