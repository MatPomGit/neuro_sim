# Statyczne demonstratory widoku mózgu

Ten katalog zawiera statyczne pliki HTML używane jako dokumentacyjne demo
interaktywnych widoków aktywności mózgu. Pliki nie są wynikiem pojedynczego
uruchomienia eksperymentu i nie powinny zawierać danych badawczych ani metryk
z konkretnego przebiegu symulacji.

## Klasyfikacja plików przeniesionych z katalogu głównego

| Plik | Klasyfikacja | Uzasadnienie |
| --- | --- | --- |
| `brain_viewer.html` | statyczne demo dokumentacyjne | Samodzielny widok czterech rzutów mózgu z przykładową animacją regionów. |
| `brain_viewer_compact.html` | statyczne demo dokumentacyjne | Kompaktowy wariant tego samego demonstratora przeznaczony do prezentacji i druku. |
| `brain_sagittal_inline_regions.html` | statyczne demo dokumentacyjne | Jednorzutowy demonstrator strzałkowy z osadzonymi regionami SVG. |
| `raport_eksperymentu.pdf` | artefakt wynikowy | Raport PDF z konkretnego eksportu eksperymentu; został usunięty z repozytorium i powinien być odtwarzany przez kod raportujący. |

## Źródło generowania

Widoki bazują na wersjonowanych zasobach SVG z `assets/svg/` oraz grafikach
przekrojów w `docs/`. Mapowanie nazw regionów i koncepcję viewer opisuje
`brain_viewer/brain_viewer.md`, a kod pomocniczy dla regionów znajduje się w
`brain_viewer/mapping.py`.

Jeżeli demonstratory będą ponownie generowane automatycznie, skrypt generujący
powinien zapisywać pliki tymczasowe poza repozytorium albo w ignorowanym
katalogu `docs/generated/`, a do `docs/viewers/` należy przenosić wyłącznie
świadomie zatwierdzone wersje dokumentacyjne.
