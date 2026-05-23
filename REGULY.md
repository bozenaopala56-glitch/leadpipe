# REGULY: T0/T0.5/T1/T2 Lead Scoring Pipeline

Data: 2026-05-23  
Wersja rulesetu: `ruleset-2026-05-23-v1`  
Zakres: kwalifikacja T2, bramki decyzyjne, kampanie, suppression, evidence, feedback, rate limiting, import i deduplikacja.

## 1. Zasady nadrzedne

Reguly sa jawne, wersjonowane i audytowalne. Kazda decyzja musi zapisac:

- `ruleset_version`;
- `rule_key`;
- decyzje: `skip`, `retry`, `manual_review`, `t2_required`, `t2_optional`, `send`;
- uzyte sygnaly i `evidence_ids`;
- wynik liczbowy, confidence i powod.

Priorytet globalny:

| Priorytet | Klasa | Efekt |
|---:|---|---|
| 1 | Compliance and suppression | Blokuje eksport niezaleznie od wyniku scoringu. |
| 2 | Data validity | Blokuje lub kieruje do retry, gdy dane sa niewiarygodne. |
| 3 | Safety and deliverability | Chroni reputacje domeny wysylkowej. |
| 4 | Campaign decision | Wybiera kampanie i subject. |
| 5 | T2 uplift | Podbija lub rozstrzyga kampanie, jesli koszt ma sens. |
| 6 | Feedback calibration | Zmienia progi dopiero po minimalnej probce. |

Skale:

- `confidence`: 0.00-1.00, pewnosc konkretnego sygnalu lub decyzji.
- `contactability`: 0-100, jak realnie mozna skontaktowac sie z leadem.
- `industry_fit`: 0-100, dopasowanie do uslug MeNET.
- `evidence_strength`: 0-100, suma wazona dowodow kampanii.
- `lead_value`: 0-100, potencjal wartosciowy na podstawie branzy, B2B, eksportu, produkcji, wielkosci i widocznych uslug.

## A. T2 Eligibility Rules

### A1. Cel

T2 ma odpowiadac tylko na pytania, ktorych T0/T0.5/T1 nie rozstrzygaja: czy strona wyglada nieprofesjonalnie, czy CTA/trust jest slaby, czy kampanie `REDESIGN_CONVERSION_AUDIT` albo `QUALIFIED_CUSTOM_AUDIT` sa lepsze niz bezpieczna kampania techniczna.

T2 nie sluzy do wybierania "najlepszych X%" leadow. Jest uruchamiane przez reguly decyzyjne i budzet.

### A2. Dane wejsciowe

| Wejscie | Zrodlo | Uwagi |
|---|---|---|
| `t0_confidence` | T0 | Pewnosc stanu strony i problemow technicznych. |
| `t1_confidence` | T1 | Pewnosc opisu firmy, kontaktu, branzy i hooka. |
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

### A4. Reguly must have

| Rule key | Warunek | Decyzja | Przyklad |
|---|---|---|---|
| `T2_MUST_AMBIGUOUS_HOOK` | `t0_confidence >= 0.70`, T0 wskazuje problem biznesowo istotny, ale `t1_confidence < 0.70` i brak 2 dowodow kampanii | `t2_required` | T0 widzi wolna strone, T1 nie umie okreslic oferty ani CTA. |
| `T2_MUST_CAMPAIGN_TIE` | Dwie kampanie maja wynik w odleglosci <= 8 pkt, jedna to `REDESIGN_CONVERSION_AUDIT` albo `CARE_PLAN_MAINTENANCE`, `lead_value >= 70` | `t2_required` | WordPress dziala, ale DOM sugeruje slabe CTA; T2 rozstrzyga care plan vs redesign. |
| `T2_MUST_VISUAL_DECISION_BLOCKER` | Brak twardych awarii, `industry_fit >= 75`, `contactability >= 70`, `campaign_confidence 0.55-0.74` | `t2_required` | Dobry producent B2B, strona aktywna, ale hook techniczny zbyt slaby. |
| `T2_MUST_CONFLICTING_EVIDENCE` | T0/T1 maja sprzeczne sygnaly dla kampanii o priorytecie >= 3 i nie ma suppression | `t2_required` albo `manual_review` | Meta wyglada nowoczesnie, ale HTML/CTA ubogie; potrzebny screenshot. |

