# Słownik EN→PL dla warstwy prezentacji

## Cel

Ten dokument definiuje mapowanie nazw technicznych używanych w kodzie (angielski) na etykiety i opisy prezentowane użytkownikowi (polski).

## Zasady użycia

1. Kod i identyfikatory techniczne pozostają w języku angielskim.
2. W interfejsach użytkownika i dokumentacji użytkowej używaj odpowiedników polskich z tego słownika.
3. Dla nowych elementów dodawaj wpis EN→PL w tym pliku równolegle ze zmianą funkcjonalną.
4. Utrzymuj spójność tłumaczeń we wszystkich widokach (GUI, CLI, raporty, dokumentacja).

## Słownik pojęć

| English (kod) | Polski (UI/opis) | Kontekst użycia |
|---|---|---|
| simulation_time | czas symulacji | Parametry uruchomienia |
| seed | ziarno losowości | Parametry uruchomienia |
| noise | szum | Parametry modelu |
| scenario | scenariusz | Wybór przebiegu eksperymentu |
| baseline | bazowy | Nazwa scenariusza |
| reward_learning | uczenie nagrodą | Nazwa scenariusza |
| threat_only | tylko zagrożenie | Nazwa scenariusza |
| stress_recovery | regeneracja po stresie | Nazwa scenariusza |
| task_switching | przełączanie zadań | Nazwa scenariusza |
| sensory_overload | przeciążenie sensoryczne | Nazwa scenariusza |
| run | uruchom | Komenda akcji |
| batch | seria uruchomień | Komenda akcji |
| save_results | zapisz wyniki | Opcja wyjścia |
| prediction_error | błąd predykcji | Metryka diagnostyczna |
| confidence | pewność | Metryka diagnostyczna |
| decision_events | zdarzenia decyzyjne | Metryka diagnostyczna |
| global_workspace | globalna przestrzeń robocza | Diagnostyka modelu |
| attention | uwaga | Moduł poznawczy |
| working_memory | pamięć robocza | Moduł poznawczy |
| semantic_memory | pamięć semantyczna | Moduł poznawczy |
| episodic_memory | pamięć epizodyczna | Moduł poznawczy |
| salience_network | sieć istotności | Moduł poznawczy |
| default_mode_network | sieć trybu domyślnego | Moduł poznawczy |
| plot_activity | wykres aktywacji | Etykieta wykresu |
| plot_diagnostics | wykres diagnostyczny | Etykieta wykresu |
| plot_eeg | wykres EEG | Etykieta wykresu |
| band_power | moc pasm | Etykieta wykresu |
| weight_trajectories | trajektorie wag | Etykieta wykresu |
| weight_deltas | przyrosty wag | Etykieta wykresu |
| executive_functions | funkcje wykonawcze | Psychologia poznawcza |
| cognitive_control | kontrola poznawcza | Psychologia poznawcza |
| inhibitory_control | kontrola hamowania | Psychologia poznawcza |
| response_inhibition | hamowanie reakcji | Psychologia poznawcza |
| cognitive_flexibility | elastyczność poznawcza | Psychologia poznawcza |
| processing_speed | szybkość przetwarzania | Psychologia poznawcza |
| sustained_attention | uwaga podtrzymana | Psychologia poznawcza |
| selective_attention | uwaga selektywna | Psychologia poznawcza |
| divided_attention | uwaga podzielna | Psychologia poznawcza |
| vigilance | czujność | Psychologia poznawcza |
| verbal_fluency | płynność słowna | Neuropsychologia |
| cognitive_reserve | rezerwa poznawcza | Neuropsychologia |
| neuroplasticity | neuroplastyczność | Neuropsychologia |
| long_term_potentiation | długotrwałe wzmocnienie synaptyczne | Neurofizjologia |
| long_term_depression | długotrwałe osłabienie synaptyczne | Neurofizjologia |
| hippocampal_binding | hipokampalne wiązanie informacji | Neuropsychologia |
| pattern_separation | separacja wzorców | Neuropsychologia |
| pattern_completion | uzupełnianie wzorców | Neuropsychologia |
| salience_detection | detekcja istotności | Psychologia poznawcza |
| affective_valence | walencja afektywna | Psychiatria / afekt |
| arousal_level | poziom pobudzenia | Psychiatria / afekt |
| anhedonia | anhedonia | Psychiatria |
| rumination | ruminacje | Psychiatria |
| psychomotor_retardation | spowolnienie psychoruchowe | Psychiatria |
| emotional_dysregulation | dysregulacja emocji | Psychiatria |
| depressive_symptom_severity | nasilenie objawów depresyjnych | Psychiatria |
| anxiety_symptom_severity | nasilenie objawów lękowych | Psychiatria |
| manic_symptom_severity | nasilenie objawów maniakalnych | Psychiatria |
| positive_symptoms | objawy pozytywne | Psychiatria |
| negative_symptoms | objawy negatywne | Psychiatria |
| cognitive_symptoms | objawy poznawcze | Psychiatria |
| remission_status | status remisji | Psychiatria |
| relapse_risk | ryzyko nawrotu | Psychiatria |
| treatment_response | odpowiedź na leczenie | Psychiatria |
| adverse_events | działania niepożądane | Psychiatria / farmakoterapia |
| medication_adherence | przestrzeganie farmakoterapii | Psychiatria / farmakoterapia |
| functional_connectivity | łączność funkcjonalna | Neuroobrazowanie |
| structural_connectivity | łączność strukturalna | Neuroobrazowanie |
| effective_connectivity | łączność efektywna | Neuroobrazowanie |
| resting_state | stan spoczynkowy | Neuroobrazowanie |
| task_evoked_activity | aktywność wywołana zadaniem | Neuroobrazowanie |
| blood_oxygen_level_dependent | sygnał BOLD (zależny od natlenowania krwi) | fMRI |
| hemodynamic_response_function | funkcja odpowiedzi hemodynamicznej | fMRI |
| region_of_interest | region zainteresowania | Neuroobrazowanie |
| voxel | woksel | Neuroobrazowanie |
| cortical_thickness | grubość kory | MRI strukturalne |
| gray_matter_volume | objętość istoty szarej | MRI strukturalne |
| white_matter_integrity | integralność istoty białej | DTI |
| fractional_anisotropy | anizotropia frakcyjna | DTI |
| mean_diffusivity | dyfuzyjność średnia | DTI |
| tractography | traktografia | DTI |
| source_localization | lokalizacja źródeł | EEG/MEG |
| event_related_potential | potencjał wywołany | EEG |
| mismatch_negativity | fala niezgodności (MMN) | EEG / potencjały wywołane |
| default_mode_network_connectivity | łączność sieci trybu domyślnego | Neuroobrazowanie |
| frontoparietal_network | sieć czołowo-ciemieniowa | Neuroobrazowanie |
| dorsal_attention_network | grzbietowa sieć uwagowa | Neuroobrazowanie |
| ventral_attention_network | brzuszna sieć uwagowa | Neuroobrazowanie |
| limbic_network | sieć limbiczna | Neuroobrazowanie |
| seed_based_analysis | analiza oparta na ziarnie | fMRI |
| independent_component_analysis | analiza składowych niezależnych | fMRI/EEG |
| graph_theory_metrics | miary teorii grafów | Neuroobrazowanie |
| small_worldness | małoświatowość sieci | Neuroobrazowanie |
| global_efficiency | efektywność globalna | Neuroobrazowanie |
| local_efficiency | efektywność lokalna | Neuroobrazowanie |
| clustering_coefficient | współczynnik grupowania | Neuroobrazowanie |
| path_length | długość ścieżki | Neuroobrazowanie |
| hubness | centralność węzłowa | Neuroobrazowanie |
| major_depressive_disorder | zaburzenie depresyjne nawracające (duża depresja) | Psychiatria — zaburzenia nastroju |
| persistent_depressive_disorder | dystymia (przewlekłe zaburzenie depresyjne) | Psychiatria — zaburzenia nastroju |
| bipolar_i_disorder | choroba afektywna dwubiegunowa typu I | Psychiatria — zaburzenia nastroju |
| bipolar_ii_disorder | choroba afektywna dwubiegunowa typu II | Psychiatria — zaburzenia nastroju |
| cyclothymic_disorder | zaburzenie cyklotymiczne | Psychiatria — zaburzenia nastroju |
| generalized_anxiety_disorder | zaburzenie lękowe uogólnione | Psychiatria — zaburzenia lękowe |
| panic_disorder | zaburzenie paniczne | Psychiatria — zaburzenia lękowe |
| agoraphobia | agorafobia | Psychiatria — zaburzenia lękowe |
| social_anxiety_disorder | zaburzenie lęku społecznego (fobia społeczna) | Psychiatria — zaburzenia lękowe |
| specific_phobia | fobia specyficzna | Psychiatria — zaburzenia lękowe |
| separation_anxiety_disorder | zaburzenie lęku separacyjnego | Psychiatria — zaburzenia lękowe |
| selective_mutism | mutyzm wybiórczy | Psychiatria — zaburzenia lękowe |
| obsessive_compulsive_disorder | zaburzenie obsesyjno-kompulsyjne | Psychiatria — spektrum OCD |
| body_dysmorphic_disorder | dysmorfofobia (zaburzenie dysmorficzne ciała) | Psychiatria — spektrum OCD |
| hoarding_disorder | zaburzenie zbieractwa | Psychiatria — spektrum OCD |
| trichotillomania | trichotillomania (zaburzenie wyrywania włosów) | Psychiatria — spektrum OCD |
| excoriation_disorder | dermatillomania (zaburzenie skubania skóry) | Psychiatria — spektrum OCD |
| posttraumatic_stress_disorder | zaburzenie stresowe pourazowe (PTSD) | Psychiatria — trauma i stres |
| acute_stress_disorder | ostre zaburzenie stresowe | Psychiatria — trauma i stres |
| adjustment_disorder | zaburzenie adaptacyjne | Psychiatria — trauma i stres |
| dissociative_identity_disorder | zaburzenie dysocjacyjne tożsamości | Psychiatria — zaburzenia dysocjacyjne |
| depersonalization_derealization_disorder | zaburzenie depersonalizacji/derealizacji | Psychiatria — zaburzenia dysocjacyjne |
| schizophrenia | schizofrenia | Psychiatria — zaburzenia psychotyczne |
| schizoaffective_disorder | zaburzenie schizoafektywne | Psychiatria — zaburzenia psychotyczne |
| schizophreniform_disorder | zaburzenie schizofreniformiczne | Psychiatria — zaburzenia psychotyczne |
| delusional_disorder | zaburzenie urojeniowe | Psychiatria — zaburzenia psychotyczne |
| brief_psychotic_disorder | krótkotrwałe zaburzenie psychotyczne | Psychiatria — zaburzenia psychotyczne |
| attention_deficit_hyperactivity_disorder | zespół nadpobudliwości psychoruchowej z deficytem uwagi (ADHD) | Psychiatria — neurorozwojowe |
| autism_spectrum_disorder | zaburzenie ze spektrum autyzmu | Psychiatria — neurorozwojowe |
| intellectual_disability | niepełnosprawność intelektualna | Psychiatria — neurorozwojowe |
| specific_learning_disorder | specyficzne zaburzenie uczenia się | Psychiatria — neurorozwojowe |
| tic_disorder | zaburzenie tikowe | Psychiatria — neurorozwojowe |
| tourette_disorder | zespół Tourette’a | Psychiatria — neurorozwojowe |
| oppositional_defiant_disorder | zaburzenie opozycyjno-buntownicze | Psychiatria — zaburzenia zachowania |
| conduct_disorder | zaburzenie zachowania | Psychiatria — zaburzenia zachowania |
| intermittent_explosive_disorder | zaburzenie eksplozywne przerywane | Psychiatria — zaburzenia kontroli impulsów |
| antisocial_personality_disorder | osobowość dyssocjalna (antyspołeczna) | Psychiatria — zaburzenia osobowości |
| borderline_personality_disorder | osobowość borderline (chwiejna emocjonalnie) | Psychiatria — zaburzenia osobowości |
| narcissistic_personality_disorder | osobowość narcystyczna | Psychiatria — zaburzenia osobowości |
| avoidant_personality_disorder | osobowość unikająca | Psychiatria — zaburzenia osobowości |
| obsessive_compulsive_personality_disorder | osobowość anankastyczna | Psychiatria — zaburzenia osobowości |
| alcohol_use_disorder | zaburzenie używania alkoholu | Psychiatria — uzależnienia |
| opioid_use_disorder | zaburzenie używania opioidów | Psychiatria — uzależnienia |
| stimulant_use_disorder | zaburzenie używania stymulantów | Psychiatria — uzależnienia |
| cannabis_use_disorder | zaburzenie używania konopi | Psychiatria — uzależnienia |
| gambling_disorder | zaburzenie hazardowe | Psychiatria — uzależnienia behawioralne |
| anorexia_nervosa | jadłowstręt psychiczny | Psychiatria — zaburzenia odżywiania |
| bulimia_nervosa | żarłoczność psychiczna | Psychiatria — zaburzenia odżywiania |
| binge_eating_disorder | zaburzenie z napadami objadania się | Psychiatria — zaburzenia odżywiania |
| avoidant_restrictive_food_intake_disorder | zaburzenie unikająco-ograniczające przyjmowanie pokarmu (ARFID) | Psychiatria — zaburzenia odżywiania |
| insomnia_disorder | zaburzenie bezsenności | Psychiatria — zaburzenia snu |
| hypersomnolence_disorder | zaburzenie nadmiernej senności | Psychiatria — zaburzenia snu |
| nightmare_disorder | zaburzenie koszmarów sennych | Psychiatria — zaburzenia snu |
| restless_legs_syndrome | zespół niespokojnych nóg | Psychiatria / neurologia — zaburzenia snu |
| somatic_symptom_disorder | zaburzenie z objawami somatycznymi | Psychiatria — zaburzenia somatyzacyjne |
| illness_anxiety_disorder | zaburzenie lękowe o zdrowie | Psychiatria — zaburzenia somatyzacyjne |
| conversion_disorder | zaburzenie konwersyjne (czynnościowe objawy neurologiczne) | Psychiatria — zaburzenia somatyzacyjne |
| premenstrual_dysphoric_disorder | przedmiesiączkowe zaburzenie dysforyczne | Psychiatria — zaburzenia nastroju |
| prolonged_grief_disorder | zaburzenie przedłużonej żałoby | Psychiatria — trauma i stres |
| mild_neurocognitive_disorder | łagodne zaburzenie neuropoznawcze | Neuropsychiatria |
| major_neurocognitive_disorder | duże zaburzenie neuropoznawcze (otępienie) | Neuropsychiatria |
| alzheimer_disease_dementia | otępienie w chorobie Alzheimera | Neuropsychiatria |
| vascular_dementia | otępienie naczyniowe | Neuropsychiatria |
| frontotemporal_dementia | otępienie czołowo-skroniowe | Neuropsychiatria |
| lewy_body_dementia | otępienie z ciałami Lewy’ego | Neuropsychiatria |

## Szablon nowego wpisu

Użyj poniższego formatu przy rozszerzaniu słownika:

| English (kod) | Polski (UI/opis) | Kontekst użycia |
|---|---|---|
| example_identifier | przykład etykiety | np. panel konfiguracji |
