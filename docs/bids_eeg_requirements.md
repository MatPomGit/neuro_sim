# Wymagania stosowania standardu BIDS dla danych EEG

Ten dokument określa wymagania dotyczące organizacji, nazewnictwa, metadanych, walidacji i replikowalności danych EEG zgodnie ze standardem **EEG-BIDS**, czyli częścią specyfikacji **Brain Imaging Data Structure (BIDS)** dla elektroencefalografii.

Źródło główne: https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html

Dokument jest przeznaczony dla osób i agentów AI pracujących nad repozytorium, w którym przetwarzane są dane EEG, dane behawioralne zsynchronizowane z EEG, dane pomocnicze, pozycje elektrod, znaczniki zdarzeń oraz dane pochodne po preprocessingu i analizie.

---

## 1. Cel stosowania EEG-BIDS

EEG-BIDS jest rozszerzeniem standardu BIDS dla danych elektroencefalograficznych. Celem standardu jest zapewnienie:

- jednoznacznej struktury katalogów;
- spójnego nazewnictwa plików EEG;
- jawnego opisu metadanych akwizycji;
- opisu kanałów, elektrod, referencji i układu współrzędnych;
- poprawnej reprezentacji zdarzeń eksperymentalnych;
- zgodności z narzędziami neuroinformatycznymi;
- automatycznej walidacji danych;
- replikowalności eksperymentów EEG;
- oddzielenia danych surowych od danych pochodnych.

W tym projekcie wszystkie dane EEG przechowywane, analizowane, przetwarzane lub udostępniane powinny być organizowane zgodnie z EEG-BIDS, o ile nie istnieje wyraźnie udokumentowany powód odstępstwa.

---

## 2. Zakres danych objętych standardem

EEG-BIDS obejmuje w szczególności:

- surowe zapisy EEG;
- dane EOG, ECG, EMG, GSR, PPG, RESP, TRIG i inne kanały pomocnicze rejestrowane razem z EEG;
- znaczniki zdarzeń eksperymentalnych;
- informacje o kanałach;
- informacje o elektrodach;
- układ współrzędnych elektrod;
- zdjęcia punktów anatomicznych lub fiducjali;
- dane behawioralne powiązane z eksperymentem;
- dane pochodne, np. dane po filtracji, epokowaniu, ICA, odrzucaniu artefaktów, analizie czasowo-częstotliwościowej, ERP lub klasyfikacji.

---

## 3. Podstawowa struktura katalogów

Minimalna struktura surowego zbioru EEG-BIDS:

```text
bids_eeg_dataset/
├── dataset_description.json
├── participants.tsv
├── README
├── CHANGES
├── sub-001/
│   └── eeg/
│       ├── sub-001_task-rest_eeg.edf
│       ├── sub-001_task-rest_eeg.json
│       ├── sub-001_task-rest_channels.tsv
│       ├── sub-001_task-rest_events.tsv
│       ├── sub-001_electrodes.tsv
│       └── sub-001_coordsystem.json
└── derivatives/
```

Dla wielu sesji należy stosować poziom `ses-*`:

```text
bids_eeg_dataset/
├── dataset_description.json
├── participants.tsv
├── sub-001/
│   ├── ses-baseline/
│   │   └── eeg/
│   │       ├── sub-001_ses-baseline_task-rest_eeg.vhdr
│   │       ├── sub-001_ses-baseline_task-rest_eeg.vmrk
│   │       ├── sub-001_ses-baseline_task-rest_eeg.eeg
│   │       ├── sub-001_ses-baseline_task-rest_eeg.json
│   │       ├── sub-001_ses-baseline_task-rest_channels.tsv
│   │       └── sub-001_ses-baseline_task-rest_events.tsv
│   └── ses-followup/
│       └── eeg/
└── derivatives/
```

Wymagania:

- każdy uczestnik musi mieć katalog `sub-<label>`;
- jeżeli stosowane są sesje, każda sesja musi mieć katalog `ses-<label>`;
- dane EEG muszą znajdować się w katalogu `eeg/`;
- dane pochodne muszą znajdować się w `derivatives/<pipeline-name>/`;
- danych surowych nie wolno nadpisywać wynikami preprocessingu.

---

## 4. Pliki główne zbioru danych

### 4.1. `dataset_description.json`