### A5. Reguly optional

| Rule key | Warunek | Decyzja | Efekt |
|---|---|---|---|
| `T2_OPT_UPGRADE_CARE_TO_REDESIGN` | `CARE_PLAN_MAINTENANCE` ma confidence 0.65-0.80, brak awarii P1/P2, `lead_value >= 65` | `t2_optional` | T2 moze podbic do `REDESIGN_CONVERSION_AUDIT`. |
| `T2_OPT_SUBJECT_ENRICHMENT` | Kampania gotowa bez T2, ale tylko 1 dowod i `contactability >= 80` | `t2_optional` | Dodatkowy dowod do subjectu, jesli budzet wolny. |
| `T2_OPT_HIGH_VALUE_LOW_RISK` | `lead_value >= 85`, `industry_fit >= 75`, `campaign_confidence >= 0.70`, brak twardych problemow | `t2_optional` | Ulepszenie personalizacji dla konta wartosciowego. |

### A6. Reguly skip

| Rule key | Warunek | Decyzja |
|---|---|---|
| `T2_SKIP_SUPPRESSED` | Jakikolwiek aktywny suppression P1 | `skip_t2` |
| `T2_SKIP_NO_CONTACT` | `contactability < 40` i brak manualnego opiekuna | `skip_t2` |
| `T2_SKIP_STRONG_CAMPAIGN` | Kampania P1/P2 ma `campaign_confidence >= 0.82` i >= 2 dowody | `skip_t2` |
| `T2_SKIP_LOW_FIT` | `industry_fit < 45` albo lead spoza rynku | `skip_t2` |
| `T2_SKIP_NOT_SCREENSHOTTABLE` | Screenshot pusty, zablokowany, captcha-only lub consent wall > 70% viewportu | `skip_t2_manual_review` |

### A7. Reguly kosztowe

| Limit | Wartosc startowa | Efekt |
|---|---:|---|
| Dzienny budzet T2 | 10 USD | Po przekroczeniu: tylko `manual_review`, bez nowych calli. |
| Budzet batcha | 2% zakladanej wartosci batcha albo 5 USD, nizsza wartosc wygrywa | Chroni piloty i duze importy. |
| Limit per lead | 2 screenshoty + 2 prompty + 1 retry transportowy | Brak petli kosztowej. |
| Maks. T2 w batchu bez feedbacku | 200 leadow | Dopiero po pomiarze uplift mozna podniesc. |
| Rezerwa must have | 40% budzetu T2 | Optional nie moze zuzyc calego budzetu. |

## B. Decision Gates

### B1. Cel

Bramki ustalaja pierwsza dozwolona decyzje. Sa sprawdzane w stalej kolejnosc, zeby compliance i jakosc danych wygrywaly z atrakcyjnym scoringiem.

### B2. Kolejnosc bramek

| Priorytet | Gate | Decyzja | Progi |
|---:|---|---|---|
| 1 | `GATE_OPT_OUT` | `skip` | Opt-out: permanentnie, natychmiast. |
| 2 | `GATE_SUPPRESSION` | `skip` | Domena/NIP/email/telefon na suppression. |
| 3 | `GATE_INVALID_INPUT` | `skip` | Brak domeny/NIP/kontaktu po normalizacji. |
| 4 | `GATE_NOT_COMPANY` | `skip` | Marketplace, katalog, portal, agregator, prywatny blog: confidence >= 0.75. |
| 5 | `GATE_COUNTRY_FIT` | `skip` | Brak Polski lub obslugi PL: confidence >= 0.75. |
| 6 | `GATE_INDUSTRY_EXCLUSION` | `skip/manual` | IT/software house/konkurencja: auto skip przy confidence >= 0.85, manual przy 0.65-0.84. |
| 7 | `GATE_SCAN_RETRY` | `retry` | Transient HTTP/DNS/TLS, retry <= 1. |
| 8 | `GATE_SCAN_FAILED_FINAL` | `manual_review/skip` | Po retry brak strony; manual jesli `lead_value >= 75`, inaczej skip. |
| 9 | `GATE_CONTACTABILITY` | `manual_review/skip` | < 40 skip, 40-54 manual, >= 55 moze isc dalej. |
| 10 | `GATE_EVIDENCE_MINIMUM` | `manual_review` | Kampania bez minimalnego evidence. |
| 11 | `GATE_T2_ELIGIBILITY` | `t2_required/t2_optional` | Reguly A. |
| 12 | `GATE_CAMPAIGN` | `send/manual_review` | Campaign confidence >= prog kampanii. |

