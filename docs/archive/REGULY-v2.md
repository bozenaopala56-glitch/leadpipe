# REGULY: T0/T0.5/T1/T2 Lead Scoring Pipeline

Data: 2026-05-23  
Wersja rulesetu: `ruleset-2026-05-23-v2`  
Zakres: kwalifikacja T2, bramki decyzyjne, kampanie, suppression, evidence, feedback, rate limiting, import i deduplikacja.

## 1. Zasady nadrzedne

Reguly sa jawne, wersjonowane i audytowalne. Pipeline konczy sie na decyzji, prostym evidence_text, copywritingu i manualnym QA. System nie wysyla automatycznie maili w MVP.

Kazda decyzja musi zapisac:

- `ruleset_version`;
- `rule_key`;
- decyzje: `send`, `skip`, `manual_review`, `t2_required`, `retry`;
- uzyte sygnaly i `evidence_ids`;
- wynik liczbowy, confidence i powod.

W MVP `send` oznacza "gotowe do manualnego QA", nie auto-send. Wszystkie rekordy eksportowane do copywritingu i dashboardu maja finalnie przejsc przez `manual_review` albo reczne zatwierdzenie.

Priorytet globalny:

| Priorytet | Klasa | Efekt |
|---:|---|---|
| 1 | Compliance and suppression | Blokuje eksport niezaleznie od wyniku scoringu. |
| 2 | Data quality | Blokuje, kieruje do retry albo manual review, gdy dane sa niewiarygodne. |
| 3 | Safety and contactability | Chroni reputacje domeny wysylkowej i jakosc kontaktu. |
| 4 | Campaign decision | Wybiera kampanie i prosty opis dowodow. |
| 5 | T2 resolver | Rozstrzyga niejednoznaczne przypadki, jesli koszt ma sens. |
| 6 | Feedback calibration | Zmienia progi dopiero po minimalnej probce. |

Skale:

- `confidence`: 0.00-1.00, pewnosc konkretnego sygnalu lub decyzji.
- `contactability`: 0-100, jak realnie mozna skontaktowac sie z leadem.
- `industry_fit`: 0-100, dopasowanie do uslug tworzenia, przebudowy i opieki nad stronami.
- `evidence_strength`: 0-100, suma wazona dowodow kampanii.
- `lead_value`: 0-100, potencjal wartosciowy na podstawie branzy, B2B, eksportu, produkcji, wielkosci i widocznych uslug.

## A. T2 Eligibility Rules

### A1. Cel

T2 ma odpowiadac tylko na pytania, ktorych T0/T0.5/T1 nie rozstrzygaja: czy strona wyglada nieprofesjonalnie, czy trust/CTA sa slabe, czy argument redesign/rework jest mocniejszy niz bezpieczna kampania wspierajaca.

T2 nie sluzy do wybierania "najlepszych X%" leadow ani do wzbogacania kazdej personalizacji. Jest uruchamiane przez reguly decyzyjne i budzet.

### A2. Dane wejsciowe

| Wejscie | Zrodlo | Uwagi |
|---|---|---|
| `t0_confidence` | T0 | Pewnosc stanu strony i problemow technicznych. |
| `t1_confidence` | T1 | Pewnosc opisu firmy, kontaktu, branzy i CTA. |
| `contactability` | T1/import | Email, telefon, formularz, rola kontaktu. |
| `industry_fit` | T0.5/T1 | Dopasowanie do MSP uslug/produkcji/B2B. |
| `lead_value` | T0.5/T1 | Potencjal koszyka i strategiczne branze. |
| `campaign_candidate` | Campaign Engine | Najlepsza kampania przed T2. |
| `evidence_strength` | Evidence Engine | Sila dowodow przed T2. |
| `cost_budget_remaining` | T2 Budget | Budzet dzienny i batcha. |
| `screenshottable` | Playwright quality | Czy strona da sie poprawnie zrzucic. |

### A3. Progi bazowe

