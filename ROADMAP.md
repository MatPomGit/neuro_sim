# ROADMAP — `neuro_sim`

## 1. Cel produktu

`neuro_sim` ma ewoluować z demonstratora procesów poznawczych do **wieloskalowej platformy symulacji mózgu** łączącej:
- neuropsychologię,
- psychologię poznawczą,
- psychiatrię obliczeniową,
- dydaktykę akademicką.

Docelowo aplikacja ma umożliwiać studentom i badaczom:
1. uruchamianie porównywalnych scenariuszy bodźców,
2. obserwację zmian aktywności neuronalnej i dynamiki sieciowej,
3. analizę wpływu neuroprzekaźników oraz neuromodulatorów,
4. porównanie mózgu zdrowego vs. mózgu z zaburzeniami, deficytami i uszkodzeniami.

---

## 2. Zasady realizacji roadmapy

1. **KISS + minimalny zakres zmian** — każdy etap dostarcza działającą wartość edukacyjną i badawczą.
2. **Rozdzielenie warstw** — `brain_core` (silnik), `brain_model` (modele domenowe), UI/raporty jako warstwa prezentacji.
3. **Konfiguracja ponad hardcoding** — eksperymenty uruchamiane przez YAML/JSON (reproducibility).
4. **Deterministyczność** — kontrola RNG, wersjonowanie parametrów i danych.
5. **Dydaktyczność by design** — „explainability panel” i raport krok-po-kroku dla każdej symulacji.

---

## 3. Architektura docelowa (warstwy)

### Warstwa biologiczna
- neurony i populacje E/I,
- synapsy i receptory (AMPA, NMDA, GABA),
- neuromodulacja (DA, 5-HT, ACh, NA),
- uproszczona homeostaza i plastyczność.

### Warstwa sieciowa
- atlas regionów,
- konektom strukturalny + opóźnienia przewodzenia,
- sprzężenia międzyobszarowe,
- rytmy i synchronizacja.

### Warstwa poznawcza
- uwaga, pamięć robocza/epizodyczna/semantyczna,
- kontrola wykonawcza i salience,
- emocje, wycena i podejmowanie decyzji,
- scenariusze zadań poznawczych.

---

## 4. Horyzonty realizacji

### Zadanie referencyjne przekrojowe: **Roving Oddball Task**

Roving oddball task (sekwencje powtarzanych bodźców z okazjonalną zmianą standardu) staje się
**głównym scenariuszem referencyjnym** do walidacji neuropsychologicznej, poznawczej, psychiatrycznej i dydaktycznej.

**Dlaczego właśnie to zadanie:**
- dobrze testuje predykcję, detekcję nowości i aktualizację reprezentacji,
- ma czytelne markery czasowe dla raportów edukacyjnych,
- wspiera porównania healthy vs disorder vs lesion,
- pozwala mapować wpływ neuromodulatorów na adaptację i błąd predykcji.

**Minimalna implementacja (MVP):**
- generator sekwencji `standard -> deviant -> nowy standard` z kontrolą długości runów,
- rejestr zdarzeń: rozpoczęcie (onset) bodźca, typ bodźca, wskaźnik zaskoczenia (surprise index), aktualizacja stanu sieci,
- raport dydaktyczny pokazujący przebieg adaptacji trial-by-trial,
- dashboard porównawczy dla profili healthy/disorder/lesion.

## Faza 1 (0–3 miesiące): Fundament symulacyjno-edukacyjny

**Cele:**
- Uporządkowanie konfiguracji i scenariuszy eksperymentów.
- Wprowadzenie pierwszej wersji raportowania dydaktycznego.
- Stabilizacja pipeline: bodziec → symulacja → analiza → raport.

**Zakres:**
- Standaryzacja plików konfiguracyjnych (baseline healthy brain).
- Rejestr zdarzeń symulacji (co, kiedy, dlaczego).
- Raporty tekstowe i wykresy z osią czasu.
- Testy regresji dla istniejących modułów poznawczych.
- MVP roving oddball task z wersją healthy (single-region + multi-region readout).

**Kryteria ukończenia:**
- Student uruchamia gotowy eksperyment i otrzymuje czytelny raport krokowy.
- Każda symulacja ma identyfikowalną konfigurację i seed.
- Dla roving oddball widoczne są: habituacja do standardu i odpowiedź na zmianę.

---

## Faza 2 (3–6 miesięcy): Model whole-brain na poziomie neural mass

**Cele:**
- Przejście z pojedynczej macierzy połączeń do konektomu regionów.
- Wprowadzenie opóźnień przewodzenia i podstaw neuromodulacji.

