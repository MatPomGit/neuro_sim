# AGENTS.md — wytyczne dla agentów AI w projekcie `neuro_sim`

Ten dokument definiuje obowiązkowe zasady dla agentów AI wykonujących zmiany w repozytorium.

## 1) Zasady nadrzędne

1. **KISS (Keep It Simple, Stupid)**
   - Preferuj najprostsze rozwiązanie, które spełnia wymagania.
   - Nie dodawaj nowych warstw abstrakcji bez realnej potrzeby biznesowej/technicznej.

2. **Minimalny zakres zmian**
   - Modyfikuj wyłącznie pliki i obszary niezbędne do realizacji zadania.
   - Unikaj refaktorów „przy okazji” jeśli nie są częścią zlecenia.

3. **Spójność z istniejącą architekturą**
   - Szanuj podział odpowiedzialności (`brain_core` vs `brain_model`, konfiguracja, I/O).
   - Nie wprowadzaj zależności cyklicznych i nie mieszaj warstw domenowych z infrastrukturą.

4. **Bezpieczeństwo i przewidywalność**
   - Nie dodawaj ukrytych efektów ubocznych.
   - Nie osłabiaj walidacji wejścia i mechanizmów deterministyczności.

---

## 2) Nakazy (MUST)

1. **Dokumentuj decyzje architektoniczne**
   - Każda zmiana strukturalna (np. nowy moduł, istotna zmiana granic odpowiedzialności, zmiana strategii konfiguracji, I/O, losowości, integracji) **musi** zostać opisana w ADR.
   - ADR dodawaj zgodnie z zasadami w `docs/architecture_decision_records.md` (status, kontekst, decyzja, konsekwencje, alternatywy).

2. **Uzasadniaj kompromisy**
   - Jeśli wybierasz rozwiązanie mniej oczywiste: opisz dlaczego, jakie są koszty i jakie alternatywy odrzucono.

3. **Dbaj o testowalność**
   - Kod musi być możliwy do zweryfikowania (testy, walidacja, reprodukcja uruchomienia).
   - Przy zmianach logiki: dodaj lub zaktualizuj odpowiednie testy/artefakty weryfikacji.

4. **Zachowuj kompatybilność konfiguracji**
   - Przy zmianie konfiguracji/schematu zapewnij ścieżkę migracji lub czytelny błąd walidacji.

5. **Czytelność ponad „spryt”**
   - Nazwy mają być jednoznaczne i domenowe.
   - Funkcje powinny być krótkie, z pojedynczą odpowiedzialnością.

6. **Jawność zmian**
   - Opisuj w PR co, dlaczego i jak zweryfikowano.
   - Nie ukrywaj istotnych zmian pod dużym, niepowiązanym diffem.

---

## 3) Zakazy (MUST NOT)

1. **Zakaz over-engineeringu**
   - Nie wprowadzaj wzorców/protokółów/frameworków „na przyszłość”, jeśli nie są teraz potrzebne.

2. **Zakaz „silent breaking changes”**
   - Nie zmieniaj zachowania API, formatów danych, konfiguracji lub semantyki bez jawnej dokumentacji i migracji.

3. **Zakaz mieszania odpowiedzialności**
   - Nie przenoś logiki domenowej do warstwy technicznej i odwrotnie.

4. **Zakaz martwego kodu**
   - Nie dodawaj nieużywanych klas, funkcji, flag, parametrów i komentarzy TODO bez właściciela/uzasadnienia.

5. **Zakaz pseudonapraw**
   - Nie „naprawiaj” problemu przez wyciszanie wyjątków, usuwanie walidacji, ignorowanie błędów lub omijanie testów.

6. **Zakaz losowej niedeterministyczności**
   - Nie używaj niekontrolowanych źródeł losowości poza uzgodnionym mechanizmem RNG.

7. **Zakaz masowych zmian formatowania bez powodu**
   - Nie przebudowuj całych plików tylko po to, by zmienić styl/układ, jeśli zadanie tego nie wymaga.

---

## 4) Checklist przed zakończeniem zadania

Agent AI ma obowiązek sprawdzić:

- [ ] Czy rozwiązanie jest najprostsze możliwe (KISS)?
- [ ] Czy zakres diffu jest minimalny i zgodny z zadaniem?
- [ ] Czy nie wprowadzono zmian ubocznych poza zakresem?
- [ ] Czy zmiany strukturalne zostały opisane w ADR?
- [ ] Czy konfiguracja/schemat pozostają spójne i walidowalne?
- [ ] Czy testy/weryfikacja potwierdzają działanie?
- [ ] Czy opis PR jasno tłumaczy: **co**, **dlaczego**, **jak sprawdzono**?

---

## 5) Preferowany styl pracy agenta

1. Najpierw zrozum wymaganie, potem koduj.
2. Najpierw lokalna poprawka, potem ewentualna generalizacja.
3. Jeśli niepewność jest wysoka — zaproponuj 2–3 warianty i wybierz rekomendowany.
4. Przy zmianach architektury: najpierw ADR (proposed), potem implementacja.

---

## 6) Reguła rozstrzygania konfliktów zasad

Jeżeli występuje konflikt między wytycznymi:
1. Bezpieczeństwo i poprawność systemu,
2. Polecenie użytkownika,
3. Ten dokument (AGENTS.md),
4. Lokalna wygoda implementacyjna.

Agent ma zawsze wybrać opcję bezpieczniejszą i lepiej udokumentowaną.

---

## 7) Polityka językowa (MUST)

1. **Interfejs i opisy dla użytkownika w języku polskim**
   - Wszystkie treści prezentowane użytkownikowi końcowemu (GUI, CLI, raporty, logi użytkowe, opisy scenariuszy, dokumentacja użytkowa) twórz po polsku.

2. **Komentarze w kodzie w języku polskim**
   - Komentarze inline, docstringi objaśniające implementację oraz komentarze projektowe zapisuj po polsku.

3. **Kod i nazewnictwo techniczne w języku angielskim**
   - Nazwy zmiennych, funkcji, klas, modułów, plików konfiguracyjnych i identyfikatorów API muszą pozostać angielskie.
   - Nie tłumacz nazw technicznych używanych w kodzie na polski.

4. **Mapowanie nazw EN→PL dla warstwy prezentacji**
   - Gdy nazwa techniczna (EN) jest pokazywana użytkownikowi, udostępnij czytelny odpowiednik PL w warstwie UI/opisu.
   - Jako źródło mapowania stosuj słownik: `docs/english_polish_glossary.md`.

5. **Spójność terminologiczna**
   - Dla tego samego pojęcia używaj jednej, konsekwentnej formy polskiej we wszystkich interfejsach i dokumentach.


8. **Wymóg docstringów i type hints (MUST)**
   - Każda nowa funkcja i klasa dodawana przez agenta musi zawierać kompletne adnotacje typów oraz docstring.
   - Dotyczy to także funkcji pomocniczych i metod prywatnych.

---

## 9) Stos desktopowego GUI (MUST)

1. **PySide6/Qt jako docelowa biblioteka GUI**
   - Nowe elementy desktopowego GUI buduj w oparciu o `PySide6` i wzorce Qt używane w modułach `brain_model/qt_*`.
   - Nie dodawaj nowych ekranów, widżetów ani przepływów użytkownika opartych na `tkinter`; istniejące moduły `tkinter` traktuj jako kod legacy/kompatybilności, którego nie należy rozwijać bez osobnej decyzji architektonicznej.

2. **Wykresy w GUI**
   - Osadzanie wykresów w desktopowym GUI realizuj przez backend Matplotlib dla Qt (`matplotlib.backends.backend_qtagg`) oraz komponenty zgodne z `brain_model/qt_plotting.py`.
   - Nie mieszaj backendów GUI w jednym nowym przepływie użytkownika.

3. **Spójność zależności**
   - Każdą zmianę zależności wymaganych przez GUI synchronizuj w `pyproject.toml`, `requirements.txt`, `environment.yml` i dokumentacji użytkowej.
   - `PySide6` jest zależnością uruchomieniową desktopowego GUI, a punktami wejścia pozostają `main_gui.py`, `brain_model.gui:run_gui` oraz skrypt `neuro-sim-gui`.
