# Wymagania stosowania standardu BIDS dla danych obrazowych mózgu

Ten dokument określa wymagania dotyczące organizacji, nazewnictwa, metadanych i walidacji plików związanych z przetwarzaniem danych obrazowych mózgu zgodnie ze standardem **BIDS** — **Brain Imaging Data Structure**.

Źródło główne: https://bids-specification.readthedocs.io/en/stable/

Dokument jest przeznaczony dla osób i agentów AI pracujących nad repozytorium, w którym przetwarzane są dane neuroobrazowe, w szczególności MRI, fMRI, DWI, mapy pola oraz pochodne wynikające z pipeline'ów analitycznych.

---

## 1. Cel stosowania BIDS

BIDS jest standardem organizacji danych neuroobrazowych i behawioralnych. Jego głównym celem jest zapewnienie:

- jednoznacznej struktury katalogów;
- spójnego nazewnictwa plików;
- jawnego opisu metadanych;
- interoperacyjności z narzędziami neuroinformatycznymi;
- automatycznej walidacji zbiorów danych;
- replikowalności analiz;
- łatwego oddzielenia danych surowych, danych źródłowych i danych pochodnych.

W tym projekcie wszystkie dane obrazowe mózgu, które mają być przechowywane, analizowane, przetwarzane lub udostępniane, powinny być organizowane zgodnie z BIDS, o ile nie istnieje wyraźnie udokumentowany powód odstępstwa.

---

## 2. Zakres danych objętych standardem

Dla danych obrazowych mózgu szczególnie istotne są następujące typy danych BIDS:

| Typ danych | Katalog | Przykłady |
|---|---|---|
| Obrazy anatomiczne | `anat/` | `T1w`, `T2w`, `FLAIR`, `PDw`, `T1map`, `T2map` |
| Obrazy funkcjonalne | `func/` | `bold`, `sbref`, pliki zdarzeń `events.tsv` |
| Obrazowanie dyfuzyjne | `dwi/` | `dwi.nii.gz`, `dwi.bval`, `dwi.bvec` |
| Mapy pola | `fmap/` | `phasediff`, `magnitude1`, `epi` |
| Perfuzja | `perf/` | ASL i inne dane perfuzyjne |
| Spektroskopia MR | `mrs/` | dane spektroskopii rezonansu magnetycznego |
| Dane pochodne | `derivatives/` | wyniki preprocessingu, maski, segmentacje, rejestracje, mapy cech |

Jeżeli projekt przetwarza tylko podzbiór tych modalności, należy stosować wyłącznie katalogi odpowiadające rzeczywiście występującym danym. Nie należy tworzyć pustych katalogów BIDS tylko „na przyszłość”.

---

## 3. Podstawowa struktura katalogów

Minimalna struktura surowego zbioru BIDS powinna wyglądać następująco:

```text
bids_dataset/
├── dataset_description.json
├── participants.tsv
├── README
├── CHANGES
├── sub-001/
│   ├── anat/
│   │   ├── sub-001_T1w.nii.gz
│   │   └── sub-001_T1w.json
│   ├── func/
│   │   ├── sub-001_task-rest_bold.nii.gz
│   │   ├── sub-001_task-rest_bold.json
│   │   └── sub-001_task-rest_events.tsv
│   ├── dwi/
│   │   ├── sub-001_dwi.nii.gz
│   │   ├── sub-001_dwi.bval
│   │   └── sub-001_dwi.bvec
│   └── fmap/
│       ├── sub-001_phasediff.nii.gz
│       ├── sub-001_phasediff.json
│       └── sub-001_magnitude1.nii.gz
└── derivatives/
```

Dla badań z wieloma sesjami należy stosować poziom `ses-<label>`:

```text
bids_dataset/
├── dataset_description.json
├── participants.tsv
├── sub-001/
│   ├── ses-baseline/
│   │   ├── anat/
│   │   ├── func/
│   │   └── dwi/
│   └── ses-followup/
│       ├── anat/
│       ├── func/
│       └── dwi/
└── derivatives/
```

Jeżeli co najmniej jeden uczestnik ma wiele sesji, poziom `ses-*` powinien być stosowany konsekwentnie dla wszystkich uczestników, jeżeli struktura badania to uzasadnia.

---

## 4. Katalogi główne

### 4.1. `dataset_description.json`

