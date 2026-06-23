# ADR-0041: Zaawansowany widok neuroanatomiczny NiiVue/WebGL

**Status:** accepted  
**Data:** 2026-06-23

## Kontekst

Dokument `brain_viewer/brain_viewer.md` opisuje dwa poziomy wizualizacji aktywności mózgu: lekki tryb SVG/Canvas oraz tryb zaawansowany oparty na NiiVue/WebGL. Repozytorium ma już statyczną stronę `docs/index.html`, dlatego najprostsza integracja powinna działać bez dodatkowego backendu i bez mieszania logiki symulacji z warstwą prezentacji.

Pełny pipeline eksportu aktywności regionalnej do NIfTI nie jest jeszcze gotowy. Jednocześnie użytkownik potrzebuje miejsca, w którym można sprawdzić docelowy komponent NiiVue, przełączyć rzuty i wczytać przygotowaną nakładkę NIfTI.

## Decyzja

Dodajemy osobną stronę `docs/niivue_viewer.html`, która ładuje NiiVue z CDN jsDelivr jako moduł ES, inicjalizuje widok WebGL na elemencie `canvas`, pokazuje demonstracyjne tło MNI152 i pozwala wczytać zewnętrzny adres nakładki NIfTI. Strona pozostaje statyczna i jest linkowana z `docs/index.html`.

Warstwa NiiVue pozostaje oddzielona od silnika symulacji. Obecna implementacja nie generuje ani nie modyfikuje danych neuroobrazowych; tylko prezentuje wolumeny dostarczone jako adresy URL. Docelowy eksport `regional_activity` oraz pochodnych NIfTI zostanie dodany osobno, gdy kontrakt danych i katalog `derivatives/<pipeline-name>/` będą gotowe.

Dla wersji desktopowej przyjmujemy tę samą stronę HTML/JavaScript jako komponent osadzany w `QWebEngineView`. Integracja desktopowa powinna użyć `QWebChannel` jako mostu PySide6 ↔ JavaScript i walidować ścieżki plików NIfTI po stronie Pythona przed przekazaniem ich do NiiVue.

`ipyniivue` pozostaje wariantem notebookowym, a nie podstawowym sposobem osadzania widoku w desktop GUI. Użycie go w oknie Qt wymagałoby lokalnego Jupyter Server i menedżera widgetów, dlatego traktujemy je jako opcjonalny tryb badawczy albo eksport notebooka, nie jako główną architekturę panelu.

## Konsekwencje

- Użytkownik ma dostęp do zaawansowanego widoku NIfTI/WebGL bez uruchamiania backendu.
- Strona wymaga dostępu do internetu, ponieważ NiiVue i demonstracyjny wolumen są ładowane z zewnętrznych adresów.
- Desktop może ponownie użyć tego samego komponentu przez Qt WebEngine, ale wymaga dostępnego OpenGL albo zgodnej emulacji programowej.
- Integracja jest mała i odwracalna: nie zmienia API symulatora ani formatu wyników eksperymentu.
- Właściwe dane badawcze nadal muszą być eksportowane jako jawne artefakty pochodne zgodne z wymaganiami BIDS, zanim zostaną użyte jako nakładka.

## Alternatywy

1. **Pełny pipeline NIfTI od razu** — odrzucony na tym etapie, bo wymagałby zmiany kontraktów danych, walidacji BIDS i dodatkowych testów numerycznych.
2. **Wyłącznie SVG/Canvas** — dobry tryb dydaktyczny, ale nie spełnia prośby o implementację NiiVue.
3. **Bundlowanie NiiVue w repozytorium** — odrzucone na etap demonstratora, aby nie dodawać dużych artefaktów frontendowych i nie komplikować statycznego hostingu dokumentacji. Przy wdrożeniu desktopowym można wrócić do wariantu vendoringu, jeśli wymagana będzie praca offline.
4. **Osobna natywna implementacja desktopowa bez NiiVue** — odrzucona, bo dublowałaby logikę rzutów i skalowania koloru względem wersji webowej.
