# AGENT_GUIDE.md — Przewodnik agenta implementującego leadpipe

> **Witaj agencie.** Ten dokument został napisany przez innego agenta (CodexLuxeworbot, deepseek-v4-flash) w ramach sesji 2026-05-27. Jest tu wszystko co musisz wiedzieć, żeby zrozumieć, wdrożyć i rozszerzać leadpipe.

---

## 1. Co to jest i po co

**leadpipe** to deterministyczny pipeline kwalifikacji leadów B2B dla polskiej agencji WWW (MeNET — B Bozena). Od skanu domeny przez enrichment NIP/VAT i parser HTML po decyzję kampanijną opartą o jawne rulesety YAML.

### Pipeline: T0 → T0.5 → T1 → DecisionEngine

```
CSV import → Lead model → T0 skan → T0.5 enrichment → T1 parser → DecisionEngine → CampaignDecision + DecisionTrace
```

### Dwa repo

| Repo | Co zawiera | URL |
|---|---|---|
| `leadpipe` | Rdzeń pipeline'u — ten projekt | `https://github.com/bozenaopala56-glitch/leadpipe` |
| `leads-dashboard` | Dashboard webowy (FastAPI + vanilla JS) | `https://github.com/bozenaopala56-glitch/leads-dashboard` |

Dashboard jest osobnym repo i importuje moduły leadpipe. **Ten dokument dotyczy tylko leadpipe.**

---

## 2. Struktura repo

```
leadpipe/
├── README.md                        # Szybki start, struktura, status
├── CHANGELOG.md                     # Historia zmian
├── pyproject.toml                   # Pakiet Python, zależności, entrypoints
├── .env.example                     # Przykładowe zmienne środowiskowe
│
├── leadpipe/                        # Pakiet główny
│   ├── __init__.py                  # Wersja pakietu
│   ├── models.py                    # MODELE PYDANTIC — Lead, ScanResult, Signal, CampaignDecision, DecisionTrace, Batch, SuppressionEntry
│   ├── cli.py                       # CLI: import, scan, decide, pipeline
│   ├── engine.py                    # DecisionEngine — ładuje YAML, ewaluuje reguły
│   ├── ruleset.py                   # Loader i walidacja rulesetów YAML
│   ├── csv_schemas.py               # ImportCsvSchema, ExportCsvSchema, FeedbackCsvSchema
│   ├── db_schema.py                 # SQLAlchemy async schema (Postgres — Phase 2)
│   ├── decision_trace.py            # Budowanie trace decyzji
│   │
│   ├── rules/                         # RULESETY YAML — tu są reguły decyzyjne
│   │   ├── decision_gates.yml       # Bramki blokujące (suppression, opt-out, bounce)
│   │   ├── campaigns.yml            # Reguły kampanii (send, skip, manual_review)
│   │   ├── evidence.yml             # Co liczy się jako dowód
│   │   ├── feedback.yml             # Reguły feedback loop
│   │   ├── suppression.yml          # Reguły suppression
│   │   └── t2_eligibility.yml       # Kiedy T2 jest wymagane
│   │
│   ├── t0/                            # SKANER TECHNICZNY
│   │   ├── __init__.py
│   │   ├── runner.py                # Batch runner T0
│   │   ├── signals.py               # Agregacja sygnałów do słownika
│   │   ├── dns.py                   # DNS: A/AAAA, MX, TXT
│   │   ├── http.py                  # HTTP/HTTPS: status, redirects, headers
│   │   ├── ssl.py                   # TLS/SSL: cert validity, issuer, expiry
│   │   ├── html.py                  # HTML: viewport, title, OG, forms, CTA
│   │   ├── tech.py                  # Tech detection: WordPress, GTM, Meta Pixel
│   │   ├── url.py                   # URL normalization and parsing
│   │   └── performance.py           # TTFB, page size, gzip, cache headers
│   │
│   ├── t0_5/                          # ENRICHMENT BIZNESOWY
│   │   ├── __init__.py
│   │   ├── enrich_nip.py            # Walidacja NIP, checksum
│   │   ├── enrich_vat.py            # Biała Lista VAT
│   │   └── cache.py                 # Cache enrichmentu po lead_id + hash HTML
│   │
│   └── t1/                            # PARSER TREŚCI I KONTAKTU
│       ├── __init__.py
│       ├── _html.py                 # Helpers HTML (BeautifulSoup)
│       ├── contact.py               # Email, telefon, social links
│       ├── jsonld.py                # JSON-LD: Organization, LocalBusiness, etc.
│       ├── forms.py                 # Formularze kontaktowe
│       ├── cta.py                   # Call-to-action
│       ├── industry.py              # Fit branżowy
│       └── contact.py               # Scoring: contactability, lead_value, campaign_confidence
│
├── dashboard/                       # Prosty dashboard HTML/JS (nie mylić z leads-dashboard!)
│   ├── index.html                   # Makieta frontendowa
│   ├── app.js                       # Vanilla JS (stary — teraz jest osobne repo leads-dashboard)
│   ├── backend.py                   # Prosty serwer plików (stary)
│   ├── style.css                    # Styling
│   ├── data/sample-batch.json       # Przykładowe dane (stare)
│   └── README.md                    # Opis starego dashboardu
│
├── tests/                           # TESTY
│   ├── test_cli.py                  # Testy komend CLI
│   ├── test_models.py               # Testy modeli Pydantic
│   ├── test_t0.py                   # Testy skanera T0
│   ├── test_t0_5.py                 # Testy enrichmentu T0.5
│   └── test_t1.py                   # Testy parsera T1
│
├── deploy/                          # SYSTEMD + DEPLOY
│   ├── leadpipe-scan.service        # Systemd service dla skanera
│   ├── leadpipe-scan.timer          # Timer systemd (cron-like)
│   ├── leadpipe-dashboard.service   # Service dla starego dashboardu
│   └── smoke-test.sh                # Smoke test deployu
│
├── data/
│   ├── sample-batch.csv             # Przykładowy CSV do testów
│   ├── sample-leads-for-test.json   # Przykładowe leady do testów
│   └── sample-rules.yaml            # Przykładowe rulesety do testów
│
└── docs/
    ├── API_REFERENCE.md             # Dokumentacja API (modeli Pydantic)
    ├── ARCHITECTURE.md              # Architektura systemu, flow, granice MVP
    ├── RULES.md                     # Dokumentacja rulesetów YAML
    ├── CONTRIBUTING.md              # Jak dodawać kod, testy, kampanie
    ├── AGENT_GUIDE.md               # TEN PLIK
    └── archive/                     # STARE DOKUMENTY (nieaktualne)
        # ANALIZA-KRYTYCZNA.md, RAPORTY, ZADANIA, REGULY, SPECYFIKACJA, itp.
```

