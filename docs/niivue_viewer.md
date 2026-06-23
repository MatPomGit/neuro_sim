# Widok NiiVue/WebGL w `neuro_sim`

Ten dokument opisuje bieżącą webową integrację NiiVue oraz rekomendowany sposób
przeniesienia tego samego widoku do aplikacji desktopowej PySide6/Qt. Widok jest
warstwą prezentacji: nie uruchamia symulacji, nie modyfikuje danych źródłowych i
nie zapisuje artefaktów eksperymentu.

## Aktualny zakres webowy

Plik `docs/niivue_viewer.html` udostępnia statyczny demonstrator NiiVue:

- ładuje NiiVue jako moduł ES z CDN jsDelivr;
- inicjalizuje `canvas` WebGL;
- wczytuje demonstracyjne tło anatomiczne MNI152;
- pozwala przełączać rzut poprzeczny, czołowy, strzałkowy, wielorzutowy i 3D;
- pozwala zmieniać skalę koloru ostatniego wolumenu;
- pozwala wczytać dodatkową nakładkę NIfTI z podanego adresu URL.

To jest tryb diagnostyczno-demonstracyjny dla przyszłych eksportów. Produkcyjny
pipeline powinien najpierw utworzyć jawny artefakt pochodny NIfTI, a dopiero
potem przekazać go do widoku.

## Dane wejściowe i odpowiedzialności

Widok NiiVue powinien przyjmować wyłącznie przygotowane artefakty:

| Dane | Format | Odpowiedzialny moduł | Uwagi |
| --- | --- | --- | --- |
| Tło anatomiczne | `.nii` albo `.nii.gz` | atlas / dane referencyjne | Nie nadpisywać danych surowych. |
| Nakładka aktywności | `.nii` albo `.nii.gz` | eksport pochodnych | Powinna powstać z `regional_activity`. |
| Metadane przebiegu | `.json` | pipeline eksperymentu | Powinny zawierać seed, commit, konfigurację i wersję danych. |
| Oś czasu aktywności | `.json` | pipeline eksperymentu | Docelowo steruje suwakiem czasu i animacją. |

Minimalny katalog pochodnych dla przyszłej integracji:

```text
results/<run-id>/
├── config.yaml
├── git_info.json
├── environment.json
├── metrics.json
└── derivatives/
    └── niivue/
        ├── dataset_description.json
        ├── sub-demo_task-sim_desc-activity_overlay.nii.gz
        └── sub-demo_task-sim_desc-activity_timeseries.json
```

Nazwy plików i metadane powinny być zgodne z wymaganiami BIDS opisanymi w
`docs/bids_brain_imaging_requirements.md`, jeśli artefakty reprezentują dane
neuroobrazowe lub ich pochodne.

## Rekomendowana implementacja desktopowa

Desktop powinien użyć tego samego komponentu HTML/JavaScript, osadzonego w Qt.
Pozwala to uniknąć utrzymywania dwóch niezależnych implementacji WebGL.

### 1. Docelowy stos

- `PySide6.QtWebEngineWidgets.QWebEngineView` jako kontener widoku NiiVue;
- `PySide6.QtWebChannel.QWebChannel` jako bezpieczny most Python ↔ JavaScript;
- lokalny plik HTML albo zasób aplikacji Qt jako źródło strony;
- te same nazwy pól i komunikatów po polsku co w webowym widoku;
- brak nowych przepływów `tkinter`.

### 2. Proponowany podział plików

```text
brain_model/
    qt_niivue_viewer.py      # widget Qt z QWebEngineView
    qt_niivue_bridge.py      # QObject wystawiony przez QWebChannel

docs/
    niivue_viewer.html       # wspólny widok web/desktop na czas MVP
```

Jeśli komponent zacznie być używany produkcyjnie, część HTML/JS warto przenieść
z `docs/` do wersjonowanego zasobu aplikacji, np. `brain_viewer/web/`, a w
`docs/` zostawić stronę demonstracyjną i instrukcję.

### 3. Przepływ danych desktopowych

```text
PySide6 GUI
  ↓ wybór przebiegu albo artefaktu NIfTI
qt_niivue_bridge.py
  ↓ walidacja ścieżki i metadanych
QWebChannel
  ↓ komunikat loadOverlay({ url, name, opacity, colormap })
niivue_viewer.html
  ↓ nv.addVolumeFromUrl(...)
NiiVue/WebGL
```

Most Qt powinien przekazywać do JavaScript tylko ścieżki do jawnie wybranych
artefaktów lub plików zapisanych przez pipeline. Nie powinien udostępniać
arbitralnego dostępu do systemu plików.

### 4. Szkic API mostu Qt

Poniższy szkic opisuje kontrakt, a nie gotowy kod produkcyjny:

```python
class NiiVueBridge(QObject):
    overlayLoaded = Signal(dict)

    @Slot(str, result=dict)
    def describe_overlay(self, overlay_path: str) -> dict[str, str]:
        """Zwróć zwalidowane metadane nakładki NIfTI dla widoku NiiVue."""
```