| Metryka | Skip | Optional | Required |
|---|---:|---:|---:|
| `contactability` | < 40 | 55-69 | >= 70 przy ambiguous |
| `industry_fit` | < 45 | 60-74 | >= 75 przy ambiguous |
| `lead_value` | < 45 | 60-74 | >= 75 przy campaign tie |
| `t0_confidence` | < 0.45 | 0.45-0.69 | >= 0.70 z problemem, ale bez hooka |
| `t1_confidence` | < 0.45 | 0.45-0.69 | < 0.70 przy dobrym T0 |
| `campaign_confidence` | < 0.55 | 0.55-0.74 | 0.55-0.74 i brak rozstrzygniecia |
| `evidence_strength` | < 45 | 45-69 | < 70 przy lead_value >= 75 |

Must-have T2 nie powinno blokowac dobrych leadow przez zbyt sztywne warunki. Gdy jeden z progow jest minimalnie niespelniony, ale `lead_value >= 85` i brak suppression, decyzja moze byc `manual_review` zamiast `skip_t2`.

### A4. Reguly must have

| Rule key | Warunek | Decyzja | Przyklad |
|---|---|---|---|
| `T2_MUST_AMBIGUOUS_HOOK` | `t0_confidence >= 0.70`, T0 wskazuje problem biznesowo istotny, ale `t1_confidence < 0.70` i brak 2 dowodow kampanii | `t2_required` | T0 widzi wolna strone, T1 nie umie okreslic oferty ani CTA. |
| `T2_MUST_CAMPAIGN_TIE` | Dwie kampanie maja wynik w odleglosci <= 8 pkt, jedna to `REDESIGN_AUDIT` albo `CARE_PLAN_MAINTENANCE`, `lead_value >= 70` | `t2_required` | WordPress dziala, ale DOM sugeruje slabe CTA; T2 rozstrzyga care plan vs redesign. |
| `T2_MUST_VISUAL_DECISION_BLOCKER` | Brak twardych awarii, `industry_fit >= 75`, `contactability >= 70`, `campaign_confidence 0.55-0.74` | `t2_required` | Dobry producent B2B, strona aktywna, ale hook techniczny zbyt slaby. |
| `T2_MUST_CONFLICTING_EVIDENCE` | T0/T1 maja sprzeczne sygnaly dla kampanii o priorytecie >= 3 i nie ma suppression | `t2_required` albo `manual_review` | Meta wyglada nowoczesnie, ale HTML/CTA ubogie; potrzebny screenshot. |

### A5. Reguly optional

| Rule key | Warunek | Decyzja | Efekt |
|---|---|---|---|
| `T2_OPT_UPGRADE_CARE_TO_REDESIGN` | `CARE_PLAN_MAINTENANCE` ma confidence 0.65-0.80, brak awarii P1/P2, `lead_value >= 65` | `manual_review` albo `t2_required` gdy budzet wolny | T2 moze podbic do `REDESIGN_AUDIT`. |
| `T2_OPT_HIGH_VALUE_LOW_RISK` | `lead_value >= 85`, `industry_fit >= 75`, `campaign_confidence >= 0.70`, brak twardych problemow | `manual_review` albo `t2_required` gdy budzet wolny | Ulepszenie decyzji dla konta wartosciowego. |

Usunieto optional T2 tylko do wzbogacania subjectu. Copywriting jest osobnym systemem, a T2 ma rozstrzygac decyzje, nie produkowac ladniejsze maile.

### A6. Reguly skip

| Rule key | Warunek | Decyzja |
|---|---|---|
| `T2_SKIP_SUPPRESSED` | Jakikolwiek aktywny suppression P1 | `skip_t2` |
| `T2_SKIP_NO_CONTACT` | `contactability < 40` i brak manualnego opiekuna | `skip_t2` |
| `T2_SKIP_STRONG_CAMPAIGN` | Kampania ma `campaign_confidence >= 0.82` i >= 2 dowody | `skip_t2` |
| `T2_SKIP_LOW_FIT` | `industry_fit < 45` albo lead spoza rynku | `skip_t2` |
| `T2_SKIP_NOT_SCREENSHOTTABLE` | Screenshot pusty, zablokowany, captcha-only lub consent wall > 70% viewportu | `skip_t2_manual_review` |