Każdy zbiór BIDS musi zawierać plik `dataset_description.json` w katalogu głównym.

Minimalny przykład:

```json
{
  "Name": "Neuroimaging dataset",
  "BIDSVersion": "1.11.1",
  "DatasetType": "raw",
  "Authors": [
    "Research Team"
  ]
}
```

Dla zbiorów pochodnych należy stosować:

```json
{
  "Name": "Preprocessed neuroimaging dataset",
  "BIDSVersion": "1.11.1",
  "DatasetType": "derivative",
  "GeneratedBy": [
    {
      "Name": "custom-preprocessing-pipeline",
      "Version": "1.0.0",
      "CodeURL": "https://example.org/repository"
    }
  ],
  "SourceDatasets": [
    {
      "URL": "../"
    }
  ]
}
```

Wymagania projektowe:

- `dataset_description.json` musi być obecny w każdym niezależnym zbiorze BIDS;
- każdy pipeline w `derivatives/` powinien mieć własny `dataset_description.json`;
- pole `BIDSVersion` powinno odpowiadać wersji standardu używanej w projekcie;
- dla danych pochodnych należy zapisać informację o narzędziu lub pipeline, który je wygenerował.

---

### 4.2. `participants.tsv`

Plik `participants.tsv` opisuje uczestników badania. Powinien znajdować się w katalogu głównym zbioru.

Przykład:

```text
participant_id	age	sex	group
sub-001	24	M	control
sub-002	31	F clinical
```

Wymagania:

- pierwsza kolumna powinna identyfikować uczestnika jako `participant_id`;
- identyfikatory muszą odpowiadać katalogom `sub-*`;
- wartości brakujące należy kodować jako `n/a`;
- plik musi być tabulatorem rozdzielanym TSV, nie CSV;
- dane identyfikujące uczestników muszą być usunięte lub zanonimizowane.

Zalecany plik towarzyszący `participants.json`:

```json
{
  "participant_id": {
    "Description": "Unique participant identifier"
  },
  "age": {
    "Description": "Age at the time of scanning",
    "Units": "years"
  },
  "sex": {
    "Description": "Biological sex",
    "Levels": {
      "M": "male",
      "F": "female",
      "O": "other"
    }
  },
  "group": {
    "Description": "Experimental or clinical group"
  }
}
```

---

### 4.3. `README`

Plik `README` powinien opisywać:

- cel zbioru danych;
- ogólną procedurę badawczą;
- typy pozyskanych danych;
- sposób anonimizacji;
- sposób cytowania danych;
- ograniczenia użycia danych;
- informacje kontaktowe zespołu lub opiekuna danych.

---

### 4.4. `CHANGES`

Plik `CHANGES` powinien dokumentować historię zmian w zbiorze danych.

Przykład:

```text
1.0.0 2026-05-29
- Initial BIDS conversion.
- Added anatomical T1w and resting-state BOLD data.
- Added dataset_description.json and participants.tsv.
```

---

## 5. Zasady nazewnictwa plików

Nazwy plików BIDS składają się z encji, sufiksu i rozszerzenia.

Ogólny wzorzec:

```text
sub-<label>[_ses-<label>][_task-<label>][_acq-<label>][_run-<index>][_echo-<index>][_part-<label>]_<suffix>.<extension>
```

Przykłady:

```text
sub-001_T1w.nii.gz
sub-001_ses-baseline_T1w.nii.gz
sub-001_task-rest_bold.nii.gz
sub-001_task-nback_run-01_bold.nii.gz
sub-001_acq-highres_T2w.nii.gz
sub-001_dir-AP_epi.nii.gz
sub-001_dwi.nii.gz
```

Wymagania:

- identyfikator uczestnika musi zaczynać się od `sub-`;
- identyfikator sesji musi zaczynać się od `ses-`;
- encje muszą występować w kolejności określonej przez standard BIDS;
- sufiks musi odpowiadać typowi danych, np. `T1w`, `bold`, `dwi`;
- nie należy używać spacji, polskich znaków, znaków specjalnych ani opisowych nazw poza encjami BIDS;
- etykiety powinny być alfanumeryczne;
- należy unikać nazw różniących się tylko wielkością liter;
- nazwa pliku danych i odpowiadającego mu pliku JSON musi być taka sama poza rozszerzeniem.

---

## 6. Format plików obrazowych

