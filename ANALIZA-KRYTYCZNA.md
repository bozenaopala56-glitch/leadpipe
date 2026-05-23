# ANALIZA KRYTYCZNA SPECYFIKACJI T0/T1/T2

Data analizy: 2026-05-23  
Zakres: plik `SPECYFIKACJA-T0-T1-T2.md`

## Executive Summary

Architektura T0/T1/T2 ma sens jako kierunek, ale w obecnej formie jest bardziej raportem researchowym niż specyfikacją produkcyjnego systemu sprzedażowego. Największy błąd: pipeline optymalizuje wykrywanie problemów technicznych, ale nie dowodzi, że te problemy przewidują intencję zakupową, wartość leada albo skuteczność outreachu.

Najważniejsze zmiany do zrobienia natychmiast:

1. Oddzielić `diagnostykę` od `decyzji sprzedażowej`: scoring techniczny nie może automatycznie oznaczać dobrej kampanii.
2. Dodać warstwę T0.5/T1 biznesową: firma, branża, wielkość, lokalizacja, aktywność, dane kontaktowe, potencjalny budżet.
3. Zbudować minimalny pipeline produkcyjny: kolejka, idempotencja, storage, wersjonowanie skanów, deduplikacja, observability.
4. Zastąpić "47 archetypów" prostszym modelem reguł + priorytetów + eksperymentów A/B.
5. Uruchomić T2 tylko selektywnie, nie globalnie. Vision ma sens wyłącznie dla leadów, gdzie może zmienić decyzję.

Największy ROI: nie Gemini Vision, nie HDBSCAN, nie kolejne algorytmy. Największy ROI da wdrożenie prostego T0+T1+kampanie+feedback loop i pomiar: open rate, reply rate, meeting rate, conversion rate.

---

## 1: Czy architektura T0 -> T1 -> T2 ma sens?

**Analiza:**

Kierunek warstwowy ma sens: najpierw tanie sygnały techniczne, potem analiza tekstu i danych biznesowych, potem drogie AI. To poprawny wzorzec ekonomiczny dla lead scoringu.

Problemem jest jednak definicja warstw. T1 jest opisane jako analiza tekstu, ale realnie powinno być warstwą biznesową. Obecne T1 zbiera opis firmy, nazwę, branżę i lokalizację, czyli nie jest tylko NLP. Brakuje formalnej warstwy T0.5/T1 dla firmografii i danych kontaktowych: NIP, REGON, KRS/CEIDG, PKD, lokalizacja, wielkość firmy, forma prawna, aktywność VAT, e-mail, telefon, LinkedIn, branża, potencjalny koszyk usług.

Kolejność T0 -> T1 -> T2 jest dobra, ale nie powinna być liniowa dla każdego leada. Pipeline powinien być decyzyjny:

- T0 dla wszystkich leadów.
- T1 dla aktywnych stron i leadów z potencjałem.
- T2 tylko wtedy, gdy wynik T0/T1 jest niejednoznaczny albo lead jest wartościowy.

Obecne założenie "T1 0ms" jest nieprawdziwe produkcyjnie. HTML może być już pobrany, ale parsowanie, normalizacja, ekstrakcja NIP, JSON-LD, canonical URL, języka, branży i walidacja danych mają koszt CPU, błędów i utrzymania. To nie jest duży koszt, ale nie jest zerowy.

**Rekomendacja:**

Zmień architekturę z liniowej na bramkowaną:

`Lead intake -> Normalize/Dedupe -> T0 -> T0.5 Business Enrichment -> Decision Gate -> T1 Content -> Decision Gate -> T2 Vision -> Campaign Assignment -> Outreach -> Feedback`

Priorytet: HIGH  
Szacowany wysiłek: 2-4 dni na projekt kontraktów danych i routing, 5-10 dni na pierwszą implementację.

**Alternatywy:**

- Opcja A: Zachować T0 -> T1 -> T2, ale dodać bramki kosztowe po T0 i T1. Najmniej zmian, dobry ROI.
- Opcja B: Wprowadzić T0.5 jako osobną warstwę firmograficzną przed T1. Najlepsze pod sprzedaż B2B.
- Opcja C: Połączyć T1 i T2 w jedną warstwę "semantic enrichment", ale tylko jako abstrakcję API. Wewnątrz nadal rozdzielać koszty.