### A7. Reguly kosztowe

| Limit | Wartosc startowa | Efekt |
|---|---:|---|
| Dzienny budzet T2 | 5 USD | Po przekroczeniu: tylko `manual_review`, bez nowych calli. |
| Budzet batcha | 2% zakladanej wartosci batcha albo 5 USD, nizsza wartosc wygrywa | Chroni piloty i duze importy. |
| Limit per provider call | 0.02 USD | Call powyzej limitu blokuje kolejne T2 i wymaga rewizji konfiguracji. |
| Limit per lead | 2 screenshoty + 1 prompt bazowy + opcjonalny 1 prompt doglebny + 1 retry transportowy | Brak petli kosztowej. |
| Maks. T2 w batchu bez feedbacku | 100 leadow | Dopiero po pomiarze uplift mozna podniesc. |
| Rezerwa must have | 50% budzetu T2 | Optional nie moze zuzyc budzetu must-have. |
| Ostrzezenie budzetowe | Optional zuzylo > 30% budzetu albo narusza rezerwe must-have | Zatrzymac optional, kontynuowac tylko must-have lub manual review. |

### A8. Screenshoty i prompty T2

T2 uzywa dwoch screenshotow i jednego promptu bazowego na oba obrazy. Drugi prompt jest opcjonalny tylko wtedy, gdy prompt 1 zwraca wynik niejednoznaczny.

Opcje screenshotow:

| Opcja | Screenshot 1 | Screenshot 2 | Kiedy |
|---|---|---|---|
| A | Strona glowna desktop | Podstrona kontakt/o nas/oferta desktop | Gdy T1 znajdzie sensowna podstrone. |
| B | Strona glowna desktop | Strona glowna mobile | Gdy podstrona jest niepewna albo mobile moze zmienic ocene. |

Prompt 1: ocena ogolna widocznych problemow, trust, CTA, czytelosc oferty i confidence.  
Prompt 2: doglebna analiza tylko dla wyniku niejednoznacznego, konfliktu kampanii albo wysokiego lead_value.

## B. Decision Gates

### B1. Cel

Bramki ustalaja pierwsza dozwolona decyzje. Sa sprawdzane w stalej kolejnosc, zeby compliance i jakosc danych wygrywaly z atrakcyjnym scoringiem.

### B2. Kolejnosc bramek

12 bramek v1 zostalo scalonych do 7, bez utraty audytowalnosci. Szczegolowe powody sa zapisywane w `DecisionTrace.blocked_by[]`.

| Priorytet | Gate | Decyzja | Progi |
|---:|---|---|---|
| 1 | `GATE_COMPLIANCE` | `skip` | Opt-out, suppression, forbidden source, aktywny klient/deal, cooldown. |
| 2 | `GATE_DATA_QUALITY` | `skip/manual_review` | Brak domeny/NIP/kontaktu po normalizacji, nie-firma, marketplace/katalog/portal, brak Polski lub obslugi PL. |
| 3 | `GATE_INDUSTRY_FIT` | `skip/manual_review` | Wykluczona branza, potencjalny partner, niski fit albo niepewna klasyfikacja. |
| 4 | `GATE_SCAN_HEALTH` | `retry/manual_review/skip` | Transient HTTP/DNS/TLS retry <= 1; po retry manual dla wartosciowych leadow, inaczej skip. |
| 5 | `GATE_CONTACTABILITY` | `manual_review/skip` | < 40 skip, 40-54 manual, >= 55 moze isc dalej. |
| 6 | `GATE_EVIDENCE_AND_T2` | `manual_review/t2_required` | Kampania bez minimalnego evidence albo reguly A wymagaja T2. |
| 7 | `GATE_CAMPAIGN_READY` | `manual_review` | Kampania spelnia prog, ale MVP wymaga recznego QA przed wysylka. |