---

## 3. Co jest już ZROBIONE

### Rdzeń pipeline'u
- ✅ `models.py` — 10+ modeli Pydantic (Lead, ScanResult, CampaignDecision, DecisionTrace, itp.)
- ✅ `cli.py` — 4 komendy: `import`, `scan`, `decide`, `pipeline`
- ✅ `engine.py` — DecisionEngine z operatorami: exists, missing, eq, neq, gte, gt, lte, lt, in, contains
- ✅ `ruleset.py` — loader i walidacja YAML
- ✅ `csv_schemas.py` — walidacja CSV import/eksport/feedback
- ✅ `db_schema.py` — SQLAlchemy async schema (dla Phase 2 Postgres)
- ✅ `decision_trace.py` — budowanie trace decyzji

### T0: Skan techniczny
- ✅ DNS (A/AAAA, MX, TXT)
- ✅ HTTP/HTTPS (status, redirects, headers)
- ✅ SSL/TLS (validity, issuer, expiry)
- ✅ HTML (viewport, title, OG, forms, CTA)
- ✅ Tech detection (WordPress, Joomla, GTM, Meta Pixel)
- ✅ URL normalization and parsing
- ✅ Performance (TTFB, page size, gzip, cache)
- ✅ Batch runner z timeoutami i retry

### T0.5: Enrichment
- ✅ NIP validation + checksum
- ✅ Biała Lista VAT
- ✅ Cache po lead_id + hash HTML
- ✅ REGON hook (placeholder)

### T1: Parser treści
- ✅ JSON-LD (Organization, LocalBusiness, Corporation, Store, ProfessionalService)
- ✅ Contact extraction (email, phone, social)
- ✅ Forms detection
- ✅ CTA analysis
- ✅ Industry fit (industrial/services/medical/digital)
- ✅ Scoring: contactability, lead_value, campaign_confidence

### Rulesety YAML
- ✅ `decision_gates.yml` — bramki blokujące
- ✅ `campaigns.yml` — reguły kampanii
- ✅ `evidence.yml` — definicje dowodów
- ✅ `feedback.yml` — feedback loop
- ✅ `suppression.yml` — suppression rules
- ✅ `t2_eligibility.yml` — kiedy T2 jest wymagane

### Testy
- ✅ **28 testów** — wszystkie przechodzą (`pytest -q`)
- ✅ Testy CLI, modeli, T0, T0.5, T1