**Ryzyka:**

- Bez T0.5 pipeline będzie wysyłał dobre technicznie, ale biznesowo nietrafione kampanie.
- T2 uruchamiane globalnie przepali budżet i opóźni batch.
- Liniowy pipeline utrudni retry, cache i częściowe odświeżanie danych.

---

## 2: Czy 12 core tagów to wystarczająca reprezentacja?

**Analiza:**

12 core tagów może wystarczyć do segmentacji technicznej, ale nie wystarcza do lead scoringu sprzedażowego. To zasadnicza różnica.

Redukcja z 28 do 12 przez implication lattice może być poprawna statystycznie, ale specyfikacja nie pokazuje walidacji predykcyjnej. To, że sygnał jest inferowalny z innego sygnału z confidence >= 95%, nie oznacza, że jest nieprzydatny sprzedażowo. Rzadkie sygnały mogą mieć wysoką wartość, jeśli mocno zmieniają argument sprzedażowy lub priorytet.

Przykład: sygnały security występują u <2% leadów, więc są słabe do masowego klastrowania, ale mogą być świetne do kampanii CyberPakt, bo dają konkretny, bolesny hak. Usunięcie ich z core może być OK dla archetypów, ale nie dla generowania argumentów w mailu.

Kolejny problem: `whois:no` jest zbyt mocno eksponowany. Brak WHOIS dla domen .pl często wynika z prywatności, ograniczeń rejestru albo sposobu pobierania danych, a nie z problemu biznesowego. Kampania "uzupełnij dane firmy w rejestrze" wygląda słabo i może być merytorycznie błędna.

Brakuje tagów o wysokiej wartości biznesowej:

- `contact:email_found`
- `contact:phone_found`
- `contact:form_found`
- `business:nip_found`
- `business:vat_active`
- `business:industry_detected`
- `cms:wordpress`
- `tracking:analytics_missing`
- `ads:conversion_tracking_missing`
- `seo:indexability_problem`
- `content:stale_or_thin`
- `mobile:viewport_missing`
- `consent:cookies_problem`

**Rekomendacja:**

Zostaw 12 tagów jako `technical_core_tags`, ale nie jako pełną reprezentację leada. Dodaj drugi zestaw: `sales_features` i trzeci: `evidence_items`.

Priorytet: HIGH  
Szacowany wysiłek: 1 dzień na nowy schemat danych, 2-5 dni na implementację najważniejszych 10-15 cech.

**Alternatywy:**

- Opcja A: 12 core tagów tylko do segmentacji technicznej, reszta jako evidence dla maila.
- Opcja B: 12 core tagów + 10 business tags jako minimalny scoring sprzedażowy.
- Opcja C: Porzucić twardą redukcję i trzymać pełne sygnały w storage, a do kampanii używać wybranych widoków.

**Ryzyka:**

- Nadmierna redukcja usunie sygnały, które są rzadkie, ale sprzedażowo mocne.
- Archetypy zbudowane tylko na T0 będą ignorować branżę i budżet.
- Confidence z implication lattice może być artefaktem konkretnego datasetu 4529 leadów i nie przenieść się na nowe źródła leadów.

---

## 3: Czy 8 kampanii to optymalny zestaw?

**Analiza:**

8 kampanii to sensowny start, ale zestaw nie jest optymalny. Kampanie mieszają trzy różne rzeczy:

- realne awarie: RESCUE, CRISIS_AUDIT;
- problemy techniczne: SSL, DNS, performance;
- ogólny upsell: MODERNIZE, UPSELL_PREMIUM;
- wątpliwy pretekst: WHOIS_RECOVERY.

Cannibalization jest realnym problemem. Jeden lead może jednocześnie mieć `status:active`, `speed:slow`, `ssl:no`, `dns:minimal`, `whois:no` i `crisis:yes`. Bez formalnego decision tree system będzie wybierał kampanię arbitralnie albo generował sprzeczne wiadomości.

Priorytety są częściowo dobre: RESCUE i CRISIS_AUDIT powinny być wysoko. Ale `DNS_SETUP` przy `dns:none` może dotyczyć domen bez strony albo źle znormalizowanych leadów, więc wymaga ostrożności. `MODERNIZE` jako "status active + brak infra modern" jest zbyt szerokie i słabe. Brak IPv6/CDN nie jest dobrym argumentem sprzedażowym dla polskiego MŚP.