### B3. Skip/retry/campaign/manual review

| Decyzja | Kiedy | Przyklad |
|---|---|---|
| `skip` | Compliance, suppression, niska jakosc danych, brak kontaktu, niski fit | Opt-out, konkurencja, brak domeny. |
| `retry` | Blad przejsciowy i nie przekroczono limitu | 503, 429, timeout, SERVFAIL. |
| `manual_review` | Dobry lead, ale brak automatycznej podstawy | Producent z telefonem, brak emaila i slabe evidence. |
| `t2_required` | Bez obrazu nie da sie wybrac kampanii | Care plan vs redesign przy dobrym leadzie. |
| `send` | Kampania ma prog, kontakt i evidence | Brak HTTPS + email + firma PL. |

### B4. Cooldown

| Zdarzenie | Cooldown |
|---|---:|
| Dowolna kampania wyslana do leadu | 90 dni |
| Ta sama kampania do tej samej firmy | 180 dni |
| Po `positive_reply` | Brak nowych kampanii, tylko follow-up handlowy |
| Po `meeting` | 365 dni lub do recznego odblokowania |
| Po `soft_bounce` | 14 dni i maks. 1 ponowna proba na ten email |
| Po `hard_bounce` | Email permanentnie, firma 180 dni chyba ze jest nowy kontakt |
| Po `opt_out` | Permanentnie dla emaila, domeny i NIP |
| Po `manual_reject` | 180 dni lub do zmiany danych |

## C. Campaign Rules

### C1. Cel

Wybrac jedna z 8 kampanii na podstawie dowodow, a nie samych tagow. Kampania musi miec wystarczajacy confidence, minimalne evidence i bezpieczny subject.

### C2. Kampanie i wymagania

| Priorytet | Kampania | Wymagane sygnaly | Prog confidence | Min evidence |
|---:|---|---|---:|---:|
| 1 | `SITE_DOWN_RESCUE` | T0: brak odpowiedzi, DNS fail, TLS/HTTP fatal, 5xx stale | 0.80 | 2 |
| 2 | `SECURITY_TRUST_FIX` | T0: `ssl.no` lub cert invalid; opcjonalnie brak HSTS/CSP | 0.78 | 2 |
| 3 | `EMAIL_DELIVERABILITY_FIX` | T0: brak MX/SPF/DMARC lub SPF broken; T1 contact istnieje | 0.76 | 2 |
| 4 | `PERFORMANCE_CONVERSION_FIX` | T0: TTFB/total slow, duzy HTML, brak compression | 0.74 | 2 |
| 5 | `SEO_VISIBILITY_FIX` | T0/T1: noindex, brak title/meta, sitemap/robots problem, canonical chaos | 0.72 | 2 |
| 6 | `REDESIGN_CONVERSION_AUDIT` | T2: slaby trust/CTA/design albo T1 DOM: brak CTA/social proof + slaba struktura | 0.76 z T2, 0.68 manual bez T2 | 2 |
| 7 | `CARE_PLAN_MAINTENANCE` | T0/T1: WordPress/CMS/plugin hints, brak awarii P1/P2, firma aktywna | 0.70 | 1 |
| 8 | `QUALIFIED_CUSTOM_AUDIT` | Dobry fit, dobry kontakt, brak jednoznacznej kampanii automatycznej | 0.65 | 2 |

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
| Subject mialby opierac sie na jednym slabym dowodzie | -10 |

### C4. Priorytety konfliktow

Gdy wiele kampanii pasuje:

