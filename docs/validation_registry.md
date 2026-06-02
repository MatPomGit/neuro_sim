# Rejestr walidacji benchmarków

Ten dokument porządkuje minimalny rejestr benchmarków używanych do walidacji
technicznej i jakościowej. Źródłem prawdy dla poziomu, źródła, zakresu i
ograniczeń pozostaje `data/validation/benchmark_metadata.json`; poniższa tabela
uzupełnia ten opis o oczekiwany efekt, tolerancję oraz bieżący status.

| Benchmark | Poziom | Źródło | Oczekiwany efekt | Tolerancja | Status |
| --- | --- | --- | --- | --- | --- |
| `eeg` | `synthetic` | Syntetyczny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; nie pochodzi z danych uczestników. | Raport zachowuje poprawny kształt krótkiego sygnału EEG dla kanałów Cz i Pz oraz umożliwia podstawowe porównania amplitudy bez interpretacji klinicznej. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Aktywny benchmark edukacyjno-techniczny; nie jest benchmarkiem empirycznym. |
| `fmri` | `synthetic` | Syntetyczny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; nie pochodzi z akwizycji MRI ani z publicznego zbioru BIDS. | Raport zachowuje poprawny kształt krótkiego sygnału fMRI dla regionów V1 i PFC oraz umożliwia porównanie średniej aktywności. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Aktywny benchmark edukacyjno-techniczny; nie jest benchmarkiem empirycznym. |
| `behavior` | `educational` | Edukacyjny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; wartości dobrano ręcznie do testów raportowania. | Raport zachowuje spójne porównania trafności i czasu reakcji dla minimalnego zestawu prób demonstracyjnych. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Aktywny benchmark edukacyjny; nie jest benchmarkiem empirycznym. |