Subject line'y są zbyt techniczne i miejscami ryzykowne prawnie/reputacyjnie. "Brakuje rekordów DNS - e-mail może nie dochodzić" może być fałszywe, jeśli e-mail działa przez konfigurację niewykrytą przez skaner. "5 problemów na Twojej stronie" wymaga dokładnie 5 udowodnionych problemów.

**Rekomendacja:**

Zmień kampanie na hierarchiczny model:

1. `SITE_DOWN_RESCUE`
2. `SECURITY_TRUST_FIX`
3. `PERFORMANCE_CONVERSION_FIX`
4. `EMAIL_DELIVERABILITY_FIX`
5. `SEO_VISIBILITY_FIX`
6. `REDESIGN_CONVERSION_AUDIT`
7. `CARE_PLAN_MAINTENANCE`
8. `QUALIFIED_CUSTOM_AUDIT`

Dodaj `campaign_decision_reason`, `evidence`, `confidence`, `suppression_rules` i `fallback_campaign`.

Priorytet: HIGH  
Szacowany wysiłek: 1-2 dni na decyzje i reguły, 2-3 dni na template'y i testy.

**Alternatywy:**

- Opcja A: Jedna kampania per lead według najwyższego bólu, z twardym priorytetem.
- Opcja B: Kampania główna + 1-2 secondary hooks w treści maila.
- Opcja C: Multi-armed bandit/A-B testing subjectów po zebraniu pierwszych 500-1000 wysyłek.

**Ryzyka:**

- Źle dobrana kampania obniży deliverability i spali domeny mailingowe.
- Zbyt agresywne subjecty mogą wyglądać jak scareware.
- Kampanie techniczne bez kontekstu biznesowego będą miały niski reply rate.

---

## 4: Jak powinien wyglądać produkcyjny pipeline?

**Analiza:**

Obecnie nie ma produkcyjnego pipeline'u. Jest research, artefakty i koncepcja. Do działania brakuje podstaw: kontraktu danych, kolejki, retry, idempotencji, storage, API, wersjonowania wyników, monitoringu i feedback loop.

Minimalny produkcyjny pipeline:

1. `lead_intake`: import URL-i, normalizacja domen, deduplikacja.
2. `scan_jobs`: kolejka z retry, timeoutami i rate limitami.
3. `t0_scan`: HTTP, DNS, SSL, HTML fetch, robots/sitemap, podstawowy tech detect.
4. `t1_enrich`: JSON-LD, meta, NIP, dane firmowe, kontakt.
5. `score_campaign`: reguły kampanii z evidence.
6. `outreach_export`: CSV/API do narzędzia mailingowego lub CRM.
7. `feedback_import`: status wysyłki, open, reply, meeting, deal.

Technicznie: Python jest dobrym wyborem dla skanerów, parserów i batchy. Nie ma potrzeby BullMQ, jeśli reszta stacku nie jest Node. Dla jednej VM prościej użyć Postgres + RQ/Celery/Dramatiq albo nawet SQLite + APScheduler na MVP. Przy 5000 leadów batch BullMQ/Redis też zadziała, ale wprowadza drugi język i większą operacyjność.

Storage w JSON + GCS jest dobry jako archiwum surowych artefaktów, ale zły jako podstawowy system operacyjny. Potrzebujesz bazy do zapytań, statusów, retry, historii skanów i kampanii.

Refresh rate:

- `status/error/performance`: co 30-90 dni albo przed kampanią;
- `SSL/DNS`: co 30 dni dla problematycznych, 90 dni dla stabilnych;
- `WHOIS/business`: 90-180 dni;
- `T2`: tylko przy zmianie strony albo dla gorących leadów.

**Rekomendacja:**

Zbuduj MVP na Python + Postgres + Redis/RQ albo Celery. GCS zostaw na raw snapshots i audyt. API dodaj dopiero po stabilizacji CLI/batcha, chyba że integracja z CRM wymaga go od razu.

Priorytet: HIGH  
Szacowany wysiłek: 7-14 dni na MVP produkcyjny, 3-5 dni na wersję bardzo minimalną bez dashboardu.

**Alternatywy:**