### B3. Decyzje

| Decyzja | Kiedy | Przyklad |
|---|---|---|
| `skip` | Compliance, suppression, niska jakosc danych, brak kontaktu, niski fit | Opt-out, brak domeny, prywatny blog. |
| `retry` | Blad przejsciowy i nie przekroczono limitu | 503, 429, timeout, SERVFAIL. |
| `manual_review` | Domyslna decyzja koncowa dla eksportu i QA | Kampania gotowa, ale czeka na czlowieka. |
| `t2_required` | Bez obrazu nie da sie wybrac kampanii albo potwierdzic redesign | Care plan vs redesign przy dobrym leadzie. |
| `send` | Decyzja logiczna "gotowe po QA"; w MVP nie oznacza auto-send | Brak HTTPS + email + firma PL po recznym zatwierdzeniu. |

### B4. Cooldown

| Zdarzenie | Cooldown |
|---|---:|
| Dowolna kampania wyslana do leadu | 90 dni |
| Ta sama kampania do tej samej firmy | 180 dni |
| Po `positive_reply` | Brak nowych kampanii, tylko follow-up handlowy |
| Po `soft_bounce` | 14 dni i maks. 1 ponowna proba na ten email |
| Po `hard_bounce` | Email permanentnie, firma 180 dni chyba ze jest nowy kontakt |
| Po `opt_out` | Permanentnie dla emaila, domeny i NIP |
| Po `manual_reject` | 180 dni lub do zmiany danych |

## C. Campaign Rules

### C1. Cel

Wybrac jedna z 6 kampanii skoncentrowanych na tworzeniu, przebudowie i utrzymaniu stron. Kampania musi miec wystarczajacy confidence, minimalne evidence i prosty faktograficzny opis dowodow. Subject i tresc maila generuje osobny system copywritingu.

### C2. Kampanie i wymagania

| Priorytet | Kampania | Rola | Wymagane sygnaly | Prog confidence | Min evidence |
|---:|---|---|---|---:|---:|
| 1 | `REDESIGN_AUDIT` | Glowna | T2: slaby trust/CTA/design albo T1 DOM: brak CTA/social proof + slaba struktura | 0.76 z T2, 0.68 manual bez T2 | 2 |
| 2 | `NEW_WEBSITE` | Glowna | Brak strony, landing/profil social zamiast strony, placeholder, bardzo uboga wizytowka | 0.74 | 2 |
| 3 | `SECURITY_SSL` | Wspierajaca | T0: `ssl.no` lub cert invalid; opcjonalnie brak HSTS/CSP | 0.72 | 2 |
| 4 | `SEO_VISIBILITY` | Wspierajaca | T0/T1: noindex, brak title/meta, sitemap/robots problem, canonical chaos | 0.68 | 2 |
| 5 | `CARE_PLAN_MAINTENANCE` | Opieka | T0/T1: WordPress/CMS/plugin hints, brak awarii P1/P2, firma aktywna | 0.65 | 1 |
| 6 | `QUALIFIED_CUSTOM` | Manual | Dobry fit, dobry kontakt, brak jednoznacznej kampanii automatycznej | 0.65 | 2 |

Usuniete z v2:

- `SITE_DOWN_RESCUE`: za rzadkie i zwykle trafia do `NEW_WEBSITE` albo `manual_review`.
- `EMAIL_DELIVERABILITY_FIX`: poza zakresem uslug tworzenia stron.
- `PERFORMANCE_CONVERSION_FIX`: wchloniete jako dowod wspierajacy dla `REDESIGN_AUDIT`, nie osobna kampania.

### C3. Scoring kampanii

Wynik kampanii:

```text
campaign_score =
  0.45 * evidence_strength +
  0.20 * signal_confidence +
  0.15 * contactability +
  0.15 * industry_fit +
  0.05 * lead_value
  - penalties
```

Kary:

| Kara | Wartosc |
|---|---:|
| Brak emaila, jest tylko formularz | -8 |
| Brak firmy z T0.5/T1 | -6 |
| Dowod starszy niz TTL | -12 |
| Sprzeczne dowody | -15 i `manual_review` |
| Kampania opiera sie na jednym slabym dowodzie | -10 |

### C4. Priorytety konfliktow

Gdy wiele kampanii pasuje:

1. `NEW_WEBSITE` wygrywa, gdy strona faktycznie nie istnieje albo jest placeholderem.
2. `SECURITY_SSL` wygrywa nad SEO i care, gdy problem z HTTPS/certyfikatem jest twardy.
3. `REDESIGN_AUDIT` wygrywa nad `CARE_PLAN_MAINTENANCE`, tylko gdy T2 confidence >= 0.76 lub manual approve.
4. `SEO_VISIBILITY` wygrywa nad care, gdy noindex/meta/canonical maja confidence >= 0.70.
5. `CARE_PLAN_MAINTENANCE` jest bezpieczna kampania wspierajaca dla aktywnych CMS bez twardych problemow.
6. `QUALIFIED_CUSTOM` jest fallbackiem manualnym dla dobrych leadow bez twardego hooka.

### C5. Evidence text rules

System generuje tylko prosty, faktograficzny `evidence_text`. Nie implementuje claim language rules ani pelnego copywritingu.

| Kampania | Evidence focus | Wymagane dowody |
|---|---|---|
| `REDESIGN_AUDIT` | Widoczne problemy trust/CTA/struktury albo DOM wskazujacy slaba prezentacje oferty | T2 visual + T1 CTA/trust albo manual |
| `NEW_WEBSITE` | Brak pelnej strony, placeholder, strona jednostronicowa bez podstawowych informacji | HTTP/HTML + T1 content |
| `SECURITY_SSL` | HTTPS/certyfikat i widoczny kontekst strony | Brak HTTPS/cert invalid + aktywna strona |
| `SEO_VISIBILITY` | Indeksacja i podstawowe elementy widocznosci | Noindex/meta/sitemap/canonical |
| `CARE_PLAN_MAINTENANCE` | CMS i sygnaly potrzeby opieki | CMS/WordPress + brak krytycznych awarii |
| `QUALIFIED_CUSTOM` | Fit + neutralny fakt o stronie | Fit + 2 neutralne dowody |

## D. Suppression Rules

### D1. Cel

Suppression chroni compliance, reputacje i relacje handlowe. Dziala przed scoringiem.

### D2. Zrodla suppression

| Zrodlo | Zakres | Typ |
|---|---|---|
| Opt-out | email, domena, NIP, telefon | Auto permanent |
| Hard bounce | email permanent, firma 180 dni | Auto |
| Soft bounce | email 14 dni | Auto |
| CRM customers | NIP/domena/email | Auto lub account owner |
| Active opportunities | firma/domena | Auto |
| Bezposrednia konkurencja | agencje digital, SEO, web design, hosting, marketing | Auto przy confidence >= 0.90 |
| Potential partner | software house, integrator, freelancer IT robiacy strony dla klientow | Manual review, nie auto suppression |
| Branża IT niepewna | SaaS vendors, software house, web design, SEO, ads, hosting | Manual wedlug confidence |
| Wewnetrzne blacklisty | domena, NIP, email | Auto |
| Role risky | abuse@, security@, privacy@, rodo@ | Suppress email, nie firme |
| Zrodla zakazane | scraping naruszajacy regulamin, lista bez podstawy | Auto batch suppression |

### D3. Auto vs manual

