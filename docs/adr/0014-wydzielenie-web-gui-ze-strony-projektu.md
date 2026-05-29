# ADR-0014: Wydzielenie web GUI ze strony projektu

**Status:** proposed  
**Data:** 2026-05-29

### Kontekst

Dotychczasowy plik `docs/index.html` pełnił jednocześnie rolę strony głównej projektu oraz kompletnego webowego interfejsu symulacji uruchamianego przez Pyodide. Użytkownik wchodzący na stronę dokumentacji trafiał od razu do formularza parametrów, a nie do opisu celu narzędzia, aktualnych możliwości, roadmapy i instrukcji obsługi.

Backlog, lista todo i roadmapa wskazują, że projekt ma być prezentowany jako narzędzie edukacyjno-badawcze z jasnym rozdziałem między komunikacją produktową, instrukcją użytkownika oraz właściwym uruchomieniem symulacji.

### Decyzja

Wydzielamy dotychczasowy webowy interfejs symulacji do `docs/web_gui.html`, a `docs/index.html` staje się stroną projektu. Strona główna zawiera zakładki z opisem projektu, możliwościami, roadmapą, instrukcją obsługi i odnośnikami do dokumentacji. Główne wezwania do działania prowadzą do `web_gui.html`.

### Konsekwencje

**Pozytywne:**

- użytkownik najpierw otrzymuje kontekst projektu i instrukcję obsługi,
- web GUI pozostaje dostępny jako osobny, bezpośredni artefakt,
- strona główna może promować aktualne i planowane możliwości bez mieszania ich z formularzem symulacji,
- łatwiej utrzymać polskie opisy użytkowe zgodne ze słownikiem projektu.

**Negatywne / koszty:**

- pojawia się drugi plik HTML w dokumentacji,
- zmiany w nawigacji GitHub Pages muszą pilnować, aby link do `web_gui.html` pozostał aktualny.

### Alternatywy rozważane

- Pozostawienie GUI w `index.html` i dodanie sekcji promocyjnych nad formularzem: prostsze plikowo, ale pogarsza czytelność i wydłuża stronę startową.
- Przeniesienie strony promocyjnej do osobnego pliku, np. `project.html`: zachowuje dotychczasowy adres GUI, ale nie spełnia celu, aby `docs/index.html` było stroną projektu.

### Powiązane dokumenty / issue / PR

- `docs/index.html`
- `docs/web_gui.html`
- `BACKLOG.md`
- `docs/todo.md`
- `ROADMAP.md`