- Opcja A: Python + Postgres + RQ/Redis. Najlepszy balans prostoty i produkcyjności.
- Opcja B: Python + SQLite + pliki JSON. Najszybsze MVP, ale ograniczone przy równoległości.
- Opcja C: Node + BullMQ + Postgres. Dobre, jeśli CRM/dashboard/API będą w Node, ale mniej naturalne dla skanowania.

**Ryzyka:**

- JSON jako główny storage szybko utrudni deduplikację i raportowanie.
- Brak idempotencji spowoduje duplikaty kampanii do tych samych firm.
- Brak rate limitów może doprowadzić do blokad IP i fałszywych wyników `inactive/error`.

---

## 5: Czy T2 vision ma sens ekonomiczny?

**Analiza:**

T2 ma sens, ale nie jako warstwa dla wszystkich leadów. Przy koszcie około $0.01/lead 5000 leadów kosztuje tylko około $50, więc sam koszt API nie jest dramatyczny. Prawdziwy koszt to latency, obsługa screenshotów, retry, błędy renderowania, kolejki browserów, większa złożoność i ryzyko halucynacyjnych ocen.

Vision może dać wartość tam, gdzie decyzja sprzedażowa zależy od jakości wizualnej: redesign, trust, CTA, mobile, branżowe wrażenie, stockowe zdjęcia, chaos layoutu. Nie zastąpi jednak danych biznesowych ani dowodu konwersji.

Największy problem: specyfikacja nie definiuje, co wynik T2 zmienia. Jeśli T2 tylko dodaje "strona wygląda staro", to jest za mało. T2 musi wpływać na jedną z decyzji:

- czy wysłać maila;
- jaką kampanię wybrać;
- jaki hook wpisać;
- czy lead jest wart ręcznej obsługi;
- czy podbić priorytet.

Da się zastąpić część T2 tańszymi sygnałami:

- Lighthouse/PageSpeed dla performance i mobile;
- DOM heuristics dla CTA, formularzy, telefonów;
- CSS/HTML heuristics dla wieku technologii;
- screenshot + lokalny model CLIP/classifier później;
- T1 analiza treści dla trust/social proof.

**Rekomendacja:**

Nie wdrażać T2 globalnie. Wdrożyć T2 jako selektywny enhancer dla top 10-20% leadów lub dla leadów, gdzie T0/T1 wskazuje potencjał, ale brakuje dobrego hooka.

Priorytet: MEDIUM  
Szacowany wysiłek: 3-6 dni na selektywny T2 MVP, 10-15 dni na stabilny screenshot pipeline z kontrolą jakości.

**Alternatywy:**

- Opcja A: T2 tylko dla leadów z wysokim business score i aktywną stroną.
- Opcja B: Najpierw heurystyki DOM/Lighthouse, T2 tylko gdy heurystyki są niejednoznaczne.
- Opcja C: Ręczna ocena 100-200 leadów, dopiero potem kalibracja promptów i automatyzacja.

**Ryzyka:**

- Gemini może oceniać polskie strony niespójnie albo zbyt ogólnie.
- Screenshoty będą padać na cookie bannerach, lazy loadingu, captchach i stronach wolnych.
- Bez walidacji na reply/conversion rate T2 może produkować ładne, ale bezużyteczne uzasadnienia.

---

## 6: Jakie są alternatywy dla obecnej architektury?

**Analiza:**

Obecna architektura jest dobra kosztowo, ale mocno heurystyczna. Alternatywy istnieją, lecz większość ma gorszy ROI na starcie.

LLM-first, czyli jeden prompt do Gemini z HTML/screenshotem, jest kuszący, ale nie polecam jako głównego pipeline'u. Będzie droższy, mniej deterministyczny, trudniejszy do debugowania i słabszy w audycie. LLM-first może działać jako narzędzie do generowania kopii maila na końcu, ale nie jako źródło prawdy.

ML klasyfikator ma sens dopiero po zebraniu etykiet sprzedażowych. Na dziś nie ma targetu. Klastrowanie T0 nie zastępuje supervised learningu. Targetem powinno być np. `reply`, `positive_reply`, `meeting_booked`, `deal_created`, `deal_won`, a nie archetyp.

Gotowe narzędzia typu Hotjar/OpenReplay nie pasują do oceny cudzych stron bez instalacji skryptu. BuiltWith/Wappalyzer/Similarweb/PageSpeed/CrUX mogą być bardziej sensowne jako enrichment, ale część będzie płatna lub limitowana.