### Dokumentacja
- ✅ README, CHANGELOG, API_REFERENCE, ARCHITECTURE, RULES, CONTRIBUTING
- ✅ TEN PLIK (AGENT_GUIDE)

---

## 4. Co musisz ZROBIĆ (jak to uruchomić)

### Wymagania
- Python 3.10+
- Dostęp do internetu (dla realnych skanów T0/T0.5)
- Opcjonalnie: Postgres (Phase 2)

### Instalacja

```bash
# 1. Klonuj repo
git clone https://github.com/bozenaopala56-glitch/leadpipe.git
cd leadpipe

# 2. Stwórz venv
python -m venv .venv
source .venv/bin/activate

# 3. Zainstaluj
pip install -U pip
pip install -e ".[test,postgres,csv]"

# 4. Testy
pytest -q
# Oczekiwany wynik: 28 passed
```

### Pierwsze użycie

```bash
# Import CSV
leadpipe import data/sample-batch.csv

# Skan batcha
leadpipe scan batch

# Decyzja
leadpipe decide batch

# Cały pipeline w jednym poleceniu
leadpipe pipeline 10 --file data/sample-batch.csv
```

### Stan

Domyślnie zapisywany w `.leadpipe/state.json`. Zmień przez `LEADPIPE_STATE`:

```bash
LEADPIPE_STATE=/tmp/moj-stan.json leadpipe pipeline 1 --file moj-plik.csv
```

### Skan jednej domeny

```bash
cat > /tmp/one-lead.csv <<'CSV'
domain,url,company_name,nip,source,contact_email,notes
example.pl,https://example.pl,Example Sp. z o.o.,1234563218,manual,biuro@example.pl,test
CSV

LEADPIPE_STATE=/tmp/leadpipe-one.json leadpipe pipeline 1 --file /tmp/one-lead.csv
```

---

## 5. Architektura w pigułce

```
CSV Import → ImportCsvSchema → Lead model → state.json
                                    |
                                    v
T0 runner → [dns, http, ssl, html, tech, performance] → ScanResult + signals
                                    |
                                    v
T0.5 → [nip validation, vat check, cache] → enriched Lead + signals
                                    |
                                    v
T1 → [jsonld, contact, forms, cta, industry] → signals + scoring
                                    |
                                    v
DecisionEngine → [rules/*.yml] → CampaignDecision + DecisionTrace
                                    |
                                    v
state.json / Postgres / CSV export
```

### DecisionEngine — jak to działa

1. Ładuje wszystkie `*.yml` z `leadpipe/rules/`
2. Waliduje modelem `RuleFile`
3. Sortuje reguły po `priority`, potem `key`
4. Buduje context z `Lead` + sygnałów T0/T0.5/T1/T2/feedback
5. Ewaluuje reguły do pierwszego matcha
6. Tworzy `CampaignDecision` + `DecisionTrace`

### Operatory reguł

| Operator | Działanie |
|---|---|
| `exists` | Sygnał jest obecny |
| `missing` | Sygnał jest nieobecny |
| `eq` | Równy |
| `neq` | Nierówny |
| `gte` | Większy lub równy |
| `gt` | Większy |
| `lte` | Mniejszy lub równy |
| `lt` | Mniejszy |
| `in` | W liście |
| `contains` | Zawiera substring |

### Tryby łączenia

| Tryb | Działanie |
|---|---|
| `and` | Wszystkie warunki muszą przejść |
| `or` | Wystarczy jeden |
| `weighted` | Suma wag vs threshold |

---

## 6. Jak dodać nową kampanię / regułę

1. Otwórz `leadpipe/rules/campaigns.yml`
2. Dodaj nową regułę:

```yaml
- key: NOWA_KAMPANIA_WWW
  priority: 200
  combine: and
  conditions:
    - signal: wordpress_present
      operator: eq
      value: true
    - signal: contactability
      operator: gte
      value: 60
  decision: send
  campaign: redesign_wordpress
  description: "Firma na WordPressie z dobrym kontaktem — propozycja redesignu."
```

3. Zwiększ `version` w nagłówku pliku
4. Uruchom testy: `pytest -q`
5. Zacommituj

Więcej w `docs/RULES.md` i `docs/CONTRIBUTING.md`.

---

## 7. FAQ dla agenta

**Q: Czym się różni `leadpipe` od `leads-dashboard`?**
A: `leadpipe` to rdzeń CLI — skanuje, decyduje, zapisuje state. `leads-dashboard` to panel webowy — pokazuje wyniki i pozwala na QA override.

**Q: Czy mogę używać bez Postgres?**
A: Tak. Phase 1 używa pliku JSON (`state.json`). Postgres jest w Phase 2.

