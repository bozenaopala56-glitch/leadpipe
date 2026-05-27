# ZADANIA-KRYTYKA

## 1. Co bylo bledne albo niepelne

- Stary plan mial kampanie spoza finalnego zakresu: `NEW_WEBSITE`, `CARE_PLAN`, `QUALIFIED_CUSTOM` oraz techniczne kampanie email/SEO/security/performance.
- Brakowalo jawnego zadania blokujacego powrot starych kampanii w testach.
- T0 bylo opisane jako jeden duzy etap, a realnie trzeba je podzielic na HTTP, DNS, SSL, HTML, robots, sitemap, performance i tech detection.
- T0.5 wymagal osobnych zadan na NIP, Biala Liste VAT, cache i merge identity.
- T1 bylo za szerokie; JSON-LD, kontakt, formularze, CTA i industry hints musza byc rozdzielone.
- Dashboard byl traktowany jako jeden punkt, a potrzebuje osobnych zadan dla QA, kampanii, eksportu, batch view i preview.
- T2 bylo zbyt ryzykowne jako jedno zadanie; podzielono je na screenshoty, prompt builder, klient vision i runner.
- Brakowalo zadan deployowych: Postgres, Redis/RQ, systemd, cron/timers, smoke CLI.
- Brakowalo przykladowych danych smoke i regresji "no legacy campaigns".

## 2. Co dodalem

- Faza 0 z testami i poprawka enuma, YAML oraz dashboardu.
- Pelne zadania T0: HTTP, DNS, SSL, HTML, robots, sitemap, performance, tech detection, runner.
- Pelne zadania T0.5: NIP extraction, checksum, Biala Lista VAT, cache, merge.
- Pelne zadania T1: JSON-LD, meta/OG, email, telefon, formularz, CTA, industry hints.
- Gates dla compliance, data quality, industry fit, scan health, contactability, evidence/T2 i campaign ready.
- Campaign engine z 7 kampaniami i testami konfliktow.
- Evidence engine, DecisionTrace, CSV export, feedback import i suppression.
- Dashboard QA workflow, widok kampanii, batch view, export i copywriting preview.
- T2 Playwright + kimi k2.5 vision z dynamicznymi promptami.
- VM deploy: Postgres, Redis/RQ, systemd, cron/timers, CLI smoke.
- Testowe dane: fixture HTML, JSON sample, smoke batch 100 leadow.

## 3. Co podzielilem, bo bylo >8h

| Pierwotny obszar | Problem | Podzial |
|---|---|---|
| T0 scanner | za duzy i ryzykowny | 16 zadan: HTTP, DNS, SSL, HTML, robots, sitemap, performance, tech, runner |
| T0.5 enrichment | API i parsing w jednym | 8 zadan: NIP, VAT, cache, merge |
| T1 parser | zbyt wiele parserow naraz | 14 zadan: JSON-LD, meta, contact, forms, CTA, industry, runner |
| Campaign engine | reguly, konflikty i suppression razem | osobno kampanie, konflikty, suppression |
| Dashboard | frontend + backend + eksport + QA | 10 zadan dashboardowych |
| T2 | najwieksze ryzyko techniczne | screenshoty, prompt, client, runner |
| Deploy | infrastruktura i smoke w jednym | Postgres, Redis/RQ, systemd, cron, CLI smoke |

## 4. Co usunalem jako zbedne

- Kampanie dla firm bez strony jako finalny cel outreach. Pipeline moze je oznaczyc jako `manual_review/skip`, ale finalny zestaw celuje w firmy, ktore maja strone.
- Samodzielne kampanie email deliverability, SEO visibility, pure security fix i care plan.
- Automatyczna wysylka maili w MVP. `send` zostaje statusem QA/CSV.
- T2 dla kazdego leadu. T2 jest tylko dla niejednoznacznych albo wizualnych decyzji.

## 5. Ryzyka po poprawkach

- `T2_SKIP_STRONG_CAMPAIGN` w obecnym MVP kieruje mocne kampanie do QA, nie do automatycznej wysylki. To jest zgodne z bezpiecznym MVP, ale trzeba to jawnie utrzymac w dashboardzie.
- Dynamiczne prompty T2 wymagaja stabilnego JSON contract; bez tego vision client moze rozbic engine.
- VAT API moze byc niestabilne, dlatego cache i graceful degradation sa osobnymi zadaniami.
- Dashboard demo jest statyczny; backend z DB trzeba potraktowac jako osobny milestone, nie kosmetyke.

## 6. Finalna korekta

Lista w `ZADANIA-LISTA.md` po krytyce:

- ma zadania jednodniowe;
- kazde zadanie ma plik/funkcje i kryterium;
- kazde zadanie zaczyna sie od testu;
- obejmuje wszystkie wymagane obszary z briefu;
- nie zawiera kampanii spoza finalnej siodemki jako celu runtime.