**Rekomendacja:**

Zostać przy T0/T1/T2, ale dodać feedback loop i przygotować architekturę pod późniejszy ML. Nie wdrażać ML przed danymi sprzedażowymi.

Priorytet: MEDIUM  
Szacowany wysiłek: 1-2 dni na zdefiniowanie eventów feedbacku, 5-10 dni na integrację z narzędziem wysyłkowym/CRM.

**Alternatywy:**

- Opcja A: Heurystyczny pipeline T0/T1 + eksperymenty A/B. Najlepszy start.
- Opcja B: LLM-assisted copywriting po deterministycznym scoringu. Dobry kompromis.
- Opcja C: Supervised ML po 1000+ wysyłek i sensownych etykietach. Najlepsze później, nie teraz.

**Ryzyka:**

- LLM-first da wyniki trudne do powtórzenia i audytu.
- ML bez etykiet będzie akademickim ćwiczeniem.
- Gotowe narzędzia mogą zjeść marżę i nie dać danych potrzebnych do personalizacji.

---

## 7: Co robić z 28 anomaliami HDBSCAN?

**Analiza:**

Anomalie HDBSCAN mogą być trzema rzeczami:

- błędami danych;
- nietypowymi konfiguracjami technicznymi;
- wysokowartościowymi leadami z nietypowym profilem.

Nie wolno automatycznie traktować ich jako segmentu kampanii. 28 rekordów to mało. Najpierw trzeba zrobić manualny audit. W lead scoringu anomalie często są najciekawsze, ale równie często są śmieciem: przekierowania, parking domains, błędne domeny, timeouty, captive pages, strony w budowie.

Największa wartość anomalii jest diagnostyczna: pokazują, gdzie skaner źle klasyfikuje edge-case'y i gdzie brakuje tagów.

**Rekomendacja:**

Zrób ręczną analizę wszystkich 28 anomalii i oznacz je jako `data_error`, `scanner_gap`, `rare_valid_pattern`, `high_value_manual_review`. Dopiero potem decydować o kampanii.

Priorytet: MEDIUM  
Szacowany wysiłek: 3-6 godzin na ręczny audit, 1-2 dni na poprawki skanera wynikające z audytu.

**Alternatywy:**

- Opcja A: Manual review wszystkich 28, najtańsze i najlepsze.
- Opcja B: Puścić pełny T0+T1+T2 tylko dla anomalii i porównać z normalnymi leadami.
- Opcja C: Wykluczyć anomalie z automatycznych kampanii do czasu walidacji.

**Ryzyka:**

- Automatyczne kampanie do anomalii mogą trafić w błędne lub martwe rekordy.
- Ignorowanie anomalii może ukryć cenne nisze.
- Poprawki pod 28 przypadków mogą przeuczyć skaner na edge-case'y.

---

## 8: Czy pipeline powinien być rozszerzalny?

**Analiza:**

Tak, ale rozszerzalność musi być kontrolowana. Najgorszy kierunek to "dodajemy kolejne sygnały do JSON-a". To szybko tworzy niespójny system, w którym nikt nie wie, które pola są stabilne, które eksperymentalne i które wolno używać w kampaniach.

Potrzebne są kontrakty:

- wersjonowany schema dla leadów;
- wersjonowany schema dla skanów;
- katalog sygnałów z typem, źródłem, kosztem, TTL i confidence;
- katalog kampanii z triggerami, priorytetami i suppression rules;
- eventy integracyjne do CRM;
- wersjonowanie scoringu i kampanii.

Dodawanie nowych sygnałów powinno wyglądać tak:

1. Sygnał trafia jako `experimental`.
2. Ma definicję, ownera, koszt, TTL, confidence i testy.
3. Po walidacji przechodzi do `stable`.
4. Dopiero wtedy wolno używać go w kampaniach automatycznych.

Integracja z CRM powinna być eventowa: `lead_scanned`, `lead_scored`, `campaign_assigned`, `outreach_sent`, `reply_received`, `deal_created`. HubSpot można obsłużyć przez API, ale nie powinien być źródłem prawdy dla surowych skanów.

**Rekomendacja:**

Wdrożyć prosty pluginowy katalog sygnałów i kampanii już w MVP. Nie budować ciężkiego frameworka, ale wymusić schema, wersje i testy.

