# PLAN-IMPLEMENTACJI

Data: 2026-05-23  
Tryb pracy: TDD, zadania max 8h, najpierw test, potem kod.

## Faza 0: kontrakt kampanii

Cel: usunac bloker starego enuma i zablokowac powrot kampanii spoza finalnej siodemki.

Zakres:

- `leadpipe/models.py`: `CampaignKey` ma tylko 7 finalnych wartosci.
- `leadpipe/rules/campaigns.yml`: tylko 7 kampanii.
- `dashboard/app.js` i `dashboard/data/sample-batch.json`: tylko 7 kampanii.
- test kontraktowy sprawdza dokladny set kampanii.

Kryterium: `pytest -q` przechodzi i `rg` nie znajduje starych kampanii w kodzie runtime.

## Faza 1: fundament modeli, importu i storage

Cel: stabilny kontrakt danych przed scannerami.

Zakres: modele, CSV import, dedupe, Postgres schema, repozytoria, fixtures, seed smoke.

Kryterium: import batcha tworzy leady, duplikaty sa scalane, a decyzje i trace zapisuja sie w DB.

## Faza 2: T0 scanner

Cel: tani deterministyczny scan techniczny.

Zakres: HTTP, DNS, TLS, HTML snapshot, robots, sitemap, performance light, tech detection, retry.

Kryterium: batch 100 domen konczy sie bez wiszacych jobow; transient errors ida do retry; aktywne strony maja evidence.

## Faza 3: T0.5 enrichment

Cel: potwierdzenie firmy i NIP.

Zakres: NIP extraction, checksum, Biala Lista VAT client, cache, merge identity.

Kryterium: NIP nie myli sie z telefonem, cache dziala, brak NIP obniza confidence bez automatycznego skipu.

## Faza 4: T1 parser

Cel: kontakt, oferta, CTA, formularze i fit.

Zakres: JSON-LD, meta, OG, email, telefon, formularz, CTA, industry hints, contactability, lead value.

Kryterium: fixture polskich stron daje oczekiwane sygnaly i dowody.

## Faza 5: gates, campaign engine, evidence

Cel: finalna decyzja zgodna z `REGULY-FINAL.md`.

Zakres: 7 bramek, 7 kampanii, suppression, DecisionTrace, evidence formatter.

Kryterium: kazdy `send` ma kampanie, confidence, rule_key i min. dowody; suppression nigdy nie idzie do CSV.

## Faza 6: CSV, feedback i dashboard

Cel: realny workflow QA.

Zakres: CSV export, feedback import, batch view, kampanie, copywriting preview, approve/reject/manual.

Kryterium: QA moze zatwierdzic batch, wyeksportowac CSV i zaimportowac feedback zmieniajacy suppression.

## Faza 7: T2 pilot

Cel: selektywna ocena wizualna.

Zakres: Playwright screenshots, blank/captcha checks, dynamic prompts, kimi k2.5 vision client, T2 signals/evidence.

Kryterium: T2 odpala sie tylko dla `t2_required` albo jawnego QA, zapisuje koszt i rozstrzyga kampanie wizualne.

## Faza 8: VM deploy

Cel: uruchomienie pipeline na VM.

Zakres:

- `docker-compose.yml`: Postgres 16 i Redis 7 startuja przez `docker compose up -d`, jedyny trwaly wolumen to `pgdata`.
- `.env.example`: komplet zmiennych dla DB, Redis, OpenCode Go, budzetu T2, mounta GCS, katalogu danych i `USER_AGENT`.
- `DEPLOY-CHECKLIST.md`: runbook od swiezej VM do smoke testu, bez szukania konfiguracji w innych miejscach.
- `deploy/leadpipe-dashboard.service`: systemd dla dashboardu.
- `deploy/leadpipe-scan.service` i `deploy/leadpipe-scan.timer`: codzienny periodic scan z mozliwoscia recznego startu.
- `deploy/smoke-test.sh`: import -> scan -> decide -> export -> walidacja CSV.
- `hermes/leadpipe/SKILL.md`: komendy Telegrama `/leadpipe scan`, `decide`, `report`, `qa`, `export` z lokalizacja logow i CSV.

Kryterium: po deployu smoke batch przechodzi import -> decyzje -> CSV.

Pelny podzial jednodniowych zadan jest w `ZADANIA-LISTA.md`, krytyka w `ZADANIA-KRYTYKA.md`, batche w `ZADANIA-BATCHE.md`, a plan testow w `ZADANIA-TDD.md`.