1. P1 awaryjne wygrywa: `SITE_DOWN_RESCUE`.
2. Ryzyko zaufania/security wygrywa nad performance.
3. Deliverability wygrywa nad SEO, jesli problem moze blokowac odpowiedzi email.
4. Performance wygrywa nad SEO, jesli slowdown jest >= p75 batcha lub total > 3000 ms.
5. `REDESIGN_CONVERSION_AUDIT` wygrywa nad `CARE_PLAN_MAINTENANCE`, tylko gdy T2 confidence >= 0.76 lub manual approve.
6. `QUALIFIED_CUSTOM_AUDIT` jest fallbackiem dla dobrych leadow bez twardego hooka.

### C5. Subject template rules

Subject laczy maksymalnie jeden glowny problem i jeden kontekst firmy. Nie wolno uzywac straszenia bez twardego evidence.

| Kampania | Subject pattern | Wymagane dowody |
|---|---|---|
| `SITE_DOWN_RESCUE` | "`{firma}`: problem z dostepnoscia strony" | Status/DNS/TLS + timestamp. |
| `SECURITY_TRUST_FIX` | "HTTPS i zaufanie na `{domena}`" | Brak HTTPS/cert invalid + aktywna strona. |
| `EMAIL_DELIVERABILITY_FIX` | "Konfiguracja poczty dla `{domena}`" | MX/SPF/DMARC evidence. |
| `PERFORMANCE_CONVERSION_FIX` | "Szybkosc strony `{firma}`" | Czas odpowiedzi + rozmiar/brak kompresji. |
| `SEO_VISIBILITY_FIX` | "Widocznosc strony `{firma}` w Google" | Noindex/meta/sitemap/canonical. |
| `REDESIGN_CONVERSION_AUDIT` | "Pierwsze wrazenie i CTA na `{domena}`" | T2 visual + T1 CTA/trust. |
| `CARE_PLAN_MAINTENANCE` | "Opieka techniczna nad `{domena}`" | CMS/WordPress + brak krytycznych awarii. |
| `QUALIFIED_CUSTOM_AUDIT` | "Krotki audyt strony `{firma}`" | Fit + 2 neutralne dowody. |

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
| Konkurencja | agencje digital, SEO, software house, hosting, marketing | Auto przy confidence >= 0.85 |
| Branża IT | software house, web design, SEO, ads, hosting, SaaS vendors | Auto/manual wedlug confidence |
| Wewnetrzne blacklisty | domena, NIP, email | Auto |
| Role risky | abuse@, security@, privacy@, rodo@ | Suppress email, nie firme |
| Zrodla zakazane | scraping naruszajacy regulamin, lista bez podstawy | Auto batch suppression |

### D3. Auto vs manual

| Warunek | Decyzja |
|---|---|
| Opt-out, hard bounce, klient, aktywny deal | Auto suppression |
| Konkurencja confidence >= 0.85 | Auto suppression |
| Konkurencja/IT confidence 0.65-0.84 | Manual review |
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
| `SITE_DOWN_RESCUE` | 2 | 0.80 | AND: status + drugi techniczny dowod |
| `SECURITY_TRUST_FIX` | 2 | 0.78 | AND/OR: SSL/cert + trust/security header |
| `EMAIL_DELIVERABILITY_FIX` | 2 | 0.76 | Weighted: MX/SPF/DMARC |
| `PERFORMANCE_CONVERSION_FIX` | 2 | 0.74 | AND: czas + rozmiar/kompresja |
| `SEO_VISIBILITY_FIX` | 2 | 0.72 | OR weighted, noindex jako silny dowod |
| `REDESIGN_CONVERSION_AUDIT` | 2 | 0.76 dla T2, 0.70 dla T1 | AND: visual + CTA/trust albo manual |
| `CARE_PLAN_MAINTENANCE` | 1 | 0.70 | OR: CMS lub maintenance risk |
| `QUALIFIED_CUSTOM_AUDIT` | 2 | 0.65 | Weighted: fit + neutralny problem |

### E3. Laczenie dowodow

| Tryb | Zastosowanie |
|---|---|
| AND | Kampanie awaryjne, gdzie claim musi byc mocny. |
| OR | Kampanie z wieloma rownowaznymi problemami. |
| Weighted | SEO, deliverability i custom audit. |
| Veto | Sprzeczny albo ryzykowny dowod blokuje automatyczna wysylke. |

### E4. Evidence text

Format:

