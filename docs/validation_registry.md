# Rejestr walidacji benchmarków

Ten dokument porządkuje minimalny rejestr benchmarków używanych do walidacji
technicznej i jakościowej. Źródłem prawdy dla poziomu, źródła, zakresu,
ograniczeń i kryteriów zgodności pozostaje
`data/validation/benchmark_metadata.json`; poniższa tabela uzupełnia ten opis o
poziom walidacji jakościowej, oczekiwany efekt, tolerancję oraz bieżący status.

## Zakres ograniczeń modelu

Poziom walidacji jakościowej w tabeli oznacza wyłącznie zakres efektu, który
można kontrolować automatycznie w repozytorium. Benchmarki `eeg` i `fmri` są
syntetyczne, a `behavior` jest edukacyjny, dlatego zgodność nie oznacza
kalibracji do danych uczestników, norm populacyjnych, diagnozy klinicznej ani
walidacji psychometrycznej/hemodynamicznej. Strukturalne kryteria zgodności per
benchmark są zapisane w `data/validation/benchmark_metadata.json` w polu
`compliance_checks`; kod loadera wymaga tych pól jawnie i nie uzupełnia braków
domyślnymi progami.

| Benchmark | Poziom | Poziom walidacji jakościowej | Źródło | Oczekiwany efekt | Kryteria zgodności | Tolerancja | Ograniczenia modelu | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `eeg` | `synthetic` | Techniczna walidacja kształtu i raportowania sygnału; brak walidacji klinicznej. | Syntetyczny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; nie pochodzi z danych uczestników. | Raport zachowuje poprawny kształt krótkiego sygnału EEG dla kanałów Cz i Pz oraz umożliwia podstawowe porównania amplitudy bez interpretacji klinicznej. | Zgodność oznacza poprawny odczyt niepustej macierzy z kolumnami metryk Cz i Pz, zachowanie co najmniej dwóch próbek oraz raportowanie metryk porównawczych bez interpretacji klinicznej. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Benchmark nie reprezentuje norm klinicznych, rozkładów populacyjnych ani pełnych właściwości czasowo-częstotliwościowych EEG. | Aktywny benchmark edukacyjno-techniczny; nie jest benchmarkiem empirycznym. |
| `fmri` | `synthetic` | Techniczna walidacja kształtu i średniej aktywności regionów; brak walidacji hemodynamicznej. | Syntetyczny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; nie pochodzi z akwizycji MRI ani z publicznego zbioru BIDS. | Raport zachowuje poprawny kształt krótkiego sygnału fMRI dla regionów V1 i PFC oraz umożliwia porównanie średniej aktywności. | Zgodność oznacza poprawny odczyt niepustej macierzy regionów V1 i PFC, zachowanie co najmniej dwóch próbek oraz raportowanie porównań średniej aktywności bez wnioskowania hemodynamicznego. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Benchmark nie modeluje pełnej odpowiedzi hemodynamicznej, opóźnień skanera, wariancji międzyosobniczej ani artefaktów akwizycji. | Aktywny benchmark edukacyjno-techniczny; nie jest benchmarkiem empirycznym. |
| `behavior` | `educational` | Edukacyjna walidacja spójności raportowania trafności i czasu reakcji; brak walidacji psychometrycznej. | Edukacyjny cel walidacyjny utrzymywany w repozytorium `neuro_sim`; wartości dobrano ręcznie do testów raportowania. | Raport zachowuje spójne porównania trafności i czasu reakcji dla minimalnego zestawu prób demonstracyjnych. | Zgodność oznacza poprawny odczyt minimalnego zestawu prób z trafnością i czasem reakcji oraz raportowanie porównań behawioralnych wyłącznie jako kontroli edukacyjnej. | Testy regresji powinny akceptować wyłącznie różnice numeryczne wynikające z precyzji obliczeń; zmiana jakościowa wymaga aktualizacji metadanych i uzasadnienia. | Benchmark nie jest próbą empiryczną, nie zawiera wariancji populacyjnej i nie powinien być używany do wniosków psychometrycznych. | Aktywny benchmark edukacyjny; nie jest benchmarkiem empirycznym. |

## Rejestr metryk raportowych

Tabela opisuje metryki zapisywane w `analysis_report.metrics`. Polskie etykiety
są zgodne ze słownikiem `docs/english_polish_glossary.md`. Zakres interpretacji
określa, co wolno wnioskować z metryki w tym repozytorium; ograniczenia wskazują,
czego metryka nie potwierdza i nie powinna sugerować użytkownikowi.

