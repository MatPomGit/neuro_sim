# GUI PySide6: wybór lekcji, uruchomienie scenariusza i raport zajęciowy

## Cel widoku

Desktopowe GUI `neuro_sim` jest przeznaczone do prowadzenia krótkich lekcji z użyciem gotowych konfiguracji eksperymentów. Interfejs nie tworzy osobnego schematu konfiguracji: wybiera istniejący plik `configs/*.yaml`, pokazuje jego opis i przekazuje go do silnika `brain_core`, gdzie odbywa się walidacja konfiguracji.

## Struktura lekcji

Każda lekcja w GUI powinna być omawiana w stałej kolejności, aby prowadzący mógł powiązać wynik z konfiguracją, profilem i obserwacją:

1. **Cel** — jednozdaniowe wyjaśnienie, czego uczestnicy mają się nauczyć, np. rozpoznania habituacji, hamowania reakcji albo obciążenia pamięci roboczej.
2. **Scenariusz YAML** — wskazanie pliku `configs/*.yaml`, ziarna losowości, czasu symulacji i pola `task.scenario`. To plik YAML pozostaje źródłem prawdy dla silnika.
3. **Profil** — omówienie `clinical_profile`: nazwy profilu, mechanizmu, regionów i funkcji poznawczych, które będą użyte do interpretacji wyniku.
4. **Przewidywanie** — zapis oczekiwanego kierunku efektu przed uruchomieniem, np. wyższy błąd predykcji, słabsze hamowanie reakcji albo gorsza aktualizacja pamięci roboczej.
5. **Obserwacja** — wspólne przejrzenie osi czasu, tabeli triali, panelu „Co obserwujesz?” i metryk raportu analitycznego.
6. **Pytania kontrolne** — krótkie pytania sprawdzające, czy uczestnicy potrafią uzasadnić wynik na podstawie konfiguracji, profilu i obserwacji.

## Wybór lekcji

1. Otwórz aplikację przez `neuro-sim-gui`, `main_gui.py` albo punkt wejścia `brain_model.gui:run_gui`.
2. W zakładce **Konfiguracja** użyj pola **Lekcja**, jeżeli chcesz rozpocząć od przygotowanego przebiegu dydaktycznego.
3. Lekcja jest wyborem nadrzędnym nad pojedynczym scenariuszem: ustawia pole **konfiguracja YAML**, a dopiero wybrany plik YAML określa scenariusz silnika, czas, seed i profil.
4. Dostępne gotowe lekcje obejmują co najmniej:
   - **roving oddball** — standard, dewiant, habituacja i readaptacja;
   - **go/no-go** — hamowanie reakcji i wpływ dysregulacji GABA;
   - **n-back** — pamięć robocza, aktualizacja wartości i deficyt dopaminowy.
5. Pole **po co ten wybór** opisuje, jaki scenariusz silnika, czas oraz mechanizm profilu klinicznego znajdują się w pliku YAML.

## Wybór i uruchomienie scenariusza

1. W polu **konfiguracja YAML** wybierz preset z katalogu `configs/`, jeżeli nie korzystasz z gotowej lekcji albo chcesz ręcznie zmienić plik po wyborze lekcji.
2. Kliknij **Zastosuj konfigurację YAML**, aby przepisać do formularza bezpieczne pola podglądu: scenariusz, czas, krok czasowy, seed i opcję zapisu wyników.
3. Jeżeli zmieniasz czas albo seed, pamiętaj, że GUI zapisuje te wartości w migawce uruchomienia i przekazuje dokument do walidacji `brain_core`.
4. Kliknij **Uruchom symulację**.
5. Po zakończeniu przejdź do zakładek **Wykresy**, **Oś czasu zdarzeń**, **Profil kliniczny**, **Co obserwujesz?** i **Pytania kontrolne**.

## Jak czytać panel „Co obserwujesz teraz?”

Panel **Co obserwujesz teraz?** syntetyzuje artefakty zwrócone przez silnik:

- `event_timeline` — oś czasu eksperymentu z bodźcami, odpowiedziami i zmianami aktywności;
- `clinical_profile` — profil kliniczny użyty w konfiguracji;
- `analysis_report.roving_oddball` — metryki lekcji roving oddball, jeżeli dany scenariusz je generuje.

Panel **Dlaczego to ważne?** używa polskich nazw i kontekstów ze słownika `docs/english_polish_glossary.md`. Dzięki temu prowadzący może powiązać techniczne metryki, takie jak `prediction_error`, `confidence` albo `event_timeline`, z polskimi opisami widocznymi w interfejsie i raporcie.

## Eksport raportu i pakietu zajęciowego

Po zakończeniu symulacji dostępne są dwie akcje:

1. **Eksportuj raport PDF** — zapisuje pojedynczy plik PDF z podsumowaniem, konfiguracją, profilem klinicznym, osią czasu, raportem analitycznym i wykresami z panelu GUI.
2. **Eksportuj pakiet zajęciowy** — zapisuje katalog `pakiet_zajeciowy_neuro_sim/` zawierający:
   - `raport_zajeciowy.html` — raport tekstowy do szybkiego przeglądu;
   - `raport_zajeciowy.pdf` — wersję PDF do dystrybucji;
   - `konfiguracja_gui.json` — migawkę wyborów GUI, w tym seed;
   - kopię wybranego pliku `configs/*.yaml`, jeżeli jest dostępny;
   - `environment.json` — wersję Pythona, platformę i wersje kluczowych zależności;
   - `git_info.json` — hash commita, gałąź i status dirty repozytorium;
   - `metadata_uruchomienia.json` — czas eksportu, seed, scenariusz, ścieżkę konfiguracji, hash SHA-256 YAML, commit Git i wersje zależności;
   - `README_pakietu.md` — instrukcję odtworzenia uruchomienia z artefaktów pakietu;
   - `pytania_kontrolne.md` — pytania dla studentów z odpowiedziami z raportu, gdy są dostępne;
   - `skrot_dla_prowadzacego.md` — skrót scenariusza, profilu i metryk do omówienia;
   - `plan_lekcji.md` — przebieg lekcji w strukturze: cel, scenariusz YAML, profil, przewidywanie, obserwacja, pytania kontrolne oraz opcjonalna tabela **Co zmienić w kolejnym uruchomieniu**.

## Interpretacja raportu

- Zacznij od sekcji **Skrót metryk**, aby ustalić, które wartości najlepiej pokazują efekt scenariusza.
- W sekcji **Tabela triali** sprawdź, czy bodźce, odpowiedzi i zmiany aktywności są spójne z celem lekcji.
- W sekcji **Konfiguracja** zweryfikuj seed, czas symulacji i wybrany plik YAML, aby przebieg można było powtórzyć.
- W sekcji **Profil kliniczny** odczytaj mechanizm, regiony i funkcje poznawcze, które uzasadniają interpretację.
- W sekcji **Polski słownik pojęć** używaj tych samych nazw co w GUI, aby unikać rozbieżności terminologicznych podczas zajęć.