Priorytet: HIGH  
Szacowany wysiłek: 2-4 dni na schema i registry, 3-5 dni na integrację z pierwszym CRM/exportem.

**Alternatywy:**

- Opcja A: YAML/JSON registry sygnałów i kampanii. Najszybsze i wystarczające na start.
- Opcja B: Python classes dla scannerów i campaign rules. Lepsze testowanie, trochę więcej kodu.
- Opcja C: Pełny workflow engine. Nie polecam na MVP, za duży narzut.

**Ryzyka:**

- Zbyt elastyczny system stanie się trudny do debugowania.
- Bez wersjonowania nie da się porównać wyników kampanii w czasie.
- Integracja CRM bez deduplikacji spowoduje duplikaty firm i kontaktów.

---

## 9: Co najbardziej brakuje w całej architekturze?

Najbardziej brakuje feedback loop sprzedażowego. Specyfikacja zakłada, że lepsza diagnoza techniczna da lepszy outreach, ale tego nie mierzy.

Brakuje:

- definicji sukcesu: reply rate, positive reply rate, meetings, deals, revenue;
- modelu wartości leada;
- danych kontaktowych i zgód/procesu wysyłki;
- suppression list;
- deduplikacji firm i domen;
- kontroli deliverability;
- eksperymentów A/B;
- historii kontaktów;
- wersjonowania scoringu;
- observability pipeline'u.

Największy brak architektoniczny: brak rozdzielenia między `lead intelligence` a `sales execution`.

Rekomendacja: dodać moduł `sales_feedback` i traktować go jako równorzędny wobec T0/T1/T2.  
Priorytet: HIGH  
Wysiłek: 2-3 dni na model eventów, 5-10 dni na pierwszą integrację z narzędziem outreach/CRM.

---

## 10: Czy podejście research-first, kod później ma sens?

Tak, ale research przekroczył punkt malejących zwrotów. Dalsze FP-Growth, HDBSCAN, Louvain i MCA bez produkcyjnego feedbacku będą poprawiać raporty, nie sprzedaż.

Research-first miał sens do zredukowania chaosu sygnałów i znalezienia podstawowych archetypów. Teraz trzeba przejść do build-measure-learn:

1. Zbudować minimalny pipeline.
2. Wysłać kontrolowaną kampanię.
3. Zmierzyć odpowiedzi.
4. Poprawić scoring i treści.

Rekomendacja: zamrozić research poza walidacją T1/T2 i przez 2 tygodnie budować MVP.  
Priorytet: HIGH  
Wysiłek: 10 dni roboczych do pierwszego batcha produkcyjnego.

Ryzyko: kontynuowanie researchu stworzy pozorną precyzję bez dowodu biznesowego.

---

## 11: Minimalny produkcyjny pipeline

Minimalna wersja, która ma działać:

1. Import CSV z `domain`, opcjonalnie `company_name`, `source`.
2. Normalizacja domeny i deduplikacja.
3. T0 scan: HTTP, HTTPS, SSL, DNS, redirects, title, meta, HTML snapshot.
4. T1 light: JSON-LD, meta description, NIP regex, e-mail/telefon/formularz, branża z prostych reguł.
5. Scoring: twarde reguły kampanii + confidence + evidence.
6. Eksport do CSV/HubSpot: firma, domena, kampania, subject, 2-3 bullet evidence, status.
7. Feedback import: sent/open/reply/positive/meeting.
8. Raport: skuteczność kampanii i błędy skanera.

Nie robić w MVP:

- dashboardu;
- pełnego T2 dla wszystkich;
- ML;
- 47 archetypów jako głównego interfejsu;
- ciężkiego workflow engine;
- automatycznego wysyłania bez manualnego QA pierwszych batchy.

Technologie MVP:

- Python 3.12;
- `httpx`, `selectolax` lub `BeautifulSoup`, `dnspython`, `cryptography`, `tldextract`, `pydantic`;
- Playwright tylko opcjonalnie, nie dla każdego leada;
- Postgres;
- Redis + RQ/Celery albo SQLite na bardzo mały start;
- GCS dla raw snapshots.

Wysiłek:

- wersja minimalna bez CRM: 3-5 dni;
- wersja z kolejką i Postgres: 7-14 dni;
- wersja z CRM i feedbackiem: 14-21 dni.

---

## 12: Ocena technologii

**JSON + GCS vs baza danych**