Wszystkie dane obrazowe powinny być przechowywane w formacie NIfTI:

```text
.nii
.nii.gz
```

W projekcie preferowany jest format skompresowany:

```text
.nii.gz
```

Wymagania:

- dane DICOM należy traktować jako dane źródłowe, nie jako surowe dane BIDS;
- DICOM-y należy przechowywać poza właściwym raw BIDS, np. w `sourcedata/dicoms/`;
- konwersję DICOM → NIfTI należy wykonywać narzędziem zachowującym możliwie dużo metadanych, np. `dcm2niix`;
- każdy plik NIfTI wymagający metadanych powinien mieć odpowiadający plik sidecar JSON;
- orientacja, rozdzielczość, czas repetycji, czas echa, kolejność warstw i parametry akwizycji powinny być zachowane w metadanych, jeśli są dostępne.

---

## 7. Pliki JSON sidecar

Pliki sidecar JSON służą do przechowywania metadanych opisujących akwizycję i interpretację danych.

Przykład dla danych anatomicznych:

```json
{
  "Manufacturer": "Siemens",
  "ManufacturersModelName": "Prisma",
  "MagneticFieldStrength": 3,
  "MRAcquisitionType": "3D",
  "RepetitionTime": 2.3,
  "EchoTime": 0.00298,
  "FlipAngle": 9
}
```

Przykład dla danych fMRI:

```json
{
  "TaskName": "rest",
  "RepetitionTime": 2.0,
  "EchoTime": 0.030,
  "SliceTiming": [0.0, 1.0, 0.1, 1.1],
  "PhaseEncodingDirection": "j-",
  "EffectiveEchoSpacing": 0.00058
}
```

Wymagania:

- plik JSON musi mieć tę samą nazwę bazową co odpowiadający plik danych;
- metadane powinny pochodzić z DICOM lub dokumentacji protokołu;
- wartości liczbowe powinny używać kropki jako separatora dziesiętnego;
- jednostki powinny być zgodne z BIDS, zwykle SI;
- czas powinien być podawany w sekundach, częstotliwość w hercach;
- brak metadanych nie powinien być ukrywany przez arbitralne wartości domyślne.

---

## 8. Zasada dziedziczenia metadanych

BIDS pozwala umieszczać metadane na różnych poziomach katalogów. Plik JSON położony wyżej w hierarchii może opisywać wiele plików niżej, jeżeli spełnia reguły dopasowania BIDS.

Przykład:

```text
bids_dataset/
├── task-rest_bold.json
└── sub-001/
    └── func/
        ├── sub-001_task-rest_run-01_bold.nii.gz
        └── sub-001_task-rest_run-02_bold.nii.gz
```

Jeżeli oba przebiegi `run-01` i `run-02` mają takie same parametry akwizycji, można przechować wspólne metadane w `task-rest_bold.json`.

Wymagania projektowe:

- stosuj dziedziczenie tylko wtedy, gdy metadane rzeczywiście są identyczne;
- nie nadpisuj tych samych pól w wielu miejscach bez potrzeby;
- w razie wątpliwości preferuj jawny plik JSON przy konkretnym pliku danych;
- unikaj układu, w którym wiele plików JSON na tym samym poziomie może opisywać ten sam plik danych.

---

## 9. Dane anatomiczne `anat/`

Katalog `anat/` zawiera strukturalne obrazy mózgu.

Typowe sufiksy:

```text
T1w
T2w
FLAIR
PDw
T2starw
UNIT1
T1map
T2map
R1map
R2map
R2starmap
```

Przykłady:

```text
sub-001/anat/sub-001_T1w.nii.gz
sub-001/anat/sub-001_T1w.json
sub-001/anat/sub-001_acq-highres_T2w.nii.gz
sub-001/anat/sub-001_FLAIR.nii.gz
```

Wymagania:

- obrazy T1-zależne zapisuj z sufiksem `T1w`;
- obrazy T2-zależne zapisuj z sufiksem `T2w`;
- FLAIR zapisuj jako `FLAIR`;
- parametryczne mapy ilościowe zapisuj odpowiednim sufiksem, np. `T1map`, `T2map`, `R1map`;
- nie używaj własnych sufiksów typu `structural`, `mprage`, `brain`, jeśli istnieje sufiks BIDS;
- warianty akwizycji opisuj encją `acq-<label>`, np. `acq-highres`;
- kolejne powtórzenia zapisuj z encją `run-<index>`.

