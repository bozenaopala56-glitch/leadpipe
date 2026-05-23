# ZADANIA-TDD

## Zasada

Kazde zadanie zaczyna sie od testu, ktory najpierw failuje. Kod jest gotowy dopiero po zielonym tescie lokalnym i braku regresji w `pytest -q`.

## Batch 1

Testy: `tests/test_models.py`, test braku legacy campaigns.  
Mocki: brak.  
Fixture: `data/sample-leads-for-test.json`, `dashboard/data/sample-batch.json`.  
Cel: enum, YAML i dashboard maja tylko 7 kampanii.

## Batch 2

Testy: `tests/test_dedupe.py`, `tests/test_db_schema.py`, `tests/test_repositories.py`.  
Mocki: SQLite/Postgres test container albo transaction rollback.  
Fixture: leady z duplikatami domen, NIP, emaili i telefonow.

## Batch 3

Testy: `tests/test_importer.py`.  
Mocki: repozytorium batcha.  
Fixture: poprawny CSV, CSV z blednym NIP, duplikaty, brak domeny.

## Batch 4

Testy: `tests/test_t0_http.py`, `tests/test_t0_dns.py`, `tests/test_t0_ssl.py`.  
Mocki: `respx`/mock HTTP, fake resolver DNS, fake cert socket.  
Fixture: 200, redirect, timeout, 429, 503, NXDOMAIN, SERVFAIL, cert expired.

## Batch 5

Testy: `tests/test_t0_html.py`, `tests/test_t0_robots_sitemap.py`.  
Mocki: HTTP responses z fixture HTML/robots/sitemap.  
Fixture: HTML z meta/viewport, HTML bez viewport, robots disallow all, sitemap ok/404.

## Batch 6

Testy: `tests/test_t0_performance.py`, `tests/test_t0_tech.py`, `tests/test_t0_runner.py`.  
Mocki: zegar/monotonic, HTTP fixture.  
Fixture: WP generator, wp-content, GTM, Meta Pixel, duzy HTML, brak gzip.

## Batch 7

Testy: `tests/test_enrichment_nip.py`, `tests/test_enrichment_vat.py`, `tests/test_enrichment_cache.py`, `tests/test_enrichment_merge.py`.  
Mocki: Biala Lista VAT API, cache in-memory.  
Fixture: poprawny NIP, zly checksum, numer telefonu podobny do NIP, VAT active/inactive/not_found.

## Batch 8

Testy: `tests/test_t1_jsonld.py`, `tests/test_t1_meta.py`, `tests/test_t1_contact.py`, `tests/test_t1_forms.py`.  
Mocki: brak, parser HTML na fixture.  
Fixture: JSON-LD Organization/LocalBusiness, mailto/tel, formularz kontaktowy, brak formularza.

## Batch 9

Testy: `tests/test_t1_cta.py`, `tests/test_t1_industry.py`, `tests/test_t1_runner.py`.  
Mocki: brak.  
Fixture: strony z mocnym CTA, slabe CTA, ukryty kontakt, agencja web, software house, producent B2B.

## Batch 10

Testy: `tests/test_gates.py`.  
Mocki: sygnaly recznie budowane.  
Fixture: opt-out, competitor, low contactability, retry, final failed, brak evidence.

## Batch 11

Testy: `tests/test_campaigns.py`, `tests/test_campaign_conflicts.py`, `tests/test_suppression.py`.  
Mocki: brak zewnetrznych API.  
Fixture: po 2-3 leady na kazda kampanie plus konflikty ads/mobile/trust/outdated/conversion/wp/tech.

## Batch 12

Testy: `tests/test_evidence_engine.py`, `tests/test_decision_trace.py`, `tests/test_export.py`, `tests/test_feedback.py`.  
Mocki: repozytorium i zegar.  
Fixture: decyzje send/manual/skip, suppression, positive reply, hard bounce, opt-out.

## Batch 13

Testy: `tests/test_dashboard_api.py`, `tests/test_dashboard_qa.py`.  
Mocki: test DB i klient HTTP backendu.  
Fixture: batch z leadami we wszystkich statusach QA.

## Batch 14

Testy: `tests/test_dashboard_campaigns.py`, `tests/test_copy_preview.py`, `tests/test_dashboard_export.py`.  
Mocki: backend API.  
Fixture: 7 kampanii, zatwierdzone i odrzucone leady, subject/evidence.

## Batch 15

Testy: `tests/test_t2_screenshots.py`, `tests/test_t2_prompts.py`, `tests/test_t2_vision_client.py`, `tests/test_t2_runner.py`.  
Mocki: Playwright page dla unitow, fake screenshot files, mock kimi k2.5 API, fake cost meter.  
Fixture: desktop/mobile screenshot, blank page, captcha, consent wall, odpowiedzi vision dla visual_outdated/weak_cta/mobile/trust.

## Batch 16

Testy: `tests/test_queue.py`, `tests/test_smoke_pipeline.py`, `tests/test_integration_batch.py`, `tests/test_no_legacy_campaigns.py`.  
Mocki: Redis faker albo test Redis, T2 mock, VAT mock, HTTP fixtures.  
Fixture: smoke batch 100 leadow, 7 kampanii, skip, retry, manual, T2.

## Batch 17

Testy: `tests/test_settings.py`, `tests/test_deploy_files.py`.  
Mocki: env vars.  
Fixture: `.env.example`, `docker-compose.yml`, systemd unit templates, timer templates, `hermes/leadpipe/SKILL.md`, `DEPLOY-CHECKLIST.md`, `deploy/smoke-test.sh`, `data/sample-batch.csv`.

Dodatkowe testy deploy:

- `tests/test_deploy_files.py::test_required_deploy_files_exist` sprawdza istnienie `docker-compose.yml`, `.env.example`, `DEPLOY-CHECKLIST.md`, `deploy/leadpipe-dashboard.service`, `deploy/leadpipe-scan.service`, `deploy/leadpipe-scan.timer`, `deploy/smoke-test.sh`, `hermes/leadpipe/SKILL.md`.
- `tests/test_deploy_files.py::test_env_example_has_required_fields` sprawdza pola `POSTGRES_DSN`, `REDIS_URL`, `OPENCODE_GO_API_KEY`, `OPENCODE_GO_BASE_URL`, `T2_DAILY_BUDGET`, `T2_COST_PER_CALL`, `GCS_MOUNT`, `PIPELINE_DATA_DIR`, `USER_AGENT`.
- `tests/test_deploy_files.py::test_docker_compose_services` sprawdza obrazy `postgres:16` i `redis:7` oraz wolumen `pgdata`.
- `tests/test_deploy_files.py::test_hermes_skill_documents_commands` sprawdza komendy `/leadpipe scan`, `/leadpipe decide`, `/leadpipe report`, `/leadpipe qa`, `/leadpipe export` oraz sciezki logow i eksportow CSV.
- `tests/test_deploy_files.py::test_smoke_script_contract` sprawdza kroki `leadpipe import`, `leadpipe scan`, `leadpipe decide`, `leadpipe export` oraz komunikaty `SMOKE OK` i `SMOKE FAIL`.

## Co mockowac zawsze

- Zewnetrzne HTTP stron w unitach T0.
- DNS resolver w unitach DNS.
- Biala Lista VAT.
- Kimi k2.5 vision.
- Zegar dla TTL/cooldown.
- Redis/RQ w unitach, realny Redis dopiero w smoke/deploy.

## Czego nie mockowac w integracji

- Walidacji Pydantic modeli.
- Ladowania YAML przez `DecisionEngine`.
- Dedupe i scoringu kampanii.
- Formatowania CSV.
- DecisionTrace.
