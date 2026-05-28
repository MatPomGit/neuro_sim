# ADR-0013: Stan GUI niezależny od formularzy zaawansowanych

**Status:** proposed  
**Data:** 2026-05-28

### Kontekst

GUI modelu poznawczego przechowywało część konfiguracji w niewidocznych instancjach `ParameterForm`. To wiązało stan uruchomienia symulacji z widgetami Tkinter, utrudniało rozróżnienie wartości zatwierdzonych od wartości tylko edytowanych w oknie „Parametry zaawansowane” i zwiększało ryzyko niejawnej zmiany konfiguracji po zamknięciu okna dialogowego.

Wymagane jest zachowanie dotychczasowego formatu konfiguracji JSON oraz pozostawienie `ParameterForm` jako prostego, widocznego edytora pól w panelu zaawansowanym.

### Decyzja

Wprowadzamy dataclass `GuiState` jako jedno źródło prawdy dla danych edytowalnych przez GUI:

- wartości skalarnych symulacji (`T`, `dt`, seed, tryb uruchomienia),
- zatwierdzonych `BrainParams`,
- zatwierdzonych `WilsonCowanParams`,
- wyboru wykresów,
- ustawień batch i sensitivity.

Widoczne kontrolki głównego okna są synchronizowane ze stanem przez jawne metody pomocnicze. Okno „Parametry zaawansowane” tworzy lokalne instancje `ParameterForm`, inicjalizuje je ze stanu i zapisuje do `GuiState` wyłącznie po kliknięciu „Zapisz”. Zamknięcie okna albo kliknięcie „Anuluj” niszczy tylko lokalne formularze i nie zmienia zatwierdzonego stanu.

Format JSON pozostaje `brain-model-gui-config-v1`; zmienia się wyłącznie wewnętrzne źródło danych używane przy zapisie, odczycie, resecie i uruchamianiu symulacji.

### Konsekwencje

**Pozytywne:**

- stan konfiguracji jest jawny i niezależny od niewidocznych widgetów,
- anulowanie edycji parametrów zaawansowanych nie ma efektów ubocznych,
- `_collect_config`, `_apply_config`, `_build_brain_params` i `reset_defaults` pracują na tym samym źródle danych,
- łatwiej testować zależności GUI bez uruchamiania pełnego okna Tkinter.

**Negatywne / koszty:**

- dochodzi cienka warstwa synchronizacji między `GuiState` i kontrolkami Tkinter,
- przy dodawaniu nowych pól GUI trzeba dopisać je zarówno do `GuiState`, jak i do metod synchronizacji.

### Alternatywy rozważane

- Pozostawienie niewidocznych `ParameterForm` jako magazynu stanu: najmniejsza zmiana, ale utrwala problem niejawnych zależności widgetów.
- Trzymanie stanu w luźnym słowniku: mniej kodu początkowo, lecz słabsza czytelność i brak typowania pól.
- Pełny model MVVM dla Tkinter: czystsza architektura, ale nadmierny zakres względem prostego wymagania.

### Powiązane

- `brain_model/gui_state.py`
- `brain_model/gui_app.py`
- `brain_model/gui_config.py`
- `brain_model/gui_layout.py`
- `brain_model/gui_runner.py`