**Zakres:**
- Moduł anatomii regionów i mapowania funkcji poznawczych.
- Neural mass / mean-field per region (E/I + adaptacja).
- Coupling z opóźnieniami `C_ij` i `delay_ij`.
- Podstawowe indeksy: synchronizacja, moc pasmowa, przepływ informacji.

**Kryteria ukończenia:**
- Możliwość uruchomienia symulacji wieloregionowej dla co najmniej dwóch zadań poznawczych.
- Widoczne i interpretowalne efekty opóźnień oraz modulacji.

---

## Faza 3 (6–9 miesięcy): Biblioteka fenotypów klinicznych i uszkodzeń

**Cele:**
- Dodanie scenariuszy „healthy vs disorder vs lesion”.
- Umożliwienie porównań 1:1 dla tych samych bodźców.

**Zakres:**
- Profile zaburzeń (np. hipodopaminergia, dysregulacja GABA, deficyty serotoniny).
- Profile uszkodzeń mechanicznych (ogniskowe i sieciowe).
- Walidacje jakościowe względem literatury i hipotez neuropsychologicznych.
- Dashboard porównawczy wyników.
- Warianty roving oddball dla profili klinicznych (zmiany amplitudy, latencji, tempa readaptacji).

**Kryteria ukończenia:**
- Student może uruchomić ten sam bodziec dla min. 3 profili i porównać trajektorie.
- Raport explicite wskazuje mechanizm różnicy (region, nadajnik, czas, efekt poznawczy).

---

## Faza 4 (9–12 miesięcy): Hybrydy mikro-makro (wybrane obwody spiking)

**Cele:**
- Integracja wybranych obwodów spiking z modelem makro.
- Lepsza dydaktyka mechanizmów neuronalnych „od kanału do zachowania”.

**Zakres:**
- Pilot dla 1–2 obwodów (np. hipokamp, PFC-basal ganglia).
- Interfejs współsymulacji (spiking submodel ↔ whole-brain).
- Scenariusze pokazujące wpływ lokalnej mikro-dynamiki na wynik zadania poznawczego.

**Kryteria ukończenia:**
- Działający eksperyment wieloskalowy z pełnym raportem dydaktycznym.
- Udokumentowane ograniczenia wydajnościowe i interpretacyjne.

---

## Faza 5 (12+ miesięcy): Platforma dydaktyczna i badawcza

**Cele:**
- Produkcyjna jakość edukacyjna.
- Gotowe „lekcje laboratoryjne” dla kursów neuropsychologii i psychiatrii obliczeniowej.

**Zakres:**
- Biblioteka scenariuszy dydaktycznych (poziom podstawowy/zaawansowany).
- Auto-raporty i quizy interpretacyjne.
- Wersjonowane benchmarki i protokoły walidacji.

**Kryteria ukończenia:**
- Kompletne moduły zajęć laboratoryjnych możliwe do prowadzenia na uczelni.
- Powtarzalne wyniki i jasna ścieżka interpretacji przez studentów.

---

## 5. Strumienie przekrojowe (ciągłe)

1. **Walidacja naukowa:** przeglądy modeli, testy hipotez, zgodność jakościowa z literaturą.
2. **Inżynieria jakości:** testy jednostkowe/integracyjne/regresyjne, CI, kontrola parametrów.
3. **UX dydaktyczny:** narracje, legendy, objaśnienia pojęć i mechanizmów.
4. **Wydajność:** profilowanie obliczeń, strategie skalowania, uproszczenia tam gdzie to możliwe.
5. **Dokumentacja:** ADR dla zmian strukturalnych, przewodniki eksperymentów i metodyki.

---

## 6. Mierniki sukcesu

- **Naukowe:** spójność dynamiki modelu z oczekiwanymi efektami neurobiologicznymi.
- **Edukacyjne:** skrócenie czasu potrzebnego studentowi do poprawnej interpretacji wyników.
- **Inżynierskie:** reprodukowalność wyników z tej samej konfiguracji i seeda.
- **Produktowe:** liczba gotowych scenariuszy porównawczych healthy/disorder/lesion.

---

## 7. Ryzyka i mitigacje

1. **Ryzyko nadmiernej złożoności** → etapowanie i twarde kryteria „Definition of Done”.
2. **Ryzyko braku interpretowalności** → obowiązkowe raporty „co się wydarzyło i dlaczego”.
3. **Ryzyko niestabilności numerycznej** → testy stabilności i ograniczenia zakresów parametrów.
4. **Ryzyko rozjazdu warstw (GUI vs silnik)** → ścisłe API konfiguracji i izolacja odpowiedzialności.