Każdy zbiór BIDS musi zawierać `dataset_description.json`.

Minimalny przykład dla danych surowych:

```json
{
  "Name": "EEG dataset",
  "BIDSVersion": "1.11.1",
  "DatasetType": "raw",
  "Authors": [
    "Research Team"
  ]
}
```

Przykład dla danych pochodnych:

```json
{
  "Name": "Preprocessed EEG dataset",
  "BIDSVersion": "1.11.1",
  "DatasetType": "derivative",
  "GeneratedBy": [
    {
      "Name": "custom-eeg-preprocessing-pipeline",
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

Wymagania:

- `dataset_description.json` musi być obecny w katalogu głównym;
- każdy pipeline w `derivatives/` powinien mieć własny `dataset_description.json`;
- `BIDSVersion` powinno odpowiadać wersji standardu stosowanej w projekcie;
- dla danych pochodnych należy zapisać, czym zostały wygenerowane.

---

### 4.2. `participants.tsv`

Plik `participants.tsv` opisuje uczestników.

Przykład:

```text
participant_id	age	sex	group
sub-001	24	F	control
sub-002	31	M	clinical
```

Wymagania:

- pierwszą kolumną powinno być `participant_id`;
- wartości `participant_id` muszą odpowiadać katalogom `sub-*`;
- wartości brakujące zapisuj jako `n/a`;
- plik musi być TSV, nie CSV;
- dane osobowe muszą być zanonimizowane;
- nie zapisuj imienia, nazwiska, numeru dokumentacji medycznej ani dokładnej daty urodzenia.

Zalecany plik `participants.json`:

```json
{
  "participant_id": {
    "Description": "Unique participant identifier"
  },
  "age": {
    "Description": "Age at the time of EEG recording",
    "Units": "years"
  },
  "sex": {
    "Description": "Biological sex",
    "Levels": {
      "F": "female",
      "M": "male",
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

Plik `README` powinien zawierać:

- ogólny opis badania;
- typ eksperymentu EEG;
- rodzaj aparatury EEG;
- liczbę uczestników;
- liczbę kanałów;
- schemat elektrod;
- opis warunków eksperymentalnych;
- opis synchronizacji zdarzeń;
- informacje o anonimizacji;
- informacje o sposobie cytowania danych;
- ograniczenia użycia danych.

---

### 4.4. `CHANGES`

Plik `CHANGES` powinien dokumentować wersje zbioru danych.

Przykład:

```text
1.0.0 2026-05-29
- Initial EEG-BIDS conversion.
- Added resting-state EEG data.
- Added channels.tsv, events.tsv and eeg.json files.
```

---

## 5. Zasady nazewnictwa plików EEG

Ogólny wzorzec nazewnictwa danych EEG:

```text
sub-<label>[_ses-<label>]_task-<label>[_acq-<label>][_run-<index>]_eeg.<extension>
```

Przykłady:

```text
sub-001_task-rest_eeg.edf
sub-001_task-eyesopen_run-01_eeg.vhdr
sub-001_task-eyesopen_run-01_eeg.vmrk
sub-001_task-eyesopen_run-01_eeg.eeg
sub-001_ses-baseline_task-oddball_run-02_eeg.set
sub-001_ses-baseline_task-rest_channels.tsv
sub-001_ses-baseline_task-rest_events.tsv
```

Wymagania:

- identyfikator uczestnika musi zaczynać się od `sub-`;
- identyfikator sesji musi zaczynać się od `ses-`, jeśli występuje;
- każda rejestracja EEG musi mieć encję `task-<label>`;
- kolejne powtórzenia tego samego zadania oznaczaj jako `run-01`, `run-02`;
- warianty akwizycji oznaczaj jako `acq-<label>`;
- plik danych musi mieć sufiks `_eeg`;
- powiązane pliki JSON, TSV i pliki formatu BrainVision muszą mieć zgodną nazwę bazową;
- nie używaj spacji, polskich znaków ani opisowych nazw poza encjami BIDS.

---

## 6. Dozwolone formaty danych EEG

EEG-BIDS dopuszcza kilka formatów surowych danych EEG.

Dopuszczalne formaty:

| Format | Rozszerzenia | Uwagi |
|---|---|---|
| European Data Format | `.edf` | pojedynczy plik; `.EDF` wielkimi literami nie powinno być używane |
| BrainVision Core Data Format | `.vhdr`, `.vmrk`, `.eeg` | trzy pliki tworzące jeden zapis |
| EEGLAB | `.set`, opcjonalnie `.fdt` | format powszechny w analizach MATLAB/EEGLAB |
| BioSemi Data Format | `.bdf` | pojedynczy plik; `.BDF` wielkimi literami nie powinno być używane |

Preferowane formaty projektowe:

1. BrainVision (`.vhdr`, `.vmrk`, `.eeg`) — preferowany dla danych z markerami i rozbudowanymi metadanymi.
2. EDF (`.edf`) — preferowany jako prosty format wymiany.
3. EEGLAB (`.set`, `.fdt`) — dopuszczalny, gdy pipeline bazuje na EEGLAB lub MNE.
4. BDF (`.bdf`) — dopuszczalny szczególnie dla systemów BioSemi.

Wymagania:

- nie zapisuj danych EEG jako własnych plików `.csv`, `.txt`, `.npy` w raw BIDS;
- pliki konwertowane z formatu producenta powinny zachować markery, częstotliwość próbkowania i nazwy kanałów;
- oryginalne pliki producenta można przechowywać w `sourcedata/`, jeśli są potrzebne;
- konwersja do EEG-BIDS powinna być skryptowalna i udokumentowana.

---

## 7. Plik `*_eeg.json`

Każdy zapis EEG powinien mieć plik sidecar JSON z metadanymi akwizycji.

Przykład:

```json
{
  "TaskName": "rest",
  "Manufacturer": "Brain Products",
  "ManufacturersModelName": "actiCHamp",
  "SoftwareVersions": "BrainVision Recorder 1.25",
  "EEGReference": "Cz",
  "EEGGround": "AFz",
  "EEGPlacementScheme": "10-20",
  "SamplingFrequency": 500,
  "PowerLineFrequency": 50,
  "RecordingDuration": 600,
  "RecordingType": "continuous",
  "EEGChannelCount": 64,
  "EOGChannelCount": 2,
  "ECGChannelCount": 0,
  "EMGChannelCount": 0,
  "TriggerChannelCount": 1,
  "SoftwareFilters": "n/a",
  "HardwareFilters": {
    "Anti-aliasing filter": {
      "half-amplitude cutoff (Hz)": 250,
      "Roll-off": "n/a"
    }
  }
}
```

Pola wymagane:

- `EEGReference`;
- `SamplingFrequency`;
- `PowerLineFrequency`;
- `SoftwareFilters`.

Pola zalecane:

- `TaskName`;
- `Manufacturer`;
- `ManufacturersModelName`;
- `SoftwareVersions`;
- `CapManufacturer`;
- `CapManufacturersModelName`;
- `EEGChannelCount`;
- `EOGChannelCount`;
- `ECGChannelCount`;
- `EMGChannelCount`;
- `MISCChannelCount`;
- `TriggerChannelCount`;
- `RecordingDuration`;
- `RecordingType`;
- `EEGGround`;
- `EEGPlacementScheme`;
- `HardwareFilters`;
- `SubjectArtefactDescription`;
- `InstitutionName`;
- `InstitutionAddress`.

Wymagania projektowe:

- `SamplingFrequency` zapisuj w Hz;
- `PowerLineFrequency` w Polsce zwykle wynosi `50`, ale nie wpisuj tej wartości automatycznie bez potwierdzenia;
- `RecordingType` powinno mieć jedną z wartości: `continuous`, `epoched`, `discontinuous`;
- `SoftwareFilters` i `HardwareFilters` muszą opisywać filtry, jeśli były zastosowane;
- jeżeli filtrów nie było albo informacja jest niedostępna, stosuj wartość zgodną z BIDS, np. `"n/a"`;
- `EEGReference` musi opisywać schemat referencji danych surowych;
- jeżeli różne kanały mają różne referencje, opisz je w `channels.tsv`.

---

## 8. Plik `*_channels.tsv`

Plik `*_channels.tsv` opisuje kanały zapisane w danych EEG.

Przykład:

```text
name	type	units	description	reference	low_cutoff	high_cutoff	notch	status	status_description
Fp1	EEG	uV	n/a	Cz	0.1	100	50	good	n/a
Fp2	EEG	uV	n/a	Cz	0.1	100	50	good	n/a
VEOG	VEOG	uV	vertical eye movement	VEOG-	0.1	100	50	good	n/a
HEOG	HEOG	uV	horizontal eye movement	HEOG-	0.1	100	50	good	n/a
TRIG	TRIG	V	trigger channel	n/a	n/a	n/a	n/a	good	n/a
```

Wymagane kolumny:

- `name`;
- `type`;
- `units`.

Zalecane kolumny:

- `description`;
- `sampling_frequency`;
- `reference`;
- `low_cutoff`;
- `high_cutoff`;
- `notch`;
- `status`;
- `status_description`.

Wymagania:

- kolumna `name` musi być pierwsza;
- wartości `name` muszą być unikalne;
- kolumna `type` musi być druga;
- typ kanału musi być zapisany wielkimi literami;
- kolumna `units` musi być trzecia;
- kanały powinny być zapisane w kolejności występowania w pliku EEG;
- uszkodzone lub odrzucone kanały oznaczaj jako `bad`;
- przy `status=bad` podaj przyczynę w `status_description`;
- pozycje elektrod nie powinny być zapisywane w `channels.tsv`, lecz w `electrodes.tsv`.

Typowe wartości `type`:

```text
EEG
EOG
HEOG
VEOG
ECG
EMG
TRIG
MISC
RESP
GSR
PPG
TEMP
AUDIO
EYEGAZE
PUPIL
REF
```

---

## 9. Plik `*_events.tsv`

Plik `*_events.tsv` opisuje zdarzenia eksperymentalne, bodźce, odpowiedzi uczestnika, markery i inne znaczniki czasowe.

Przykład:

```text
onset	duration	trial_type	value	response_time	accuracy
0.000	2.000	fixation	10	n/a	n/a
2.000	0.200	target	21	0.534	1
4.500	0.200	distractor	22	0.712	0
```

Wymagania:

- `onset` oznacza czas początku zdarzenia względem początku zapisu;
- `duration` oznacza czas trwania zdarzenia;
- czasy zapisuj w sekundach;
- wartości brakujące zapisuj jako `n/a`;
- `trial_type` powinien opisywać klasę zdarzenia;
- dodatkowe kolumny, np. `value`, `response_time`, `accuracy`, muszą być opisane w `events.json`;
- markerów nie wolno usuwać, jeśli są potrzebne do rekonstrukcji procedury eksperymentalnej;
- jeżeli zdarzenia są zapisane w pliku BrainVision `.vmrk`, należy sprawdzić zgodność `events.tsv` z markerami źródłowymi.

Zalecany `*_events.json`:

```json
{
  "onset": {
    "Description": "Event onset relative to the beginning of the EEG recording",
    "Units": "s"
  },
  "duration": {
    "Description": "Event duration",
    "Units": "s"
  },
  "trial_type": {
    "Description": "Type of experimental event"
  },
  "value": {
    "Description": "Original event marker value"
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

## 10. Plik `*_electrodes.tsv`

Plik `*_electrodes.tsv` opisuje fizyczne położenia elektrod.

Przykład:

```text
name	x	y	z	type	material	impedance
Fp1	-30.1	85.2	45.0	cup	Ag/AgCl	8.5
Fp2	30.4	85.0	45.2	cup	Ag/AgCl	7.9
Cz	0.0	0.0	100.0	cup	Ag/AgCl	5.1
```

Wymagane kolumny:

- `name`;
- `x`;
- `y`;
- `z`.

Zalecane kolumny:

- `type`;
- `material`;
- `impedance`.

Wymagania:

- `name` musi być pierwszą kolumną;
- `x`, `y`, `z` muszą być drugą, trzecią i czwartą kolumną;
- wartości `name` muszą być unikalne;
- impedancję zapisuj w `kOhm`;
- jeśli pozycja elektrody nie jest znana, stosuj `n/a`;
- `electrodes.tsv` nie powinien być duplikowany dla każdego runu, jeśli elektrody się nie zmieniały;
- jeśli elektrody zostały ponownie zakładane lub digitalizowane, rozważ użycie osobnej sesji albo encji `acq-*`.

---

## 11. Plik `*_coordsystem.json`

Jeżeli istnieje `*_electrodes.tsv`, należy dostarczyć odpowiadający plik `*_coordsystem.json`.

Przykład:

```json
{
  "EEGCoordinateSystem": "CapTrak",
  "EEGCoordinateUnits": "mm",
  "EEGCoordinateSystemDescription": "Electrode positions digitized using CapTrak.",
  "FiducialsDescription": "NAS, LPA and RPA were digitized before the EEG recording.",
  "FiducialsCoordinates": {
    "NAS": [0.0, 95.0, 0.0],
    "LPA": [-75.0, 0.0, 0.0],
    "RPA": [75.0, 0.0, 0.0]
  },
  "FiducialsCoordinateSystem": "CapTrak",
  "FiducialsCoordinateUnits": "mm"
}
```

Wymagania:

- `EEGCoordinateSystem` musi opisywać układ współrzędnych elektrod;
- `EEGCoordinateUnits` musi zawierać jednostki, np. `m`, `mm`, `cm` albo `n/a`;
- jeżeli stosujesz `"Other"`, dodaj opis w `EEGCoordinateSystemDescription`;
- jeżeli dostępne są fiducjale, zapisz `NAS`, `LPA`, `RPA`;
- jeżeli elektrody są mapowane na MRI, powiązanie powinno być opisane jawnie;
- nie mieszaj współrzędnych w różnych układach bez osobnego opisu.

---

## 12. Zdjęcia punktów anatomicznych i fiducjali

EEG-BIDS dopuszcza zdjęcia punktów anatomicznych lub fiducjali.

Przykłady:

```text
sub-001/eeg/sub-001_photo.jpg
sub-001/eeg/sub-001_acq-before_photo.png
sub-001/ses-baseline/eeg/sub-001_ses-baseline_photo.jpg
```

Wymagania:

- zdjęcia mogą zawierać dane identyfikujące, więc powinny być traktowane jako wrażliwe;
- przed udostępnieniem należy ocenić ryzyko identyfikacji osoby;
- jeśli zdjęcie nie jest konieczne dla analizy, nie należy go commitować do repozytorium;
- jeśli zdjęcie jest przechowywane, musi mieć opis celu i zakresu użycia.

---

## 13. Dane pomocnicze: `physio` i `stim`

Jeżeli razem z EEG zapisano dane fizjologiczne lub stymulacyjne, można stosować pliki `*_physio.tsv.gz` i `*_stim.tsv.gz` wraz z plikami JSON.

Przykłady:

```text
sub-001_task-oddball_recording-pulse_physio.tsv.gz
sub-001_task-oddball_recording-pulse_physio.json
sub-001_task-oddball_recording-trigger_stim.tsv.gz
sub-001_task-oddball_recording-trigger_stim.json
```

Wymagania:

- dane pomocnicze muszą być zsynchronizowane z zapisem EEG albo mieć opis przesunięcia czasowego;
- kolumny plików TSV muszą być opisane w JSON;
- częstotliwość próbkowania musi być jawnie zapisana;
- nie mieszaj danych pomocniczych z właściwym plikiem EEG, jeśli można je zapisać jako odrębny strumień.

---

## 14. Zasada dziedziczenia metadanych

BIDS pozwala umieszczać metadane na wyższym poziomie katalogów, jeśli dotyczą wielu plików.

Przykład:

```text
bids_eeg_dataset/
├── task-rest_eeg.json
└── sub-001/
    └── eeg/
        ├── sub-001_task-rest_run-01_eeg.edf
        └── sub-001_task-rest_run-02_eeg.edf
```

Wymagania:

- stosuj dziedziczenie tylko wtedy, gdy metadane są rzeczywiście identyczne;
- nie duplikuj `electrodes.tsv` i `coordsystem.json` dla każdego runu, jeśli pozycje elektrod się nie zmieniały;
- gdy elektrody, referencja, częstotliwość próbkowania lub filtracja różnią się między runami, zapisz osobne pliki metadanych;
- w razie wątpliwości preferuj jawny plik metadanych przy konkretnym zapisie.

---

## 15. Dane źródłowe `sourcedata/`

Oryginalne dane producenta, pliki eksportu z aparatury lub dane przed konwersją można przechowywać w `sourcedata/`.

Przykład:

```text
bids_eeg_dataset/
├── sourcedata/
│   └── eeg_original/
│       ├── sub-001/
│       └── sub-002/
├── sub-001/
├── sub-002/
└── dataset_description.json
```

Wymagania:

- `sourcedata/` nie jest miejscem na dane pochodne;
- pliki źródłowe powinny być zanonimizowane, jeżeli mają być przechowywane;
- konwersja z `sourcedata/` do EEG-BIDS powinna być skryptowalna;
- nie wolno mieszać oryginalnych eksportów producenta z właściwym katalogiem raw BIDS;
- jeżeli `sourcedata/` zawiera dane wrażliwe, nie commituj go do repozytorium Git.

---

## 16. Dane pochodne `derivatives/`

Wyniki preprocessingu i analiz EEG zapisuj w `derivatives/`.

Przykład:

```text
bids_eeg_dataset/
└── derivatives/
    └── eeg-preproc/
        ├── dataset_description.json
        └── sub-001/
            └── eeg/
                ├── sub-001_task-rest_desc-filtered_eeg.set
                ├── sub-001_task-rest_desc-cleaned_eeg.set
                ├── sub-001_task-rest_desc-ica_components.tsv
                ├── sub-001_task-rest_desc-badchannels_channels.tsv
                └── sub-001_task-rest_desc-preproc_eeg.json
```

Wymagania:

- każdy pipeline powinien mieć osobny katalog w `derivatives/`;
- każdy katalog pipeline powinien mieć własny `dataset_description.json`;
- nazwa pliku pochodnego powinna zachowywać encje źródłowe, np. `sub-*`, `ses-*`, `task-*`, `run-*`;
- wariant przetwarzania opisuj przez `desc-<label>`, np. `desc-filtered`, `desc-cleaned`, `desc-ica`;
- nie zapisuj danych przefiltrowanych, epokowanych lub oczyszczonych w katalogu raw;
- zapisuj parametry preprocessingu w JSON lub konfiguracji pipeline;
- zapisuj wersję kodu i środowiska, które wygenerowały dane pochodne.

---

## 17. Minimalne metadane preprocessingu EEG

Dla danych pochodnych należy zapisać co najmniej:

- nazwę pipeline;
- wersję pipeline;
- identyfikator commita Git;
- wersje bibliotek;
- częstotliwość próbkowania po preprocessingu;
- filtr górnoprzepustowy;
- filtr dolnoprzepustowy;
- filtr notch;
- metodę korekcji artefaktów;
- listę usuniętych lub oznaczonych kanałów;
- metodę rereferencji;
- parametry epokowania;
- kryteria odrzucania epok;
- informacje o ICA, jeśli była stosowana;
- liczbę epok przed i po odrzuceniu;
- opis interpolacji kanałów, jeśli była stosowana.

Przykład pliku metadanych pochodnych:

```json
{
  "Description": "Cleaned EEG data after filtering, bad channel detection and ICA artifact removal.",
  "SourceFile": "sub-001/eeg/sub-001_task-rest_eeg.vhdr",
  "SamplingFrequency": 500,
  "HighPassFilter": 0.5,
  "LowPassFilter": 40.0,
  "NotchFilter": 50,
  "Reference": "average",
  "BadChannels": ["Fp1"],
  "InterpolatedChannels": ["Fp1"],
  "ICA": {
    "Method": "fastica",
    "RejectedComponents": [0, 2],
    "Reason": "ocular artifacts"
  }
}
```

---

## 18. Jednostki i wartości brakujące

Wymagania:

- czas zapisuj w sekundach;
- częstotliwość zapisuj w Hz;
- napięcie najczęściej zapisuj jako `uV` albo `V`, zgodnie z faktycznymi danymi;
- impedancję zapisuj w `kOhm`;
- wartości brakujące zapisuj jako `n/a`;
- separator dziesiętny to kropka;
- pliki tabelaryczne zapisuj jako TSV w UTF-8.

---

## 19. Anonimizacja i bezpieczeństwo danych EEG

Dane EEG oraz metadane mogą zawierać informacje wrażliwe.

Wymagania:

- usuń dane osobowe z nagłówków plików EEG;
- sprawdź pliki `.vhdr`, `.vmrk`, `.edf`, `.bdf`, `.set` pod kątem identyfikatorów osoby;
- usuń imiona, nazwiska, numery pacjentów, dokładne daty urodzenia i inne identyfikatory;
- identyfikatory `sub-*` muszą być pseudonimami;
- tabela mapująca identyfikatory na osoby nie może znajdować się w repozytorium;
- zdjęcia punktów anatomicznych traktuj jako potencjalnie identyfikujące;
- daty badań przesuwaj lub usuwaj zgodnie z procedurą ochrony prywatności;
- dla danych klinicznych unikaj nadmiernej szczegółowości metadanych, jeżeli zwiększa ryzyko reidentyfikacji.

---

## 20. Walidacja EEG-BIDS

Każdy zbiór EEG-BIDS powinien być walidowany narzędziem BIDS Validator.

Przykład:

```bash
bids-validator /path/to/bids_eeg_dataset
```

albo:

```bash
npx bids-validator /path/to/bids_eeg_dataset
```

Wymagania projektowe:

- walidację uruchamiaj po każdej większej zmianie struktury danych;
- błędy walidacji muszą zostać naprawione albo jawnie opisane;
- ostrzeżenia należy przeanalizować, nie ignorować;
- wynik walidacji można zapisać jako artefakt CI;
- nowe dane nie powinny być uznane za gotowe, dopóki nie przejdą walidacji albo nie mają udokumentowanego odstępstwa.

---

## 21. Zasady dla agentów AI

Agent AI pracujący z danymi EEG musi przestrzegać poniższych zasad:

1. Nie zmieniaj nazw plików EEG poza konwencją BIDS.
2. Nie usuwaj plików `.json`, `.tsv`, `.vmrk`, `.vhdr`, `.fdt` powiązanych z zapisem EEG.
3. Nie zapisuj danych po preprocessingu w katalogu raw.
4. Nie nadpisuj danych surowych.
5. Nie twórz własnych sufiksów, jeśli istnieje sufiks BIDS.
6. Nie usuwaj markerów zdarzeń bez jawnego uzasadnienia.
7. Nie oznaczaj kanału jako `bad` bez zapisu powodu w `status_description`.
8. Nie interpoluj kanałów bez zapisu listy kanałów i metody interpolacji.
9. Nie stosuj filtrów bez zapisania parametrów.
10. Nie stosuj ICA bez zapisu metody i odrzuconych komponentów.
11. Nie zakładaj częstotliwości sieci energetycznej bez potwierdzenia.
12. Nie mieszaj pojęć kanału i elektrody.
13. Jeżeli istnieje `electrodes.tsv`, zapewnij `coordsystem.json`.
14. Po zmianach uruchom BIDS Validator, jeśli środowisko na to pozwala.
15. Jeżeli walidacja nie może zostać uruchomiona, opisz przyczynę i elementy wymagające ręcznego sprawdzenia.

---

## 22. Zalecana struktura w repozytorium projektu

Jeżeli repozytorium zawiera kod i ma odwoływać się do danych EEG-BIDS, zalecana struktura jest następująca:

```text
project/
├── README.md
├── AGENTS.md
├── docs/
│   ├── bids_brain_imaging_requirements.md
│   └── bids_eeg_requirements.md
├── configs/
├── scripts/
│   ├── convert_eeg_to_bids.py
│   ├── validate_bids_dataset.py
│   ├── run_eeg_preprocessing.py
│   └── export_eeg_derivatives.py
├── src/
├── tests/
└── data/
    ├── README.md
    ├── sourcedata/
    ├── raw_bids/
    └── derivatives/
```

Jeżeli dane są duże lub wrażliwe, katalog `data/` nie powinien być commitowany do Git. W repozytorium należy zostawić instrukcje, konfiguracje, skrypty i małe dane testowe.

---

## 23. Minimalna lista kontrolna zgodności EEG-BIDS

Przed uznaniem zbioru danych EEG za poprawnie przygotowany sprawdź:

- [ ] Czy istnieje `dataset_description.json`?
- [ ] Czy istnieje `participants.tsv`?
- [ ] Czy identyfikatory uczestników odpowiadają katalogom `sub-*`?
- [ ] Czy dane EEG są w katalogu `eeg/`?
- [ ] Czy każdy zapis EEG ma encję `task-*`?
- [ ] Czy format danych jest zgodny z EEG-BIDS: `.edf`, `.vhdr/.vmrk/.eeg`, `.set/.fdt` albo `.bdf`?
- [ ] Czy istnieje `*_eeg.json`?
- [ ] Czy `*_eeg.json` zawiera `EEGReference`, `SamplingFrequency`, `PowerLineFrequency`, `SoftwareFilters`?
- [ ] Czy istnieje `*_channels.tsv`?
- [ ] Czy `channels.tsv` zawiera `name`, `type`, `units`?
- [ ] Czy typy kanałów są zapisane wielkimi literami?
- [ ] Czy uszkodzone kanały mają `status=bad` i opis w `status_description`?
- [ ] Czy istnieje `events.tsv`, jeśli eksperyment zawiera zdarzenia?
- [ ] Czy czasy w `events.tsv` są w sekundach względem początku zapisu?
- [ ] Czy `electrodes.tsv` ma odpowiadający `coordsystem.json`?
- [ ] Czy jednostki są jawnie opisane?
- [ ] Czy dane zostały zanonimizowane?
- [ ] Czy dane pochodne są zapisane w `derivatives/<pipeline-name>/`?
- [ ] Czy dane pochodne mają metadane preprocessingu?
- [ ] Czy zbiór przechodzi BIDS Validator?
- [ ] Czy odstępstwa od EEG-BIDS są udokumentowane?

---

## 24. Przykłady poprawnych i niepoprawnych nazw

### Poprawne

```text
sub-001/eeg/sub-001_task-rest_eeg.edf
sub-001/eeg/sub-001_task-rest_eeg.json
sub-001/eeg/sub-001_task-rest_channels.tsv
sub-001/eeg/sub-001_task-rest_events.tsv
sub-001/eeg/sub-001_electrodes.tsv
sub-001/eeg/sub-001_coordsystem.json
sub-001/ses-baseline/eeg/sub-001_ses-baseline_task-oddball_run-01_eeg.vhdr
sub-001/ses-baseline/eeg/sub-001_ses-baseline_task-oddball_run-01_eeg.vmrk
sub-001/ses-baseline/eeg/sub-001_ses-baseline_task-oddball_run-01_eeg.eeg
```

### Niepoprawne

```text
subject1/eeg/rest.edf
sub_001/eeg/eeg_data.edf
sub-001/eeg/resting_state.csv
sub-001/eeg/sub-001_rest.edf
sub-001/eeg/sub-001_task-rest_data.edf
derivatives/sub-001_cleaned.set
```

Powody niepoprawności:

- brak prefiksu `sub-`;
- niepoprawny identyfikator uczestnika, np. `sub_001`;
- brak encji `task-*`;
- niestandardowy sufiks zamiast `_eeg`;
- niezalecany format danych surowych;
- brak katalogu pipeline w `derivatives/`.

---

## 25. Relacja EEG-BIDS do danych MRI i multimodalnych

Jeżeli EEG jest analizowane razem z MRI, fMRI lub danymi anatomicznymi:

- zachowuj wspólne identyfikatory `sub-*` i `ses-*`;
- dane MRI zapisuj w odpowiednich katalogach, np. `anat/`, `func/`, `dwi/`;
- dane EEG zapisuj w `eeg/`;
- pozycje elektrod i fiducjale mogą odnosić się do obrazu anatomicznego;
- powiązanie z MRI powinno być opisane w `coordsystem.json`;
- nie zapisuj plików MRI w katalogu `eeg/`;
- nie zapisuj plików EEG w katalogach neuroobrazowych MRI.

---

## 26. Reguła nadrzędna

Każdy plik EEG powinien pozwalać odpowiedzieć na pytania:

> Kogo dotyczy zapis?  
> Z jakiej sesji pochodzi?  
> Jakiego zadania dotyczy?  
> Jakim sprzętem został zarejestrowany?  
> Jaką miał częstotliwość próbkowania?  
> Jaka była referencja i masa?  
> Jakie kanały zostały zapisane?  
> Jakie zdarzenia wystąpiły i kiedy?  
> Gdzie znajdowały się elektrody?  
> Czy plik jest surowy, źródłowy czy pochodny?  
> Jakim pipeline'em został przetworzony, jeśli jest pochodny?  
> Czy struktura i nazwa są zgodne z EEG-BIDS?

Jeżeli odpowiedź na te pytania nie wynika ze struktury katalogów, nazwy pliku i metadanych, organizacja danych wymaga poprawy.