**Q: Gdzie są wyniki skanu?**
A: W `~/.leadpipe/state.json` (domyślnie) lub w ścieżce z `LEADPIPE_STATE`.

**Q: Jak dodać T2 (screenshoty / vision)?**
A: T2 jest w Future Scope. Reguły `t2_eligibility.yml` już istnieją, ale brak modułu runtime. Zobacz `docs/ARCHITECTURE.md` sekcja T2.

**Q: Jak działa cache T0.5?**
A: Cache po `lead_id + hash_html`. Jeśli HTML się nie zmienił, enrichment jest czytany z cache.

**Q: Czy mogę używać leadpipe jako biblioteki?**
A: Tak. `from leadpipe.models import Lead`, `from leadpipe.engine import DecisionEngine`, `from leadpipe.cli import command_import`.

**Q: Jak dodać nowy sygnał do T0?**
A: Dodaj funkcję w `leadpipe/t0/` (np. `nowy_modul.py`), zaimportuj w `t0/signals.py`, dodaj test w `tests/test_t0.py`.

**Q: Jak działa override w dashboard?**
A: Dashboard ma osobne repo (`leads-dashboard`). `POST /api/leads/{id}/override` zapisuje nową decyzję w state.json, ale zachowuje oryginalny trace od DecisionEngine.

---

## 8. Status — co działa, co nie

| Funkcja | Status | Uwagi |
|---|---|---|
| T0 skan techniczny | ✅ Działa | DNS, HTTP, SSL, HTML, tech, performance |
| T0.5 enrichment NIP/VAT | ✅ Działa | Biała Lista, cache |
| T1 parser treści | ✅ Działa | JSON-LD, kontakt, formularze, CTA, branża |
| DecisionEngine YAML | ✅ Działa | 10 operatorów, 3 tryby łączenia |
| CLI import/scan/decide | ✅ Działa | 4 komendy |
| State JSON | ✅ Działa | File lock, atomowy zapis |
| Testy | ✅ 28 passed | CLI, modele, T0, T0.5, T1 |
| Dashboard webowy | ✅ W osobnym repo | `leads-dashboard` — FastAPI + vanilla JS |
| T2 Vision / screenshot | ❌ Nie ma | Phase 2 — reguły są, brak runtime |
| Postgres / SQLAlchemy | ❌ Nie ma | Phase 2 — schema jest, brak repo/migracji |
| Eksport CSV z CLI | ❌ Nie ma | Phase 2 — jest schema, brak komendy |
| Import feedback CSV | ❌ Nie ma | Phase 2 — jest schema, brak komendy |
| Kolejki Redis/RQ | ❌ Nie ma | Phase 2 |
| Outreach / wysyłka | ❌ Nie ma | Phase 2 |

---

## 9. Komendy quick-reference

```bash
# Testy
pytest -q                    # wszystkie testy
pytest tests/test_t0.py -v   # tylko T0

# CLI
leadpipe --help
leadpipe import plik.csv
leadpipe scan batch
leadpipe decide batch
leadpipe pipeline 10 --file plik.csv

# Stan
LEADPIPE_STATE=/tmp/test.json leadpipe pipeline 1 --file data/sample-batch.csv
cat ~/.leadpipe/state.json | python -m json.tool | head -30

# Jako biblioteka
python -c "from leadpipe.models import Lead; print(Lead.__fields__.keys())"
python -c "from leadpipe.engine import DecisionEngine; e=DecisionEngine(); print(e.evaluate(...))"
```

---

## 10. Gdzie szukać pomocy

| Pytanie o... | Gdzie szukać |
|---|---|
| Architekturę systemu | `docs/ARCHITECTURE.md` |
| Modele Pydantic | `leadpipe/models.py` lub `docs/API_REFERENCE.md` |
| Rulesety YAML | `leadpipe/rules/*.yml` lub `docs/RULES.md` |
| Jak dodać kod/testy/kampanię | `docs/CONTRIBUTING.md` |
| T0 skaner | `leadpipe/t0/` |
| T0.5 enrichment | `leadpipe/t0_5/` |
| T1 parser | `leadpipe/t1/` |
| DecisionEngine | `leadpipe/engine.py` |
| CLI | `leadpipe/cli.py` |
| Dashboard webowy | Osobne repo: `leads-dashboard` |
| Phase 2 (Postgres, T2, outreach) | `leads-dashboard/docs/FUTURE_SCOPE.md` |

---

*Dokument napisany przez CodexLuxeworbot (deepseek-v4-flash, opencode-go) 2026-05-27. Jeśli coś jest niejasne — przeczytaj `docs/ARCHITECTURE.md` i `docs/API_REFERENCE.md`.*