| Warunek | Decyzja |
|---|---|
| Opt-out, hard bounce, klient, aktywny deal | Auto suppression |
| Bezposrednia konkurencja confidence >= 0.90 | Auto suppression |
| Konkurencja/IT confidence 0.65-0.89 | Manual review |
| Potential partner confidence >= 0.65 | Manual review z kategoria `potential_partner` |
| Branza niepewna, ale lead_value >= 80 | Manual review |
| Brak kontaktu, ale firma strategiczna | Manual research |

### D4. Cooldown per lead i kampania

| Poziom | Regula |
|---|---|
| Lead/company | 90 dni od dowolnej wysylki. |
| Kampania | 180 dni dla tej samej kampanii. |
| Kontakt email | 90 dni, chyba ze odpowiedzial pozytywnie. |
| Domena | 90 dni, obejmuje aliasy i subdomeny. |
| NIP | 180 dni, obejmuje wszystkie domeny firmy. |

### D5. Opt-out

Opt-out blokuje w czasie rzeczywistym. SLA: suppression zapisane do 5 minut od importu feedbacku albo webhooka. Retencja opt-out jest bezterminowa. Opt-out z emaila firmowego blokuje email, domene i NIP, chyba ze recznie oznaczono, ze dotyczy tylko osoby.

## E. Evidence Rules

### E1. Cel

Evidence musi pozwolic odtworzyc i obronic personalizacje. Dowody sa minimalne, konkretne i biznesowe.

### E2. Minimalne evidence per kampania

| Kampania | Min dowody | Min confidence dowodu | Laczenie |
|---|---:|---:|---|
| `REDESIGN_AUDIT` | 2 | 0.76 dla T2, 0.70 dla T1 | AND: visual + CTA/trust albo manual |
| `NEW_WEBSITE` | 2 | 0.70 | AND: HTTP/HTML + content/contact |
| `SECURITY_SSL` | 2 | 0.72 | AND/OR: SSL/cert + trust/security header |
| `SEO_VISIBILITY` | 2 | 0.60 | OR weighted, noindex jako silny dowod |
| `CARE_PLAN_MAINTENANCE` | 1 | 0.60 | OR: CMS lub maintenance risk |
| `QUALIFIED_CUSTOM` | 2 | 0.65 | Weighted: fit + neutralny problem |

### E3. Laczenie dowodow

| Tryb | Zastosowanie |
|---|---|
| AND | Kampanie z mocnym claimem, gdzie dowod musi byc odporny na false positive. |
| OR | Kampanie z wieloma rownowaznymi problemami. |
| Weighted | SEO, care i custom. |
| Veto | Sprzeczny albo ryzykowny dowod blokuje automatyczna gotowosc i kieruje do manual review. |

### E4. Evidence text

Format:

```text
Na stronie {domena} zaobserwowano {fakt}. W skanie z {data} system potwierdzil: {konkretna wartosc}.
```

Zasady:

- pisac faktograficznie, bez pelnego copywritingu;
- nie mowic "blad krytyczny", jesli dowod jest umiarkowany;
- nie obiecywac liczby problemow bez liczby dowodow;
- nie ujawniac technicznych szczegolow, ktore brzmia jak pentest;
- `evidence_text` max 220 znakow w CSV, pelny opis w bazie.

## F. Feedback Rules

### F1. Cel

Feedback w MVP sluzy glownie compliance i podstawowej kalibracji. Pipeline konczy sie na manual_review i copywritingu, wiec rozbudowana analityka open/click/meeting/deal jest future scope.

### F2. Interpretacja zdarzen MVP

| Event | Interpretacja | Akcja |
|---|---|---|
| `bounce_hard` | Email nie istnieje lub domena odrzuca stale | Suppress email permanentnie, firma 180 dni. |
| `bounce_soft` | Tymczasowy problem skrzynki/provider | Cooldown email 14 dni, maks. 1 retry. |
| `positive_reply` | Kampania trafiona | Blokada automatycznych kampanii, przekazanie do CRM/manual sales. |
| `negative_reply` | Slaby fit, zly hook albo sprzeciw bez formalnego opt-out | Cooldown 180 dni, analiza false positive. |
| `opt_out` | Compliance | Permanent suppression. |