---

## 10. Dane funkcjonalne `func/`

Katalog `func/` zawiera dane fMRI, zwykle BOLD.

Przykłady:

```text
sub-001/func/sub-001_task-rest_bold.nii.gz
sub-001/func/sub-001_task-rest_bold.json
sub-001/func/sub-001_task-rest_events.tsv
sub-001/func/sub-001_task-nback_run-01_bold.nii.gz
sub-001/func/sub-001_task-nback_run-01_events.tsv
```

Wymagania:

- dane BOLD muszą mieć sufiks `bold`;
- każda akwizycja funkcjonalna musi zawierać encję `task-<label>`;
- dla resting-state należy stosować np. `task-rest`;
- nazwa zadania w pliku JSON powinna odpowiadać encji `task-*`;
- kolejne powtórzenia tego samego zadania zapisuj jako `run-01`, `run-02`;
- zdarzenia eksperymentalne zapisuj w `events.tsv`;
- plik `events.tsv` powinien zawierać co najmniej kolumny `onset` i `duration`, jeśli opisuje zdarzenia czasowe;
- czasy w `events.tsv` powinny być liczone względem początku akwizycji.

Przykład `events.tsv`:

```text
onset	duration	trial_type	response_time	accuracy
0.0	2.0	fixation	n/a	n/a
2.0	1.5	target	0.534	1
5.0	1.5	distractor	0.712	0
```

Zalecany `events.json`:

```json
{
  "onset": {
    "Description": "Event onset relative to the beginning of the acquisition",
    "Units": "s"
  },
  "duration": {
    "Description": "Event duration",
    "Units": "s"
  },
  "trial_type": {
    "Description": "Type of experimental trial"
  },
  "response_time": {
    "Description": "Reaction time",
    "Units": "s"
  },
  "accuracy": {
    "Description": "Response correctness",
    "Levels": {
      "0": "incorrect",
      "1": "correct"
    }
  }
}
```

---

## 11. Dane dyfuzyjne `dwi/`

Katalog `dwi/` zawiera dane obrazowania dyfuzyjnego.

Minimalny zestaw:

```text
sub-001/dwi/sub-001_dwi.nii.gz
sub-001/dwi/sub-001_dwi.json
sub-001/dwi/sub-001_dwi.bval
sub-001/dwi/sub-001_dwi.bvec
```

Wymagania:

- plik obrazu musi mieć sufiks `dwi`;
- pliki `.bval` i `.bvec` muszą mieć tę samą nazwę bazową co plik `.nii.gz`;
- liczba wartości w `.bval` i kolumn w `.bvec` musi odpowiadać liczbie wolumenów w pliku DWI;
- kierunki dyfuzji muszą odpowiadać orientacji danych po konwersji;
- parametry akwizycji, w tym `PhaseEncodingDirection`, należy zapisać w JSON, jeśli są dostępne;
- jeżeli do korekcji zniekształceń używane są dane `fmap/`, powiązania powinny być opisane zgodnie ze standardem BIDS.

---

## 12. Mapy pola `fmap/`

Katalog `fmap/` zawiera dane służące do korekcji niejednorodności pola magnetycznego i zniekształceń EPI.

Przykłady:

```text
sub-001/fmap/sub-001_phasediff.nii.gz
sub-001/fmap/sub-001_phasediff.json
sub-001/fmap/sub-001_magnitude1.nii.gz
sub-001/fmap/sub-001_dir-AP_epi.nii.gz
sub-001/fmap/sub-001_dir-PA_epi.nii.gz
```

Wymagania:

- stosuj standardowe sufiksy BIDS, np. `phasediff`, `phase1`, `phase2`, `magnitude1`, `magnitude2`, `epi`;
- dla danych EPI o różnych kierunkach kodowania fazy stosuj encję `dir-<label>`, np. `dir-AP`, `dir-PA`;
- nie traktuj encji `dir-*` jako zamiennika metadanej `PhaseEncodingDirection`;
- w JSON należy zapisać parametry potrzebne do korekcji zniekształceń, jeśli są dostępne;
- powiązanie map pola z obrazami docelowymi powinno być jawne, np. przez właściwe pola metadanych.

---

## 13. Dane źródłowe `sourcedata/`