JSON + GCS jest dobre dla:

- surowych snapshotów;
- archiwum;
- reprodukowalności;
- taniego przechowywania dużych odpowiedzi.

JSON + GCS jest złe dla:

- statusów jobów;
- deduplikacji;
- zapytań analitycznych;
- retry;
- historii kampanii;
- filtrowania leadów;
- integracji z CRM.

Rekomendacja: Postgres jako system operacyjny, GCS jako cold/raw storage.  
Priorytet: HIGH  
Wysiłek: 1-2 dni na schema MVP.

**Python vs inne**

Python jest właściwy dla T0/T1/T2:

- dobry ekosystem HTTP/DNS/HTML/ML;
- prosty batch processing;
- łatwe Pydantic schemas;
- dobry Playwright support.

Node/BullMQ ma sens, jeśli cały produkt będzie web-appem w Node. W przeciwnym razie miesza stack bez wyraźnego zysku.

Rekomendacja: Python-first. Node tylko dla frontendu/API, jeśli będzie potrzebny.  
Priorytet: MEDIUM  
Wysiłek: brak, to decyzja architektoniczna.

---

## 13: Wąskie gardła i problemy skali

Najważniejsze bottlenecki:

1. Network I/O: 5000 domen po kilka requestów każda oznacza tysiące timeoutów, redirectów i blokad.
2. DNS latency i błędy resolverów.
3. False negatives przez rate limiting, WAF, geoblokady i wolne serwery.
4. Playwright/screenshoty: największy koszt CPU/RAM i najwięcej awarii.
5. Vision API latency: 2-5 sekund per prompt, łatwo tworzy kolejki.
6. Brak cache: ponowne skany będą marnować czas.
7. Brak canonicalizacji domen: `www`, bez `www`, http/https, slash, przekierowania.
8. Brak deduplikacji firm: jedna firma może mieć wiele domen, a jedna domena wiele marek.
9. Deliverability: nawet świetny scoring nic nie da, jeśli mailing trafi do spamu.
10. Compliance: outreach B2B wymaga ostrożności w danych osobowych, podstawie kontaktu i opt-out.

Rekomendowane limity startowe:

- concurrency HTTP: 50-100, potem stroić;
- timeout connect: 3s;
- timeout total T0: 10-15s;
- retry: maksymalnie 1-2, tylko dla błędów przejściowych;
- T2: osobna kolejka, niski concurrency;
- cache DNS/HTTP: TTL zależny od typu sygnału;
- per-domain evidence log dla audytu maila.

Priorytet: HIGH  
Wysiłek: 2-4 dni na sensowne limity, retry i telemetry.

---

## Najważniejsza lista napraw według ROI

1. HIGH, 1 dzień: Zdefiniować schema `Lead`, `ScanResult`, `Signal`, `CampaignDecision`, `Evidence`, `OutreachEvent`.
2. HIGH, 2-3 dni: Zbudować T0 MVP z cache, timeoutami i wersjonowaniem wyniku.
3. HIGH, 1-2 dni: Dodać T1 light: NIP/e-mail/telefon/formularz/JSON-LD/meta.
4. HIGH, 1 dzień: Przepisać kampanie na decision tree z suppression rules.
5. HIGH, 1-2 dni: Dodać Postgres albo SQLite jako operacyjny storage.
6. HIGH, 1 dzień: Eksport kampanii do CSV z evidence i confidence.
7. HIGH, 1-2 dni: Feedback import po wysyłce.
8. MEDIUM, 3-6 dni: Selektywny T2 dla top leadów.
9. MEDIUM, 3-6 godzin: Manualny audit 28 anomalii.
10. LOW, później: ML, dashboard, pełna automatyzacja wysyłki.

## Brutalna konkluzja

Specyfikacja jest technicznie ambitna, ale sprzedażowo niedomknięta. Największe ryzyko nie polega na tym, że T0 źle wykryje SSL albo DNS. Największe ryzyko polega na tym, że system będzie bardzo precyzyjnie klasyfikował problemy, których klient nie uważa za pilne i za które nie chce zapłacić.

Nie dokładać kolejnych algorytmów przed wdrożeniem feedback loop. Zbudować mały pipeline, wysłać kontrolowany batch, zmierzyć odpowiedzi i dopiero wtedy optymalizować T1/T2/scoring.