### F3. Future feedback

Do pozniejszej iteracji:

- opens;
- clicks;
- neutral replies;
- meeting booked;
- deal created/won/lost;
- revenue attribution;
- T2 uplift na grupie kontrolnej.

### F4. Aktualizacja suppression

| Feedback | Suppression |
|---|---|
| Hard bounce | Email permanent, domena/NIP 180 dni. |
| Soft bounce | Email 14 dni. |
| Negative reply "nie piszcie" | Opt-out permanent. |
| Negative reply bez opt-out | 180 dni company cooldown. |
| Positive reply | Blokada automatycznych kampanii, przekazanie do CRM/manual sales. |

### F5. Recalibracja scoringu

Zmiany progow wymagaja minimalnej probki:

| Zmiana | Minimalna probka |
|---|---:|
| Korekta evidence_text/copywriting handoff | 100 wysylek i >= 5 reply dla kampanii |
| Korekta progu kampanii | 200 wysylek i >= 20 reply albo 10 positive replies |
| Korekta suppression branzy | 50 recznych decyzji QA |
| Korekta T2 eligibility | 100 leadow z T2 i 100 podobnych bez T2 |
| Usuniecie kampanii z MVP | 300 wysylek i positive reply rate < 0.5% |

Nie zmieniamy progow po samych open rates. Open/click analytics sa future scope.

## G. Rate Limiting i Bezpieczenstwo

### G1. Cel

Pipeline ma byc umiarkowanym skanerem publicznych informacji, nie pentestem i nie crawlerem wysokiej intensywnosci.

### G2. Concurrency i RPS

| Obszar | Limit startowy | Maks. po kalibracji |
|---|---:|---:|
| HTTP global | 50 concurrent | 100 |
| HTTP per registered domain | 1 concurrent | 1 |
| HTTP per host | 1 rps | 2 rps |
| DNS global | 100 concurrent | 200 |
| Biala Lista VAT | 5 rps | 10 rps po obserwacji |
| Playwright T2 | 2 contexts | 4 contexts |
| opencode-go/kimi T2 | 2 concurrent calls | Wedlug budzetu i rate limitu |

User-Agent:

```text
MeNETLeadScanner/1.0 (+kontakt@menet.pl; B2B site audit)
```

### G3. Koszty T2

| Limit | Wartosc |
|---|---:|
| opencode-go/kimi T2 dziennie | 5 USD |
| opencode-go/kimi per call | 0.02 USD |
| Retry providera | 1 retry tylko dla bledow transportowych |
| Przekroczenie limitu | Stop nowych calli, decyzja `manual_review` |

### G4. Retry classes

| Klasa | Przyklady | Retry |
|---|---|---|
| Transient | timeout, reset, 408, 429, 503, SERVFAIL | 1 retry, backoff 2-10 s + jitter |
| Permanent | NXDOMAIN, 404 main domain, invalid input | Bez retry |
| Compliance | robots explicit block dla crawl, opt-out, forbidden source | Bez retry, suppression/manual |
| Parser error | bledny HTML/JSON-LD | Bez retry network, fallback parser |
| T2 transport | 5xx provider, timeout | 1 retry |
| T2 quality | blank screenshot, captcha, blocked | Bez model call, manual/skip |

### G5. Cache TTL

| Dane | TTL |
|---|---:|
| DNS positive | 7 dni |
| DNS negative | 1 dzien |
| HTTP snapshot | 30 dni |
| HTTP snapshot dla eksportu kampanii | 7 dni |
| SSL/cert | 30 dni albo do `not_after`, nizsza wartosc |
| robots/sitemap | 30 dni |
| tech detection | Do zmiany HTML hash |
| NIP extraction | Do zmiany HTML hash |
| Biala Lista VAT | 30 dni |
| T1 contact parse | Do zmiany HTML hash |
| T2 screenshot | 30 dni |
| T2 vision result | 30 dni, invalidacja po nowym screenshot hash |
| Suppression | Wedlug typu, opt-out permanent |
| Feedback events | Permanent audit |