Dane przed harmonizacją, rekonstrukcją lub konwersją należy przechowywać w `sourcedata/`.

Przykład:

```text
bids_dataset/
├── sourcedata/
│   └── dicoms/
│       ├── sub-001/
│       └── sub-002/
├── sub-001/
├── sub-002/
└── dataset_description.json
```

Wymagania:

- DICOM-y nie powinny być mieszane z właściwym raw BIDS;
- dane źródłowe mogą mieć strukturę producenta lub ośrodka;
- jeżeli są przechowywane, muszą być zabezpieczone zgodnie z polityką danych osobowych;
- dane źródłowe nie powinny zawierać bezpośrednich identyfikatorów pacjenta lub uczestnika;
- konwersja z `sourcedata/` do raw BIDS powinna być skryptowalna i udokumentowana.

---

## 14. Dane pochodne `derivatives/`

Wyniki preprocessingu i analiz należy zapisywać w `derivatives/`.

Przykład:

```text
bids_dataset/
└── derivatives/
    └── fmriprep/
        ├── dataset_description.json
        └── sub-001/
            ├── anat/
            │   ├── sub-001_desc-preproc_T1w.nii.gz
            │   ├── sub-001_desc-brain_mask.nii.gz
            │   └── sub-001_dseg.nii.gz
            └── func/
                ├── sub-001_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
                ├── sub-001_task-rest_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz
                └── sub-001_task-rest_desc-confounds_timeseries.tsv
```

Wymagania:

- każdy pipeline w `derivatives/` powinien mieć osobny katalog;
- nazwa katalogu pipeline powinna odpowiadać nazwie narzędzia lub pipeline;
- każdy zbiór pochodny powinien mieć własny `dataset_description.json`;
- dane pochodne powinny zachowywać encje źródłowe, jeśli są potrzebne do identyfikacji pochodzenia;
- przestrzeń odniesienia należy oznaczać encją `space-<label>`, np. `space-MNI152NLin2009cAsym`;
- wariant przetwarzania opisuj encją `desc-<label>`;
- rozdzielczość opisuj encją `res-<label>`, jeśli istnieje wiele rozdzielczości;
- gęstość powierzchniową opisuj encją `den-<label>`, jeśli dotyczy;
- maski powinny używać sufiksu `mask`;
- segmentacje dyskretne powinny używać sufiksu `dseg`;
- pliki pochodne muszą zawierać metadane potrzebne do interpretacji wyniku.

---

## 15. Maski, segmentacje i atlasy

### 15.1. Maski

Przykłady:

```text
sub-001_desc-brain_mask.nii.gz
sub-001_task-rest_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz
```

Wymagania:

- maski binarne zapisuj z sufiksem `mask`;
- typ maski opisuj encją `desc-<label>`, np. `desc-brain`, `desc-lesion`, `desc-roi`;
- przestrzeń maski musi być zgodna z przestrzenią danych, do których maska jest stosowana;
- jeżeli maska jest w przestrzeni standardowej, użyj encji `space-*`.

### 15.2. Segmentacje

Przykłady:

```text
sub-001_dseg.nii.gz
sub-001_desc-tissue_probseg.nii.gz
```

Wymagania:

- segmentacje dyskretne zapisuj jako `dseg`;
- segmentacje probabilistyczne zapisuj jako `probseg`;
- etykiety klas powinny być opisane w pliku TSV lub JSON;
- nie należy pozostawiać segmentacji bez opisu znaczenia wartości wokseli.

### 15.3. Atlasy

Jeżeli wykorzystywany jest atlas:

- podaj nazwę atlasu;
- podaj wersję atlasu, jeśli jest dostępna;
- podaj przestrzeń odniesienia;
- opisz etykiety regionów;
- zapisz sposób transformacji atlasu do przestrzeni danych;
- nie mieszaj etykiet atlasowych z etykietami własnymi bez jawnego mapowania.

---

## 16. Dane tabelaryczne TSV

Pliki tabelaryczne muszą być zapisywane jako TSV, czyli tekst rozdzielany tabulatorami.

Wymagania:

- rozszerzenie: `.tsv`;
- separator: prawdziwy tabulator, nie spacje;
- kodowanie: UTF-8;
- separator dziesiętny: kropka;
- wartości brakujące: `n/a`;
- nagłówki kolumn powinny być w `snake_case`;
- nazwy kolumn nie mogą być puste ani zduplikowane;
- pliki TSV powinny mieć słownik danych w pliku JSON, jeżeli kolumny nie są oczywiste.