| Nazwa techniczna | Polska etykieta | Źródło danych walidacyjnych | Zakres interpretacji | Ograniczenia |
| --- | --- | --- | --- | --- |
| `band_power_delta` | moc pasma delta | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Porównanie względnej energii pasma delta w symulowanym sygnale EEG. | Nie jest markerem snu, encefalopatii ani diagnozy klinicznej; zależy od syntetycznego sygnału i parametrów próbkowania. |
| `band_power_theta` | moc pasma theta | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Porównanie względnej energii pasma theta w symulowanym sygnale EEG. | Nie jest markerem klinicznym ani normą populacyjną; nie zastępuje analizy artefaktów i protokołu EEG. |
| `band_power_alpha` | moc pasma alfa | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Porównanie względnej energii pasma alfa w symulowanym sygnale EEG. | Nie oznacza stanu czuwania, relaksacji ani patologii; brak kalibracji do empirycznych zapisów EEG. |
| `band_power_beta` | moc pasma beta | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Porównanie względnej energii pasma beta w symulowanym sygnale EEG. | Nie jest wskaźnikiem pobudzenia ruchowego ani diagnozy; interpretacja jest wyłącznie edukacyjno-techniczna. |
| `band_power_gamma` | moc pasma gamma | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Porównanie względnej energii pasma gamma w symulowanym sygnale EEG. | Nie modeluje wiarygodnie artefaktów mięśniowych ani wysokoczęstotliwościowej aktywności empirycznej. |
| `erp_proxy_peak_to_peak` | zakres odpowiedzi ERP proxy | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Opis rozpiętości głównego kanału EEG jako proxy odpowiedzi zdarzeniowej. | Nie jest empiryczną amplitudą ERP; brak segmentacji triali, baseline correction i jednostek mikrovoltów. |
| `phase_locking_value` | wartość synchronizacji fazowej | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Opis zgodności faz między dwoma symulowanymi kanałami lub regionami. | Nie potwierdza sprzężenia neuronalnego ani konektywności klinicznej; zależy od uproszczonego modelu fazy. |
| `connectivity_mean` | średnia konektywność | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Średni znakowany poziom korelacji między regionami w symulacji. | Korelacja nie oznacza przyczynowości; metryka nie uwzględnia pełnych procedur czyszczenia EEG/fMRI. |
| `connectivity_abs_mean` | średnia bezwzględna konektywność | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Ogólna siła zależności liniowych między regionami bez znaku korelacji. | Nie rozróżnia dodatnich i ujemnych kierunków zależności; nie jest markerem zaburzeń sieciowych. |
| `pli_proxy_mean` | średnia proxy indeksu opóźnienia fazy | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Uproszczony opis asymetrii fazowej między regionami. | To proxy PLI, nie pełna procedura EEG; nie usuwa automatycznie przewodnictwa objętościowego ani artefaktów. |
| `region_strength_mean` | średnia siła regionu | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Średnia siła powiązań regionów w macierzy korelacji symulacji. | Nie jest miarą anatomicznej integralności regionu ani wynikiem neuroobrazowania klinicznego. |
| `directional_mean` | średni kierunkowy przepływ informacji | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Znakowany proxy kierunku zależności czasowych między regionami. | Nie jest dowodem przyczynowości neuronalnej; brak walidacji względem metod Grangera, DCM lub transfer entropy. |
| `directional_abs_mean` | średni bezwzględny kierunkowy przepływ informacji | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Ogólna siła proxy kierunkowości bez rozróżniania znaku. | Nie wskazuje źródła patologii ani diagnozy; zależy od opóźnień syntetycznego sygnału. |
| `outgoing_mean` | średni wypływ informacji | Benchmark `eeg` z syntetycznego celu walidacyjnego w `data/validation/eeg_target.csv`. | Średni proxy wypływu informacji z regionów w sieci symulowanej. | Nie jest miarą efektywnej konektywności klinicznej; wymaga porównania w tym samym ustawieniu symulacji. |
| `prediction_error_mean` | średni błąd predykcji | Diagnostyka symulacji zapisywana w raportach eksportu GUI; brak zewnętrznego celu walidacyjnego. | Średni błąd predykcji modelu w bieżącym przebiegu symulacji. | Nie jest miarą objawu, trafności klinicznej ani jakości psychometrycznej; służy do monitorowania mechaniki modelu. |
| `behavior_mean` | średnia metryka behawioralna | Benchmark `behavior` z edukacyjnego celu walidacyjnego w `data/validation/behavior_target.csv`. | Średni poziom sygnału behawioralnego lub wyniku zadania w przebiegu demonstracyjnym. | Nie jest normą psychometryczną, miarą sprawności poznawczej ani wynikiem diagnostycznym. |
| `behavior_std` | odchylenie standardowe metryki behawioralnej | Benchmark `behavior` z edukacyjnego celu walidacyjnego w `data/validation/behavior_target.csv`. | Zmienność sygnału behawioralnego lub wyniku zadania w przebiegu demonstracyjnym. | Nie opisuje wariancji populacyjnej ani rzetelności testu psychologicznego; zależy od syntetycznej sekwencji. |
| `fmri_mean` | średnia aktywność BOLD | Benchmark `fmri` z syntetycznego celu walidacyjnego w `data/validation/fmri_target.csv`. | Średni poziom syntetycznego sygnału BOLD po modelowaniu hemodynamicznym. | Nie jest empiryczną aktywacją fMRI; brak modelowania skanera, preprocessing fMRI i kalibracji do BIDS. |
| `bold_peak_to_peak` | zakres sygnału BOLD | Benchmark `fmri` z syntetycznego celu walidacyjnego w `data/validation/fmri_target.csv`. | Rozpiętość odpowiedzi BOLD proxy w symulowanym przebiegu. | Nie potwierdza efektu hemodynamicznego ani aktywacji klinicznej; zależy od HRF i napędu neuronalnego modelu. |
