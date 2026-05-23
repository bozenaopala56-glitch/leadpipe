# ZADANIA-BATCHE

Batche sa sekwencyjne. Wewnatrz batcha zadania ida po kolei, chyba ze zespol swiadomie rozdzieli niezalezne testy.

## Batch 1: Fundament kontraktu

Priorytet: P0  
Zaleznosci: brak

Zadania: F0-01, F0-02, F0-03, F0-04, F0-05, F0-06, F0-07, M1-01, M1-02, I1-03.

Kryterium: finalne 7 kampanii dziala w modelach, YAML, dashboardzie i testach.

## Batch 2: Modele, dedupe, DB

Priorytet: P0  
Zaleznosci: Batch 1

Zadania: M1-03, M1-04, M1-05, M1-06, M1-07, M1-08.

Kryterium: mozna zapisac i odczytac batch z leadami, scanami, decyzjami, trace i suppression.

## Batch 3: Import i fixture

Priorytet: P0  
Zaleznosci: Batch 2

Zadania: I1-01, I1-02, I1-04.

Kryterium: CSV tworzy batch, dane testowe pokrywaja glowne scenariusze.

## Batch 4: T0 HTTP/DNS/SSL

Priorytet: P0  
Zaleznosci: Batch 3

Zadania: T0-01, T0-02, T0-03, T0-04, T0-05, T0-06.

Kryterium: podstawowy scan domeny zwraca HTTP, DNS i TLS evidence.

## Batch 5: T0 HTML/robots/sitemap

Priorytet: P0  
Zaleznosci: Batch 4

Zadania: T0-07, T0-08, T0-09, T0-10.

Kryterium: aktywna strona ma snapshot HTML, meta, robots i sitemap signals.

## Batch 6: T0 performance i tech detection

Priorytet: P0  
Zaleznosci: Batch 5

Zadania: T0-11, T0-12, T0-13, T0-14, T0-15, T0-16.

Kryterium: T0 runner generuje sygnaly dla speed, CMS, WordPress, tracking i retry.

## Batch 7: T0.5 business enrichment

Priorytet: P1  
Zaleznosci: Batch 6

Zadania: E05-01, E05-02, E05-03, E05-04, E05-05, E05-06, E05-07, E05-08.

Kryterium: NIP/VAT/cache/merge dzialaja z mockami i nie blokuja dobrych leadow przy awarii API.

## Batch 8: T1 kontakt i struktura strony

Priorytet: P0  
Zaleznosci: Batch 6

Zadania: T1-01, T1-02, T1-03, T1-04, T1-05, T1-06, T1-07, T1-08.

Kryterium: parser wykrywa JSON-LD, meta, email, telefon i formularze.

## Batch 9: T1 CTA, industry i runner

Priorytet: P0  
Zaleznosci: Batch 8

Zadania: T1-09, T1-10, T1-11, T1-12, T1-13, T1-14.

Kryterium: T1 runner zwraca contactability, industry_fit, lead_value i sygnaly kampanii.

## Batch 10: Decision gates

Priorytet: P0  
Zaleznosci: Batch 7 i Batch 9

Zadania: G-01, G-02, G-03, G-04, G-05, G-06, G-07, G-08.

Kryterium: compliance, data quality, industry, scan health i contactability blokuja poprawnie.

## Batch 11: Campaign engine i suppression

Priorytet: P0  
Zaleznosci: Batch 10

Zadania: C-01, C-02, C-03, C-04, C-05, C-06.

Kryterium: 7 kampanii ma happy pathy, konflikty sa deterministyczne, suppression blokuje export.

## Batch 12: Evidence, trace, CSV, feedback

Priorytet: P0  
Zaleznosci: Batch 11

Zadania: EV-01, EV-02, DT-01, DT-02, CSV-01, CSV-02, FB-01, FB-02.

Kryterium: kazda decyzja ma trace i dowody, CSV eksportuje tylko dozwolone rekordy, feedback aktualizuje suppression.

## Batch 13: Dashboard QA

Priorytet: P1  
Zaleznosci: Batch 12

Zadania: D-01, D-02, D-03, D-04.

Kryterium: dashboard czyta realne dane i zapisuje approve/reject/manual.

## Batch 14: Dashboard kampanie, eksport, preview

Priorytet: P1  
Zaleznosci: Batch 13

Zadania: D-05, D-06, D-07, D-08, D-09, D-10.

Kryterium: QA widzi 7 kampanii, batch view, copywriting preview i eksport zgodny z backendem.

## Batch 15: T2 pilot

Priorytet: P1 high-risk  
Zaleznosci: Batch 12

Zadania: T2-01, T2-02, T2-03, T2-04, T2-05, T2-06, T2-07, T2-08.

Kryterium: T2 odpala sie selektywnie, zapisuje koszt i wynik jako signal/evidence.

## Batch 16: Kolejki i smoke

Priorytet: P1  
Zaleznosci: Batch 12, czesciowo Batch 15 dla T2 jobs

Zadania: Q-01, Q-02, DEP-01, DEP-02, QA-01, QA-02, QA-03, QA-04.

Kryterium: smoke batch przechodzi end-to-end z mockami i raportem.

## Batch 17: VM deploy

Priorytet: P1  
Zaleznosci: Batch 16

Zadania: VM-01, VM-02, VM-03, VM-04, VM-05, VM-06, VM-07, VM-08, VM-09, HERMES-01, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07, DEP-08.

Kryterium: VM uruchamia Postgres 16, Redis 7, dashboard, periodic scan, skill Hermesa i smoke E2E bez szukania konfiguracji poza repo.
