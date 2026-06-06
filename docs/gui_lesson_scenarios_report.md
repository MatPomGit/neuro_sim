# GUI PySide6: wybór lekcji, uruchomienie scenariusza i raport zajęciowy

## Cel widoku

Desktopowe GUI `neuro_sim` jest przeznaczone do prowadzenia krótkich lekcji z użyciem gotowych konfiguracji eksperymentów. Interfejs nie tworzy osobnego schematu konfiguracji: wybiera istniejący plik `configs/*.yaml`, pokazuje jego opis i przekazuje go do silnika `brain_core`, gdzie odbywa się walidacja konfiguracji.

## Wybór lekcji

1. Otwórz aplikację przez `neuro-sim-gui`, `main_gui.py` albo punkt wejścia `brain_model.gui:run_gui`.
2. W zakładce **Konfiguracja** użyj pola **gotowa lekcja**, jeżeli chcesz rozpocząć od przygotowanego przebiegu dydaktycznego.
3. Lekcja ustawia pole **konfiguracja YAML** na jeden z presetów z katalogu `configs/`.
4. Pole **po co ten wybór** opisuje, jaki scenariusz silnika, czas oraz mechanizm profilu klinicznego znajdują się w pliku YAML.

## Wybór i uruchomienie scenariusza

1. W polu **konfiguracja YAML** wybierz preset z katalogu `configs/`.
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
   - `metadata_uruchomienia.json` — czas eksportu, seed, scenariusz, ścieżkę konfiguracji i informacje o środowisku;
   - `pytania_kontrolne.md` — pytania dla studentów z odpowiedziami z raportu, gdy są dostępne;
   - `skrot_dla_prowadzacego.md` — skrót scenariusza, profilu i metryk do omówienia.

## Interpretacja raportu

- Zacznij od sekcji **Skrót metryk**, aby ustalić, które wartości najlepiej pokazują efekt scenariusza.
- W sekcji **Tabela triali** sprawdź, czy bodźce, odpowiedzi i zmiany aktywności są spójne z celem lekcji.
- W sekcji **Konfiguracja** zweryfikuj seed, czas symulacji i wybrany plik YAML, aby przebieg można było powtórzyć.
- W sekcji **Profil kliniczny** odczytaj mechanizm, regiony i funkcje poznawcze, które uzasadniają interpretację.
- W sekcji **Polski słownik pojęć** używaj tych samych nazw co w GUI, aby unikać rozbieżności terminologicznych podczas zajęć.