Metoda powinna:

1. przyjąć ścieżkę wybraną przez użytkownika w GUI;
2. sprawdzić rozszerzenie `.nii` lub `.nii.gz`;
3. sprawdzić, czy plik istnieje i nie jest katalogiem;
4. opcjonalnie odczytać metadane towarzyszące z JSON;
5. zwrócić serializowalny słownik z nazwą, adresem lokalnym i opisem.

### 5. Ograniczenia środowiskowe

Qt WebEngine wymaga działającego OpenGL albo zgodnej emulacji programowej. W
środowiskach serwerowych bez bibliotek graficznych, np. bez `libGL.so.1`, import
lub uruchomienie `QWebEngineView` może się nie udać. Desktopowa implementacja
powinna wtedy pokazać czytelny komunikat po polsku i zaproponować webowy widok
albo eksport PNG/SVG jako tryb awaryjny.

### 6. Kolejność wdrożenia desktopu

1. Dodać `qt_niivue_viewer.py` z prostym `QWebEngineView`, który ładuje lokalny
   `docs/niivue_viewer.html`.
2. Dodać statyczny test, że moduł nie importuje `tkinter` i używa PySide6/Qt.
3. Dodać `qt_niivue_bridge.py` z walidacją ścieżki nakładki.
4. Rozszerzyć HTML o funkcję `window.neuroSimViewer.loadOverlay(payload)`, aby
   desktop nie musiał symulować wpisywania URL w formularzu.
5. Dodać akcję w istniejącym GUI Qt, np. „Otwórz widok NiiVue”, bez zmiany
   dotychczasowych wyników symulacji.
6. Dopiero po stabilizacji eksportu dodać generowanie pochodnych NIfTI z
   `regional_activity`.


## Czy desktop może użyć `ipyniivue`?

Może, ale nie jako podstawowy widget produkcyjnego GUI Qt. `ipyniivue` jest
widgetem Jupyter opartym na `anywidget`, więc naturalnie działa w JupyterLab,
Notebooku, JupyterLite, VS Code notebooks albo środowisku z menedżerem widgetów
Jupyter. Desktopowe GUI PySide6 nie ma takiego menedżera domyślnie.

Praktyczne warianty są trzy:

| Wariant | Ocena | Kiedy używać | Koszt |
| --- | --- | --- | --- |
| `QWebEngineView` + wspólny HTML NiiVue | rekomendowany | główne desktop GUI | najmniej zależności i brak Jupyter runtime |
| lokalny Jupyter Server + `ipyniivue` w `QWebEngineView` | możliwy, ale ciężki | tryb badawczy lub notebookowy | uruchamianie serwera, tokeny, lifecycle kernela, więcej zależności |
| eksport notebooka z `ipyniivue` | dobry dodatek | analiza offline i materiały dydaktyczne | osobny artefakt, nie natywny panel GUI |

Dlatego dla desktopu rekomendujemy bezpośrednie osadzenie NiiVue w Qt WebEngine.
`ipyniivue` warto potraktować jako dodatkowy tryb notebookowy: eksportuj
artefakty NIfTI oraz notebook `.ipynb`, w którym użytkownik może wykonać:

```python
from ipyniivue import NiiVue

nv = NiiVue()
nv.load_volumes([{"path": "derivatives/niivue/sub-demo_task-sim_desc-activity_overlay.nii.gz"}])
nv
```

Jeżeli mimo wszystko chcemy pokazać `ipyniivue` w aplikacji desktopowej, należy
uruchomić lokalny Jupyter Server jako proces potomny, otworzyć przygotowany
notebook albo stronę JupyterLab w `QWebEngineView`, przekazać token tylko do tego
widoku i zamykać kernel po zamknięciu panelu. Taki tryb powinien być oznaczony
jako eksperymentalny, ponieważ komplikuje odtwarzalność środowiska i obsługę
błędów względem bezpośredniego HTML NiiVue.

## Tryb awaryjny i eksport

Dla środowisk bez WebGL lub Qt WebEngine należy utrzymać prostszy tryb SVG/Canvas
opisany w `brain_viewer/brain_viewer.md`. Ten tryb powinien pozostać lekki,
działać offline i pozwalać na eksport PNG z czterech rzutów dydaktycznych.

## Kryteria akceptacji przyszłej implementacji desktopowej

- Widget desktopowy używa PySide6/Qt, a nie `tkinter`.
- Widok desktopowy używa tego samego kontraktu danych co widok webowy.
- Komunikaty błędów są po polsku.
- Brak ukrytego dostępu JavaScript do dowolnych ścieżek lokalnych.
- Dane surowe nie są modyfikowane; nakładki są odczytywane jako artefakty
  pochodne.
- Testy statyczne obejmują importy Qt, brak `tkinter` i walidację ścieżek.