Przykład:

```text
onset	duration	trial_type
0.0	2.0	fixation
2.0	1.5	target
```

---

## 17. Jednostki i czas

Wymagania:

- stosuj jednostki SI, jeśli standard BIDS nie wymaga inaczej;
- czas trwania i znaczniki czasu podawaj w sekundach;
- częstotliwość podawaj w hercach;
- jednostki arbitralne zapisuj jako `"arbitrary"`;
- jednostki opisuj w JSON, jeśli nie są oczywiste;
- daty i godziny zapisuj w formacie zgodnym z BIDS, jeżeli muszą być zachowane;
- dla ochrony prywatności daty mogą być przesunięte, ale przesunięcie musi zachować odstępy czasowe w obrębie uczestnika w badaniach podłużnych.

---

## 18. Anonimizacja i bezpieczeństwo danych

Dane obrazowe mózgu mogą zawierać informacje wrażliwe. Dotyczy to szczególnie DICOM, nagłówków NIfTI, obrazów twarzy w T1w oraz metadanych skanowania.

Wymagania:

- usuń identyfikatory osobowe z DICOM przed udostępnieniem;
- sprawdź metadane JSON pod kątem pól identyfikujących osobę;
- rozważ defacing obrazów anatomicznych, jeśli dane mają być udostępniane;
- nie zapisuj imion, nazwisk, numerów dokumentacji medycznej ani dokładnych dat urodzenia;
- identyfikatory `sub-*` muszą być pseudonimami;
- tabela mapująca identyfikatory badawcze na osoby, jeśli istnieje, nie może znajdować się w repozytorium;
- daty badań należy usuwać lub przesuwać zgodnie z procedurą ochrony prywatności;
- w danych publicznych unikaj nadmiernej dokładności wieku, jeśli mogłaby zwiększyć ryzyko reidentyfikacji.

---

## 19. Walidacja BIDS

Każdy zbiór danych powinien być walidowany narzędziem BIDS Validator.

Zalecane narzędzia:

```bash
bids-validator /path/to/bids_dataset
```

lub przez `npx`:

```bash
npx bids-validator /path/to/bids_dataset
```

Wymagania projektowe:

- walidację należy uruchamiać po każdej większej zmianie struktury danych;
- błędy walidacji muszą zostać naprawione albo jawnie opisane;
- ostrzeżenia powinny być przeanalizowane, nie ignorowane;
- wynik walidacji można zapisać w katalogu raportów lub jako artefakt CI;
- nowe dane nie powinny być uznane za gotowe, dopóki nie przejdą walidacji BIDS albo nie mają udokumentowanego odstępstwa.

---

## 20. Zasady dla agentów AI

Agent AI pracujący z danymi neuroobrazowymi musi przestrzegać poniższych zasad:

1. Nie zmieniaj nazw plików obrazowych poza konwencją BIDS.
2. Nie przenoś danych między `sourcedata/`, raw BIDS i `derivatives/` bez jasnego powodu.
3. Nie mieszaj danych surowych z wynikami preprocessingu.
4. Nie twórz własnych sufiksów, jeśli istnieje sufiks BIDS.
5. Nie usuwaj plików `.json`, `.bval`, `.bvec`, `.tsv` powiązanych z obrazami.
6. Nie zakładaj, że brak JSON oznacza brak wymaganych metadanych.
7. Nie nadpisuj danych surowych wynikami przetwarzania.
8. Nie zapisuj masek, segmentacji ani obrazów znormalizowanych w katalogach raw.
9. Przy generowaniu danych pochodnych zachowuj encje źródłowe potrzebne do identyfikacji pliku.
10. Przy zmianach struktury danych dodaj lub zaktualizuj dokumentację.
11. Po zmianach uruchom BIDS Validator, jeśli środowisko na to pozwala.
12. Jeśli walidacja nie może zostać uruchomiona, opisz przyczynę i wskaż, co należy sprawdzić ręcznie.

---

## 21. Zalecana struktura w repozytorium projektu

Jeżeli repozytorium zawiera kod i ma odwoływać się do danych BIDS, zalecana struktura jest następująca:

```text
project/
├── README.md
├── AGENTS.md
├── docs/
│   └── bids_brain_imaging_requirements.md
├── configs/
├── scripts/
│   ├── convert_dicoms_to_bids.py
│   ├── validate_bids_dataset.py
│   └── run_preprocessing.py
├── src/
├── tests/
└── data/
    ├── README.md
    ├── sourcedata/
    ├── raw_bids/
    └── derivatives/
```

Jeżeli dane są duże lub wrażliwe, katalog `data/` nie powinien być commitowany do Git. W repozytorium należy zostawić wyłącznie instrukcje, konfiguracje, skrypty i ewentualnie małe dane testowe.

---

## 22. Minimalna lista kontrolna zgodności BIDS

Przed uznaniem zbioru danych za poprawnie przygotowany sprawdź:

- [ ] Czy istnieje `dataset_description.json`?
- [ ] Czy istnieje `participants.tsv`?
- [ ] Czy identyfikatory uczestników w `participants.tsv` odpowiadają katalogom `sub-*`?
- [ ] Czy struktura `sub-*` i opcjonalnie `ses-*` jest konsekwentna?
- [ ] Czy pliki obrazowe są w formacie `.nii` lub `.nii.gz`?
- [ ] Czy dane DICOM znajdują się poza raw BIDS, np. w `sourcedata/`?
- [ ] Czy pliki mają poprawne encje i sufiksy BIDS?
- [ ] Czy pliki JSON mają te same nazwy bazowe co pliki obrazowe?
- [ ] Czy dane funkcjonalne mają encję `task-*`?
- [ ] Czy DWI ma odpowiadające pliki `.bval` i `.bvec`?
- [ ] Czy dane pochodne są zapisane w `derivatives/<pipeline-name>/`?
- [ ] Czy pipeline pochodny ma własny `dataset_description.json`?
- [ ] Czy maski, segmentacje i atlasy mają opis znaczenia wartości?
- [ ] Czy pliki TSV są tabulatorowe i zakodowane w UTF-8?
- [ ] Czy jednostki są jawnie określone, gdy są potrzebne?
- [ ] Czy dane zostały zanonimizowane?
- [ ] Czy zbiór przechodzi BIDS Validator?
- [ ] Czy odstępstwa od BIDS są udokumentowane?

---

## 23. Przykłady poprawnych i niepoprawnych nazw

### Poprawne

```text
sub-001/anat/sub-001_T1w.nii.gz
sub-001/anat/sub-001_acq-highres_T1w.nii.gz
sub-001/func/sub-001_task-rest_bold.nii.gz
sub-001/func/sub-001_task-nback_run-01_bold.nii.gz
sub-001/dwi/sub-001_dwi.nii.gz
sub-001/fmap/sub-001_dir-AP_epi.nii.gz
derivatives/fmriprep/sub-001/anat/sub-001_desc-preproc_T1w.nii.gz
```

### Niepoprawne

```text
subject1/T1.nii.gz
sub_001/anatomy/brain.nii
sub-001/func/resting_state.nii.gz
sub-001/dwi/diffusion_data.nii.gz
sub-001/anat/sub-001_mprage.nii.gz
derivatives/sub-001_preprocessed.nii.gz
```

Powody niepoprawności:

- brak prefiksu `sub-`;
- niestandardowe katalogi, np. `anatomy` zamiast `anat`;
- brak encji `task-*` dla fMRI;
- niestandardowy sufiks zamiast `T1w`, `bold`, `dwi`;
- brak katalogu pipeline w `derivatives/`;
- brak możliwości automatycznej interpretacji przez narzędzia BIDS.

---

## 24. Reguła nadrzędna

Każdy plik danych obrazowych mózgu powinien odpowiadać na pytania:

> Kogo dotyczy plik?  
> Z jakiej sesji pochodzi?  
> Jaką modalność reprezentuje?  
> Jak został pozyskany?  
> Jakie ma metadane akwizycji?  
> Czy jest plikiem surowym, źródłowym czy pochodnym?  
> Jakim pipeline'em został wygenerowany, jeśli jest pochodny?  
> Czy jego nazwa i lokalizacja są zgodne z BIDS?

Jeżeli odpowiedź na te pytania nie wynika ze struktury katalogów, nazwy pliku i metadanych, organizacja danych wymaga poprawy.
