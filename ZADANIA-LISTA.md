# ZADANIA-LISTA

Kazde zadanie jest TDD i miesci sie w max 8h roboczych.

| ID | Zadanie | Plik/funkcja | Kryterium ukonczenia |
|---|---|---|---|
| F0-01 | Napisac test finalnego enuma kampanii | `tests/test_models.py::test_campaign_key_contains_only_final_www_campaigns` | Test wymusza dokladnie 7 kampanii |
| F0-02 | Zmienic enum kampanii | `leadpipe/models.py::CampaignKey` | Enum ma tylko finalne 7 wartosci |
| F0-03 | Napisac test ladowania finalnych kampanii YAML | `tests/test_models.py`, `DecisionEngine()` | Engine laduje YAML bez bledu walidacji |
| F0-04 | Zmienic reguly kampanii YAML | `leadpipe/rules/campaigns.yml` | YAML zawiera tylko 7 finalnych kampanii |
| F0-05 | Napisac test dashboard labels | `tests` lub smoke JS fixture | Dashboard nie zawiera starych kampanii |
| F0-06 | Zmienic dashboard kampanii | `dashboard/app.js`, `dashboard/data/sample-batch.json` | Filtry, dropdown i subjecty uzywaja 7 kampanii |
| F0-07 | Uruchomic regresje | `pytest -q` | Wszystkie testy przechodza |
| M1-01 | Napisac test normalizacji domen | `leadpipe/models.py::Lead`, `leadpipe/normalization.py` | http/https/www/slash/case daja jedna domene |
| M1-02 | Zaimplementowac normalizacje domen | `leadpipe/normalization.py::normalize_domain` | Testy domen przechodza |
| M1-03 | Napisac test dedupe kluczy | `tests/test_dedupe.py` | Dedupe rozpoznaje domain/NIP/email/phone |
| M1-04 | Zaimplementowac dedupe | `leadpipe/dedupe.py::dedupe_leads` | Duplikaty sa scalane bez utraty zrodel |
| M1-05 | Napisac test Postgres schema | `tests/test_db_schema.py` | Alembic/metadata tworzy tabele |
| M1-06 | Dopelnic schema DB | `leadpipe/db_schema.py` | Lead, scan, signal, evidence, decision, trace, suppression zapisuje sie |
| M1-07 | Napisac test repozytoriow | `tests/test_repositories.py` | Save/load batcha i decyzji dziala |
| M1-08 | Zaimplementowac repozytoria | `leadpipe/repositories.py` | Test repozytoriow przechodzi |
| I1-01 | Napisac test importu CSV batcha | `tests/test_importer.py` | CSV tworzy batch i waliduje bledy |
| I1-02 | Zaimplementowac importer CSV | `leadpipe/importer.py::import_batch` | Import zapisuje leady i raport |
| I1-03 | Napisac test fixture sample | `data/sample-leads-for-test.json` | Sample ma rozne kampanie i decyzje |
| I1-04 | Przygotowac dane testowe | `data/fixtures/*.html`, `data/sample-*.json` | Fixture pokrywaja T0/T1/T2/gates |
| T0-01 | Napisac test HTTP scanner | `tests/test_t0_http.py` | Mock HTTP zwraca status, redirect, final_url |
| T0-02 | Zaimplementowac HTTP scanner | `leadpipe/t0/http.py::scan_http` | Obsluguje timeout, 429, 5xx, headers |
| T0-03 | Napisac test DNS scanner | `tests/test_t0_dns.py` | Mock DNS zwraca A/AAAA/MX/TXT/NS |
| T0-04 | Zaimplementowac DNS scanner | `leadpipe/t0/dns.py::scan_dns` | SERVFAIL/NXDOMAIN sa mapowane na sygnaly |
| T0-05 | Napisac test SSL scanner | `tests/test_t0_ssl.py` | Cert expired, invalid, hostname mismatch sa wykryte |
| T0-06 | Zaimplementowac SSL scanner | `leadpipe/t0/ssl.py::scan_tls` | Zwraca sygnaly trust i dowody |
| T0-07 | Napisac test HTML fetch/snapshot | `tests/test_t0_html.py` | HTML zapisuje snapshot i podstawowe meta |
| T0-08 | Zaimplementowac HTML scanner | `leadpipe/t0/html.py::scan_html` | Title/meta/viewport/canonical/lang sa parsowane |
| T0-09 | Napisac test robots/sitemap | `tests/test_t0_robots_sitemap.py` | robots disallow i sitemap 404 sa sygnalami |
| T0-10 | Zaimplementowac robots/sitemap | `leadpipe/t0/robots.py`, `leadpipe/t0/sitemap.py` | Wyniki trafiaja do `Evidence` |
| T0-11 | Napisac test performance light | `tests/test_t0_performance.py` | TTFB/total/page_size/compression sa liczone |
| T0-12 | Zaimplementowac performance light | `leadpipe/t0/performance.py` | `speed_slow`, `compression_missing`, `html_too_large` dzialaja |
| T0-13 | Napisac test tech detection | `tests/test_t0_tech.py` | WP, CMS, GTM, Meta Pixel sa wykryte |
| T0-14 | Zaimplementowac tech detection | `leadpipe/t0/tech.py::detect_tech` | Generuje sygnaly pod 7 kampanii |
| T0-15 | Napisac test orkiestratora T0 | `tests/test_t0_runner.py` | T0 sklada moduly i retry |
| T0-16 | Zaimplementowac T0 runner | `leadpipe/t0/runner.py::run_t0` | Zwraca `ScanResult` z signal/evidence |
| E05-01 | Napisac test NIP extraction | `tests/test_enrichment_nip.py` | NIP z HTML/importu przechodzi checksum |
| E05-02 | Zaimplementowac NIP extraction | `leadpipe/enrichment/nip.py` | Nie myli NIP z telefonem |
| E05-03 | Napisac test klienta Biala Lista VAT | `tests/test_enrichment_vat.py` | Mock API mapuje active/inactive/not_found |
| E05-04 | Zaimplementowac klienta VAT | `leadpipe/enrichment/vat.py` | Timeout nie blokuje leadu, zapisuje evidence |
| E05-05 | Napisac test cache enrichment | `tests/test_enrichment_cache.py` | Drugi odczyt nie wywoluje API |
| E05-06 | Zaimplementowac cache | `leadpipe/enrichment/cache.py` | TTL i key per NIP dzialaja |
| E05-07 | Napisac test merge identity | `tests/test_enrichment_merge.py` | VAT/HTML/import lacza nazwe i adres |
| E05-08 | Zaimplementowac merge identity | `leadpipe/enrichment/runner.py::run_t0_5` | Zwraca business signals |
| T1-01 | Napisac test JSON-LD parsera | `tests/test_t1_jsonld.py` | Organization/LocalBusiness/Service sa parsowane |
| T1-02 | Zaimplementowac JSON-LD parser | `leadpipe/t1/jsonld.py` | Zwraca firme, adres, telefon, social |
| T1-03 | Napisac test meta/OG parsera | `tests/test_t1_meta.py` | Title, description, OG, canonical sa parsowane |
| T1-04 | Zaimplementowac meta/OG parser | `leadpipe/t1/meta.py` | Sygnaly SEO/trust sa zapisywane |
| T1-05 | Napisac test email/telefon | `tests/test_t1_contact.py` | Email, mailto, tel i polskie telefony sa wykryte |
| T1-06 | Zaimplementowac contact parser | `leadpipe/t1/contact.py` | Contactability ma oczekiwane progi |
| T1-07 | Napisac test formularzy | `tests/test_t1_forms.py` | Form action/input/textarea/contact form sa wykryte |
| T1-08 | Zaimplementowac form parser | `leadpipe/t1/forms.py` | `form_present/form_missing` dziala |
| T1-09 | Napisac test CTA | `tests/test_t1_cta.py` | CTA missing/weak/contact_hidden sa klasyfikowane |
| T1-10 | Zaimplementowac CTA parser | `leadpipe/t1/cta.py` | Wyniki zasilaja kampanie conversion/ads |
| T1-11 | Napisac test industry hints | `tests/test_t1_industry.py` | Web/design/SEO/ads/software sa wykryte jako konkurencja |
| T1-12 | Zaimplementowac industry parser | `leadpipe/t1/industry.py` | `industry_fit` i exclusion hints dzialaja |
| T1-13 | Napisac test orkiestratora T1 | `tests/test_t1_runner.py` | T1 laczy parsers i evidence |
| T1-14 | Zaimplementowac T1 runner | `leadpipe/t1/runner.py::run_t1` | Zwraca komplet sygnalow pod gates |
| G-01 | Napisac test compliance gate | `tests/test_gates.py` | Opt-out/customer/deal/hard bounce blokuje |
| G-02 | Zaimplementowac compliance gate | `leadpipe/rules/decision_gates.yml`, `engine.py` | Suppression ma najwyzszy priorytet |
| G-03 | Napisac test data quality gate | `tests/test_gates.py` | Brak strony/portal/marketplace daje skip/manual |
| G-04 | Zaimplementowac data quality gate | `leadpipe/rules/decision_gates.yml` | Firmy bez strony nie ida do kampanii |
| G-05 | Napisac test industry/contact gates | `tests/test_gates.py` | Progi fit i contactability dzialaja |
| G-06 | Zaimplementowac industry/contact gates | `leadpipe/rules/decision_gates.yml` | <40 contact skip, 40-54 manual |
| G-07 | Napisac test scan health gate | `tests/test_gates.py` | Timeout/429/SERVFAIL ida do retry |
| G-08 | Zaimplementowac scan health gate | `leadpipe/rules/decision_gates.yml` | Final failed nie trafia do send |
| C-01 | Napisac test kazdej kampanii | `tests/test_campaigns.py` | 7 happy pathow zwraca oczekiwana kampanie |
| C-02 | Zaimplementowac final campaign YAML | `leadpipe/rules/campaigns.yml` | Wszystkie 7 kampanii maja progi i evidence |
| C-03 | Napisac test konfliktow kampanii | `tests/test_campaign_conflicts.py` | Priorytet ads/mobile/trust/outdated/conversion/wp/tech dziala |
| C-04 | Zaimplementowac conflict handling | `leadpipe/engine.py`, YAML priorities | Wygrywa jedna kampania |
| C-05 | Napisac test suppression engine | `tests/test_suppression.py` | Bounce/opt-out/cooldown blokuje eksport |
| C-06 | Zaimplementowac suppression engine | `leadpipe/suppression.py` | TTL i permanent scope dzialaja |
| EV-01 | Napisac test formatowania dowodow | `tests/test_evidence_engine.py` | 1-3 dowody sa czytelne i faktograficzne |
| EV-02 | Zaimplementowac evidence engine | `leadpipe/evidence_engine.py` | CSV i dashboard dostaja te same teksty |
| DT-01 | Napisac test DecisionTrace | `tests/test_decision_trace.py` | Trace ma evaluated_rules, winner, blockers, score |
| DT-02 | Rozszerzyc DecisionTrace | `leadpipe/decision_trace.py`, `engine.py` | Kazda decyzja zapisuje trace |
| CSV-01 | Napisac test eksportu CSV | `tests/test_export.py` | CSV ma wymagane kolumny i pomija suppression |
| CSV-02 | Zaimplementowac eksport CSV | `leadpipe/export.py`, `csv_schemas.py` | Eksport gotowy do QA/outreach |
| FB-01 | Napisac test importu feedbacku | `tests/test_feedback.py` | positive/negative/bounce/opt_out sa parsowane |
| FB-02 | Zaimplementowac feedback import | `leadpipe/feedback.py` | Feedback aktualizuje suppression i metryki |
| D-01 | Napisac test API dashboard batch | `tests/test_dashboard_api.py` | API zwraca batch, leady, kampanie, trace |
| D-02 | Zaimplementowac backend dashboardu | `dashboard/backend.py` | Dashboard czyta realne dane z DB |
| D-03 | Napisac test QA actions | `tests/test_dashboard_qa.py` | approve/reject/manual zapisuje decyzje |
| D-04 | Zaimplementowac QA workflow | `dashboard/app.js`, backend endpointy | Zmiany QA sa trwale |
| D-05 | Napisac test widoku kampanii | `tests/test_dashboard_campaigns.py` | Widok pokazuje tylko 7 kampanii |
| D-06 | Zaimplementowac widok kampanii | `dashboard/app.js` | Filtry, metryki i lista leadow dzialaja |
| D-07 | Napisac test copywriting preview | `tests/test_copy_preview.py` | Preview uzywa subject i evidence |
| D-08 | Zaimplementowac copywriting preview | `dashboard/app.js`, `leadpipe/copy_preview.py` | QA widzi podglad bez wysylki |
| D-09 | Napisac test batch view/export | `tests/test_dashboard_export.py` | Batch eksportuje zatwierdzone leady |
| D-10 | Zaimplementowac batch view/export | `dashboard/app.js`, backend | CSV zgadza sie z backend export |
| T2-01 | Napisac test Playwright screenshot | `tests/test_t2_screenshots.py` | Desktop/mobile screenshot powstaje dla fixture |
| T2-02 | Zaimplementowac screenshot service | `leadpipe/t2/screenshots.py` | Blank/captcha/consent wall sa wykryte |
| T2-03 | Napisac test dynamic prompt buildera | `tests/test_t2_prompts.py` | Prompt zawiera kontekst i 7 kampanii |
| T2-04 | Zaimplementowac prompt builder | `leadpipe/t2/prompts.py` | Prompt JSON contract jest stabilny |
| T2-05 | Napisac test klienta kimi k2.5 vision | `tests/test_t2_vision_client.py` | Mock zwraca labels/confidence/campaign |
| T2-06 | Zaimplementowac vision client | `leadpipe/t2/vision_client.py` | Timeout/retry/cost sa obslugiwane |
| T2-07 | Napisac test T2 runnera | `tests/test_t2_runner.py` | `t2_required` generuje T2 signals/evidence |
| T2-08 | Zaimplementowac T2 runner | `leadpipe/t2/runner.py` | Wynik T2 wraca do campaign engine |
| Q-01 | Napisac test RQ jobow | `tests/test_queue.py` | Job T0/T1/T2 ma idempotency key |
| Q-02 | Zaimplementowac Redis/RQ jobs | `leadpipe/jobs.py` | Retry i status jobow dzialaja |
| VM-01 | Napisac test konfiguracji Postgres | `tests/test_settings.py` | Env vars waliduja DSN i pool |
| VM-02 | Przygotowac Postgres setup | `deploy/postgres.sql`, docs | DB tworzy role, database, extensions |
| VM-03 | Napisac test konfiguracji Redis/RQ | `tests/test_settings.py` | Redis URL i queue names sa walidowane |
| VM-04 | Przygotowac Redis/RQ setup | `deploy/redis.md`, `leadpipe/jobs.py` | Worker laczy sie z Redis |
| VM-05 | Dodac docker compose dla VM | `docker-compose.yml` | `docker compose up -d` uruchamia Postgres 16 i Redis 7 z wolumenem `pgdata` |
| VM-06 | Dodac przykladowy env | `.env.example` | Plik ma wszystkie wymagane zmienne z komentarzami operatorskimi |
| VM-07 | Dodac checklist deployu | `DEPLOY-CHECKLIST.md` | Swieza VM ma instrukcje od instalacji Dockera do smoke testu |
| VM-08 | Dodac systemd dashboardu | `deploy/leadpipe-dashboard.service` | Dashboard startuje z `/opt/leadpipe/.env` i loguje do journald |
| VM-09 | Dodac timer skanu | `deploy/leadpipe-scan.service`, `deploy/leadpipe-scan.timer` | Periodic scan odpala sie z systemd timer i ma reczne uruchomienie |
| HERMES-01 | Dodac skill Hermesa dla pipeline | `hermes/leadpipe/SKILL.md` | Telegram obsluguje scan/decide/report/qa/export i wskazuje logi oraz CSV |
| DEP-01 | Napisac smoke test CLI | `tests/test_smoke_pipeline.py` | Fixture batch przechodzi end-to-end z mockami |
| DEP-02 | Zaimplementowac CLI smoke | `leadpipe/cli.py::smoke` | Jedna komenda robi import->decision->CSV |
| DEP-03 | Napisac test systemd templates | `tests/test_deploy_files.py` | Unit files maja wymagane komendy/env |
| DEP-04 | Dodac systemd/cron pliki | `deploy/*.service`, `deploy/*.timer` | VM moze uruchomic API i workery |
| DEP-05 | Napisac dokument runbook | `RUNBOOK.md` | Operator ma start/stop/retry/debug |
| DEP-06 | Dodac skrypt smoke E2E deployu | `deploy/smoke-test.sh` | Skrypt robi import, scan, decide, export i konczy `SMOKE OK` albo `SMOKE FAIL` |
| DEP-07 | Dodac fixture CSV smoke | `data/sample-batch.csv` | Smoke test ma lokalny CSV bez szukania danych poza repo |
| DEP-08 | Napisac test kompletnego deploy packa | `tests/test_deploy_files.py` | Test sprawdza istnienie compose, env, checklisty, skill, systemd i smoke script |
| QA-01 | Napisac test integracyjny 20 leadow | `tests/test_integration_batch.py` | Mix kampanii daje stabilne decyzje |
| QA-02 | Dodac smoke dataset 100 leadow | `data/smoke-batch.json` | Pokrywa 7 kampanii, skip, retry, manual, T2 |
| QA-03 | Napisac test regresji starych kampanii | `tests/test_no_legacy_campaigns.py` | Stare kampanie nie wystepuja w runtime |
| QA-04 | Dodac raport metryk smoke | `leadpipe/reports.py` | Raport pokazuje counts, FP do QA, suppression |