```text
Na stronie {domena} {obserwacja biznesowa}. W skanie z {data} system potwierdzil: {konkretna wartosc}. To moze oznaczac {konsekwencja biznesowa}.
```

Zasady:

- pisac jezykiem biznesowym, nie administracyjnym;
- nie mowic "blad krytyczny", jesli dowod jest umiarkowany;
- nie obiecywac liczby problemow bez liczby dowodow;
- nie ujawniac technicznych szczegolow, ktore brzmia jak pentest;
- `evidence_text` max 220 znakow w CSV, pelny opis w bazie.

Przyklad:

```text
Strona example.pl odpowiadala po ok. 3,4 s w skanie z 2026-05-23. Przy pierwszym kontakcie taki czas moze obnizac liczbe zapytan z formularza.
```

## F. Feedback Rules

### F1. Cel

Feedback kalibruje reguly na wyniki sprzedazowe, nie na intuicje.

### F2. Interpretacja zdarzen

| Event | Interpretacja | Akcja |
|---|---|---|
| `bounce_hard` | Email nie istnieje lub domena odrzuca stale | Suppress email permanentnie, firma 180 dni. |
| `bounce_soft` | Tymczasowy problem skrzynki/provider | Cooldown email 14 dni, maks. 1 retry. |
| `opened` | Slaby sygnal zainteresowania | Nie zmieniac progow bez reply. |
| `clicked` | Sredni sygnal | Podbic subject/template score po probce. |
| `reply` | Silny sygnal, wymaga klasyfikacji | Oznaczyc positive/neutral/negative/manual. |
| `positive_reply` | Kampania trafiona | Podbic wage sygnalow kampanii po probce. |
| `meeting` | Najsilniejszy sygnal | Podbic kampanie i fit segmentu. |
| `deal_won` | Revenue signal | Kalibrowac lead_value i segment. |
| `negative_reply` | Slaby fit albo zly hook | Cooldown 180 dni i analiza false positive. |
| `opt_out` | Compliance | Permanent suppression. |

### F3. Aktualizacja suppression

| Feedback | Suppression |
|---|---|
| Hard bounce | Email permanent, domena/NIP 180 dni. |
| Soft bounce | Email 14 dni. |
| Negative reply "nie piszcie" | Opt-out permanent. |
| Negative reply bez opt-out | 180 dni company cooldown. |
| Positive reply/meeting | Blokada automatycznych kampanii, przekazanie do CRM. |

### F4. Recalibracja scoringu

Zmiany progow wymagaja minimalnej probki:

| Zmiana | Minimalna probka |
|---|---:|
| Korekta subject template | 100 wysylek i >= 5 reply dla kampanii |
| Korekta progu kampanii | 200 wysylek i >= 20 reply albo 10 positive replies |
| Korekta suppression branzy | 50 recznych decyzji QA |
| Korekta T2 eligibility | 100 leadow z T2 i 100 podobnych bez T2 |
| Usuniecie kampanii z MVP | 300 wysylek i positive reply rate < 0.5% |

Nie zmieniamy progow po samych open rates. Open rate sluzy glownie do diagnostyki deliverability i subjectow.

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

### G3. Retry classes

| Klasa | Przyklady | Retry |
|---|---|---|
| Transient | timeout, reset, 408, 429, 503, SERVFAIL | 1 retry, backoff 2-10 s + jitter |
| Permanent | NXDOMAIN, 404 main domain, invalid input | Bez retry |
| Compliance | robots explicit block dla crawl, opt-out, forbidden source | Bez retry, suppression/manual |
| Parser error | bledny HTML/JSON-LD | Bez retry network, fallback parser |
| T2 transport | 5xx provider, timeout | 1 retry |
| T2 quality | blank screenshot, captcha, blocked | Bez model call, manual/skip |

### G4. Cache TTL

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

| Sytuacja | Zwyciezca |
|---|---|
| Jeden rekord ma NIP, drugi nie | Rekord z NIP. |
| Oba maja NIP i rozne domeny | Tworzymy jedna firme i aliasy domen. |
| Jeden rekord ma kontakt email, drugi nie | Rekord z kontaktem jako primary, drugi jako alias/source. |
| Rozne kontakty dla tej samej firmy | Zachowac wszystkie, oznaczyc primary wedlug jakosci. |
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
