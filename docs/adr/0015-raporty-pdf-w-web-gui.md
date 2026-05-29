# ADR-0015: Raporty PDF generowane w web GUI

**Status:** proposed  
**Data:** 2026-05-29

### Kontekst

Web GUI ma zbliżyć się funkcjonalnie do aplikacji desktopowej, ale działa jako statyczna strona GitHub Pages bez serwera zapisu plików. Użytkownik potrzebuje jednak gotowego raportu z badania symulacyjnego wraz z wykresami oraz możliwości zapisania konfiguracji i wyników lokalnie.

### Decyzja

Raport badawczy w web GUI generujemy po stronie przeglądarki. Metryki i opis scenariusza pochodzą z ostatniego przebiegu symulacji, a aktywne wykresy Plotly są konwertowane do obrazów PNG i osadzane w pliku PDF tworzonym przez `jsPDF`. Konfiguracja web GUI jest zapisywana i wczytywana jako lokalny JSON, a dane tabelaryczne pozostają eksportowane jako CSV.

### Konsekwencje

**Pozytywne:**

- web GUI nie wymaga backendu ani dostępu do systemu plików poza standardowym pobieraniem plików przez przeglądarkę,
- raport PDF zawiera zarówno podsumowanie badania, jak i wykresy wygenerowane w interfejsie,
- przepływ webowy jest bliższy desktopowemu: konfiguracja, uruchomienie, wykresy, eksport danych i raport.

**Negatywne / koszty:**

- eksport PDF zależy od dostępności bibliotek JavaScript ładowanych z CDN,
- bardzo duża liczba wykresów zwiększa rozmiar PDF i czas generowania,
- raport webowy jest lżejszy od raportu desktopowego opartego na Matplotlib i nie zapisuje artefaktów w katalogu `outputs/`.

### Alternatywy rozważane

- Eksport wyłącznie przez drukowanie strony do PDF: prostszy, ale mniej przewidywalny i gorzej kontroluje osadzanie wykresów.
- Generowanie PDF w Pyodide: możliwe, ale znacząco zwiększałoby czas ładowania i liczbę zależności.
- Backend raportowania: najpełniejszy technicznie, lecz sprzeczny z założeniem statycznej strony projektu.

### Powiązane dokumenty / issue / PR

- `docs/web_gui.html`
- `brain_model/report_export.py`
- `brain_model/gui_layout.py`
