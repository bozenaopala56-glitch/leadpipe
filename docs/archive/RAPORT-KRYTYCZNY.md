# RAPORT KRYTYCZNY: T0/T0.5/T1/T2 Lead Scoring Pipeline

Data: 2026-05-23  
Kontekst: przeglad architektury po dodaniu pelnych regul decyzyjnych i korekcie T2 na kimi k2.5 vision przez opencode-go.

## 1. Co brakuje?

### 1.1. Ruleset jako artefakt konfiguracyjny

Dokumentacja opisuje reguly, ale przed codingiem trzeba zdecydowac, jak beda reprezentowane w repo:

- `config/rules/t2_eligibility.yml`;
- `config/rules/decision_gates.yml`;
- `config/rules/campaigns.yml`;
- `config/rules/suppression.yml`;
- `config/rules/evidence.yml`;
- `config/rules/feedback.yml`.

Bez tego developerzy wpisza progi bezposrednio w kodzie, a system szybko straci audytowalnosc.

### 1.2. Model scoringu i wyjasnialnosc

Brakuje formalnego kontraktu `DecisionTrace`: lista sprawdzonych regul, wynik kazdej reguly, powod odrzucenia lub wygranej. To jest potrzebne do QA, supportu i feedback loop.

Minimalny kontrakt:

- `lead_id`, `scan_id`, `ruleset_version`;
- `evaluated_rules[]`;
- `winning_rule`;
- `blocked_by[]`;
- `score_breakdown`;
- `evidence_ids`;
- `decision_reason`.

### 1.3. Manual QA workflow

MVP zaklada manualne QA, ale nie opisuje narzedzia ani procesu. Brakuje:

- statusow `qa_pending`, `qa_approved`, `qa_rejected`;
- powodow odrzucenia;
- sposobu poprawy subjectu bez zmiany rulesetu;
- eksportu tylko zatwierdzonych rekordow w pierwszych batchach.

### 1.4. Data protection checklist

Jest sekcja compliance, ale brakuje checklisty operacyjnej:

- kto ma dostep do raw HTML i kontaktow;
- jak usuwac dane po zadaniu usuniecia/sprzeciwu;
- jak propagowac opt-out do eksportow juz wygenerowanych;
- jak logowac bez danych osobowych.

### 1.5. Provider adapter dla T2

Po zmianie na kimi k2.5 vision przez opencode-go trzeba doprecyzowac:

- nazwe modelu w konfiguracji;
- endpoint base URL `https://opencode.ai/zen/go/v1`;
- format OpenAI-compatible vision z base64;
- timeouty, retry, cost accounting;
- mock adapter do testow bez sieci.

### 1.6. Dataset testowy

Brakuje zdefiniowanego zestawu fixture'ow:

- HTML dla strony aktywnej, wolnej, bez SSL, bez meta, z JSON-LD, z NIP, bez kontaktu;
- DNS fixture dla MX/SPF/DMARC;
- screenshot fixture dla T2;
- CSV feedback fixture.

Bez fixture'ow reguly beda trudne do testowania deterministycznie.

## 2. Co jest nadmiarowe?

### 2.1. FastAPI w Fazie 5

API jest przydatne, ale nie powinno byc laczone z T2 w tej samej fazie. T2 ma duze ryzyko operacyjne: Playwright, screenshot quality, provider vision, budzet. API mozna przesunac po pilocie T2.

Rekomendacja: Faza 5 tylko T2 pilot i QA. API jako Faza 6.

### 2.2. Zaawansowane CEIDG/KRS w MVP

Biala Lista VAT wystarczy jako wzmacniacz. CEIDG/KRS powinny byc opcjonalne, dopiero po potwierdzeniu, ze NIP extraction czesto znajduje poprawny NIP.

### 2.3. Zbyt wiele metryk dashboardowych przed feedbackiem

Prometheus/Grafana i dashboard mozna odlozyc. W MVP wystarczy:

- JSON logs;
- batch report;
- CSV decyzji;
- feedback import;
- prosty raport kampanii.

### 2.4. `QUALIFIED_CUSTOM_AUDIT` jako automatyczna kampania

To ryzykowny fallback. W MVP lepiej traktowac ja jako `manual_review`, dopoki nie ma recznie zatwierdzonych template'ow i dobrych wynikow reply.

### 2.5. T2 optional w duzej skali

Opcjonalne T2 do wzbogacania subjectow moze zjesc budzet bez dowodu ROI. W pierwszej iteracji T2 powinno obslugiwac tylko `must have` i mala probe eksperymentalna.

## 3. Ryzyka architektoniczne

### 3.1. False positives w kampaniach technicznych

Najwieksze ryzyko reputacyjne to wyslanie maila z bledna diagnoza. Przyklady:

