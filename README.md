# leadpipe

Pipeline kwalifikacji leadow B2B dla polskiej agencji WWW: od skanu domeny przez enrichment i parser HTML do decyzji kampanijnej opartej o jawne rulesety YAML.

## Szybki Start

Wymagania: Python 3.10+, dostep do internetu dla realnych skanow T0/T0.5 oraz opcjonalnie Postgres, jesli uzywasz schematu z `leadpipe/db_schema.py`.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e ".[test,postgres,csv]"
pytest
```

CLI instaluje komende `leadpipe`:

```bash
leadpipe --help
leadpipe import data/sample-batch.csv
leadpipe scan batch
leadpipe decide batch
leadpipe pipeline 10 --file data/sample-batch.csv
```

Stan lokalny CLI jest zapisywany domyslnie w `.leadpipe/state.json`. Sciezke mozna zmienic przez `LEADPIPE_STATE`:

```bash
LEADPIPE_STATE=/tmp/leadpipe-state.json leadpipe pipeline 1 --file data/sample-batch.csv
```

## Przyklad: Skan Jednej Domeny Od A Do Z

Najprosciej przygotowac maly CSV i uruchomic pipeline:

```bash
cat > /tmp/one-lead.csv <<'CSV'
domain,url,company_name,nip,source,contact_email,notes
example.pl,https://example.pl,Example Sp. z o.o.,1234563218,manual,biuro@example.pl,test
CSV

LEADPIPE_STATE=/tmp/leadpipe-one.json leadpipe pipeline 1 --file /tmp/one-lead.csv
```

Ten przebieg robi:

1. import rekordu CSV do modelu `Lead`;
2. T0: DNS, HTTP/HTTPS, TLS, HTML, technologie i performance;
3. T0.5: NIP, walidacja VAT i cache enrichmentu;
4. T1: JSON-LD, kontakt, formularze, CTA i fit branzy;
5. `DecisionEngine`: bramki decyzyjne, suppression, T2 eligibility i kampanie.

Program wypisze decyzje, np. `decision=manual_review`, `decision=send`, `decision=skip`, `decision=retry` albo `decision=t2_required`.

## Struktura Projektu

| Sciezka | Rola |
|---|---|
| `leadpipe/models.py` | Kontrakty Pydantic: leady, sygnaly, dowody, decyzje, feedback, batch i suppression. |
| `leadpipe/t0/` | Skaner techniczny: DNS, HTTP, SSL/TLS, HTML, tech detection, performance i batch runner. |
| `leadpipe/t0_5/` | Enrichment biznesowy: NIP, Biala Lista VAT i cache. |
| `leadpipe/t1/` | Parser HTML/treści: JSON-LD, kontakt, formularze, CTA, branza i contactability. |
| `leadpipe/rules/` | Wersjonowane rulesety YAML: gates, kampanie, evidence, suppression, feedback i T2 eligibility. |
| `leadpipe/engine.py` | Config-first decision engine ladujacy YAML i zwracajacy `CampaignDecision` + `DecisionTrace`. |
| `leadpipe/db_schema.py` | Async SQLAlchemy schema dla Postgres: leady, scan results, decyzje, trace, feedback i suppression. |
| `leadpipe/csv_schemas.py` | Walidacja importu/eksportu/feedbacku CSV. |
| `leadpipe/cli.py` | CLI import/scan/decide/pipeline na lokalnym pliku stanu JSON. |
| `dashboard/` | Prosty dashboard QA i statyczne sample data. |
| `deploy/` | Systemd, timer i smoke test dla VM. |
| `tests/` | Testy jednostkowe modeli, CLI, T0, T0.5 i T1. |

## Status Pipeline

| Etap | Status | Co dziala |
|---|---|---|
| T0 | ✅ | DNS, HTTP/HTTPS, redirects, TLS, HTML, CTA hints, CMS/WP/GTM/Pixel, performance i batch runner. |
| T0.5 | ✅ | Ekstrakcja i checksum NIP, lookup REGON hook, Biala Lista VAT, merge do `Lead`, cache. |
| T1 | ✅ | JSON-LD, email, telefon, social, formularze, CTA, industry fit, lead value, campaign confidence. |
| T2 | ⏳ | Reguly kwalifikacji i prompt opisane w YAML/specyfikacji; brak runtime modułu screenshot/vision. |

## Pelna Dokumentacja

- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Rules](docs/RULES.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Dokumenty zrodlowe pozostaja w root repo: `REGULY*.md`, `SPECYFIKACJA-T0-T1-T2.md`, `ANALIZA-KRYTYCZNA.md`, `RAPORT-*.md`, `ZADANIA-*.md`, `ARCHITEKTURA.md`, `PLAN-IMPLEMENTACJI.md` i `KAMPANIE-REDESIGN.md`.