## H. Import i Deduplikacja

### H1. Cel

Jeden podmiot ma dostac maksymalnie jedna aktywna decyzje kampanijna w cooldownie, nawet jesli wystepuje pod kilkoma domenami, aliasami lub kontaktami.

### H2. Definicja duplikatu

| Klucz | Regula |
|---|---|
| Domena | Ten sam `registered_domain` po normalizacji `www`, scheme, slash, case. |
| NIP | Ten sam poprawny NIP po checksum. Najsilniejszy klucz firmy. |
| REGON/KRS | Ten sam identyfikator, gdy dostepny. |
| Email | Ten sam email lower-case, plus alias normalization tylko dla znanych domen mailboxow. |
| Telefon | Ten sam numer E.164 PL po usunieciu spacji i separatorow. |
| Firma + adres | Fuzzy match tylko do manual review, nie auto-merge w MVP. |

### H3. Ktory rekord wygrywa

Konfiguracja importu musi miec `source_priority`, zeby rozstrzygnac konflikty miedzy zrodlami.

Przyklad:

```yaml
import_sources:
  crm:
    source_priority: 100
  manual_partner_list:
    source_priority: 80
  cold_csv:
    source_priority: 50
  scraped_public:
    source_priority: 20
```

| Sytuacja | Zwyciezca |
|---|---|
| Jeden rekord ma wyzszy `source_priority` i nie lamie suppression | Rekord z wyzszym priorytetem jako primary, drugi jako source alias. |
| Jeden rekord ma NIP, drugi nie | Rekord z NIP, chyba ze nizszy `source_priority` jest oznaczony jako nieufny. |
| Oba maja NIP i rozne domeny | Tworzymy jedna firme i aliasy domen. |
| Jeden rekord ma kontakt email, drugi nie | Rekord z kontaktem jako primary, drugi jako alias/source. |
| Rozne kontakty dla tej samej firmy | Zachowac wszystkie, oznaczyc primary wedlug jakosci i `source_priority`. |
| Nowszy import ma bogatsze dane | Update enrichment, nie kasowac historii. |
| Konflikt nazwy firmy | VAT/KRS wygrywa nad HTML, HTML wygrywa nad importem. |

Contact quality:

| Kontakt | Punkty |
|---|---:|
| Imienny email w domenie firmy | 100 |
| Rola handlowa/kontaktowa w domenie firmy | 85 |
| `biuro@`, `kontakt@` w domenie firmy | 75 |
| Formularz kontaktowy | 55 |
| Telefon firmowy | 50 |
| Gmail/Onet/WP bez domeny firmowej | 35 |
| Abuse/privacy/security | 0 dla outreach |

### H4. Aliasy domen

Alias domeny to:

- redirect 301/302 do tej samej domeny kanonicznej;
- `www` i non-`www`;
- domena z tym samym NIP w stopce/VAT;
- domena produktowa tej samej firmy, gdy T1/VAT potwierdza wlasciciela.

Nie scalac automatycznie:

- franczyz i oddzialow bez wspolnego NIP;
- marketplace i profili social jako domeny firmy;
- domen z tym samym szablonem strony, ale bez identyfikatora firmy.

### H5. Przyklady

| Input A | Input B | Decyzja |
|---|---|---|
| `https://www.firma.pl/` | `firma.pl` | Duplikat domeny. |
| `firma.com.pl` z NIP X | `firma.pl` z NIP X | Jedna firma, dwa aliasy. |
| `kontakt@firma.pl` | `biuro@firma.pl` | Dwa kontakty jednej firmy. |
| Ten sam telefon, rozne NIP | Manual review. |
| Ten sam NIP, rozne nazwy z importu | VAT/KRS jako nazwa kanoniczna. |