- chwilowy timeout jako "strona nie dziala";
- brak DMARC jako "poczta nie dochodzi";
- wolny response z jednego pomiaru jako problem konwersji.

Mitigacja: wymagac dwoch dowodow dla kampanii P1/P2, zapisywac timestamp, nie uzywac absolutnych claimow w subjectach.

### 3.2. T2 jako kosztowna czarna skrzynka

Vision moze dawac ogolne, estetyczne opinie bez wartosci sprzedazowej. Moze tez roznic sie w wynikach przy podobnych screenshotach.

Mitigacja: prompt ma wymagac widocznych, konkretnych elementow i confidence. Wynik T2 nie moze samodzielnie nadpisywac twardych dowodow T0.

### 3.3. Suppression po aliasach

Firma moze miec wiele domen. Jesli suppression dziala tylko po emailu albo jednej domenie, system moze ponownie dotknac ten sam podmiot.

Mitigacja: NIP jako najsilniejszy klucz, aliasy domen, cooldown na poziomie firmy.

### 3.4. Publiczne endpointy i rate limiting

Biala Lista VAT i strony firm moga zwalniac lub blokowac ruch. Batch 5000 leadow moze miec dlugi ogon timeoutow.

Mitigacja: cache, niski RPS, statusy `partial`, retry tylko dla transient, brak blokowania batcha przez enrichment.

### 3.5. Brak realnego feedbacku

Bez feedbacku scoring stanie sie eleganckim klasyfikatorem technicznym, nie systemem sprzedazowym.

Mitigacja: feedback import musi byc w MVP, nawet jesli mailing jest manualny.

## 4. Luki w dokumentacji dla developera

Brakuje nastepujacych decyzji technicznych:

- dokladna struktura repo i modulow;
- schemat tabel SQL, indeksy i migracje;
- format `Signal`, `Evidence`, `DecisionTrace` w JSON;
- format plikow YAML dla regul;
- mapowanie bledow na `transient`, `permanent`, `compliance`, `parser_error`;
- nazwy statusow jobow i leadow;
- format CSV importu, eksportu i feedbacku;
- strategia testow fixture-based;
- sposob mockowania HTTP, DNS, Bialej Listy VAT i opencode-go;
- wersjonowanie rulesetu i migracja decyzji po zmianie progow.

Developer moze zaczac kodzic fundament danych, ale nie powinien zaczynac campaign engine bez zamkniecia formatu rulesetu i trace.

## 5. Rekomendacje przed codingiem

### 5.1. Zamknac kontrakty danych

Przed kodem ustalic:

- modele Pydantic;
- tabele Postgres;
- `DecisionTrace`;
- `ruleset_version`;
- CSV schemas.

To jest najwazniejsze, bo zmiany po implementacji decision engine beda kosztowne.

### 5.2. Zrobic config-first decision engine

Reguly kampanii, suppression, evidence i T2 powinny byc ladowane z YAML. Kod ma byc silnikiem ewaluacji, a nie miejscem przechowywania progow.

### 5.3. Ograniczyc MVP

MVP powinno obejmowac:

- import/dedupe;
- T0;
- T0.5 NIP + Biala Lista jako opcjonalny enrichment;
- T1 contact/content;
- decision gates;
- 5-7 kampanii automatycznych;
- suppression;
- CSV export;
- feedback import.

Do manual review w MVP przesunac:

- `QUALIFIED_CUSTOM_AUDIT`;
- konflikty kampanii;
- leady bez emaila;
- branze z niepewnym fit.

### 5.4. Oddzielic T2 od API

Faza po MVP powinna byc:

1. T2 must-have pilot na 50-100 leadach.
2. Pomiar uplift.
3. Dopiero potem API/CRM.

### 5.5. Zbudowac QA na poczatku

Nawet prosty CSV `qa_decisions.csv` z kolumnami `approved`, `rejected_reason`, `correct_campaign` da szybki feedback i zabezpieczy pierwsze wysylki.

### 5.6. Ustalic jezyk claimow

Przed wysylka trzeba zatwierdzic biblioteke bezpiecznych sformulowan. System powinien generowac subjecty i evidence w trybie ostroznym:

- "wyglada na";
- "w skanie z dnia";
- "moze wplywac";
- "warto sprawdzic";
- unikac "nie dziala", chyba ze dowod jest twardy i powtorzony.

## 6. Decyzja rekomendowana

Nie zaczynac od T2 ani API. Najpierw zaimplementowac deterministyczny core: import, T0, T1, ruleset, evidence, suppression i feedback. T2 ma wejsc dopiero jako rule-based resolver dla niejednoznacznych, wartosciowych leadow, z kimi k2.5 vision przez opencode-go i twardym budget guard.
