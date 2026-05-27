# API Reference

Dokumentacja obejmuje publiczne moduly runtime z pakietu `leadpipe`: T0, T0.5, T1, CLI, modele, engine i ruleset. Funkcje zaczynajace sie od `_` sa traktowane jako prywatne helpery.

## `leadpipe`

### `DecisionEngine`

Reeksport z `leadpipe.engine.DecisionEngine`.

```python
from leadpipe import DecisionEngine
```

### `CURRENT_RULESET_VERSION`, `RulesetVersion`, `load_current_ruleset_version`

Reeksport z `leadpipe.ruleset`.

```python
from leadpipe import CURRENT_RULESET_VERSION, load_current_ruleset_version
```

## T0: `leadpipe.t0`

### `compute_t0_signals(domain: str) -> dict[str, Any]`

Uruchamia caly skan techniczny dla domeny: DNS, HTTP, TLS, fetch HTML, parser HTML, tech detection i performance.

Parametry:

| Parametr | Typ | Opis |
|---|---|---|
| `domain` | `str` | Domena lub URL do normalizacji i skanowania. |

Zwraca `dict` z sygnalami gotowymi dla `DecisionEngine.evaluate()` oraz zagnieżdżonym `scan_result`.

Przyklad:

```python
from leadpipe.t0 import compute_t0_signals

result = compute_t0_signals("example.pl")
signals = {k: v for k, v in result.items() if k != "scan_result"}
print(signals["domain_present"], result["scan_result"]["http"]["status_code"])
```

### `run_t0_batch(leads: list[Lead | dict[str, Any]], concurrency: int = 5, max_retries: int = 2) -> list[dict[str, Any]]`

Skanuje liste leadow rownolegle przez `ThreadPoolExecutor`.

Parametry:

| Parametr | Typ | Opis |
|---|---|---|
| `leads` | `list[Lead | dict]` | Leady z `normalized_domain`, `domain` albo `input_domain`. |
| `concurrency` | `int` | Liczba workerow. Minimum efektywne: `1`. |
| `max_retries` | `int` | Obecnie zachowane w sygnaturze; runner ignoruje parametr. |

Zwraca liste rekordow `{lead_id, signals, scan_result}` w kolejnosci wejscia.

```python
from leadpipe.models import Lead
from leadpipe.t0 import run_t0_batch

lead = Lead(input_domain="example.pl", normalized_domain="example.pl")
batch = run_t0_batch([lead], concurrency=1)
print(batch[0]["signals"]["t0_confidence"])
```

### `scan_dns(domain: str) -> dict[str, Any]`

Modul: `leadpipe.t0.dns`.

Sprawdza A/AAAA przez `socket.getaddrinfo` oraz opcjonalnie MX/TXT przez `dnspython`, jesli biblioteka jest dostepna.

Zwraca m.in. `has_a_record`, `has_mx`, `has_txt`, `ips`, `error`.

```python
from leadpipe.t0.dns import scan_dns

print(scan_dns("example.pl")["has_a_record"])
```

### `scan_http(domain: str) -> dict[str, Any]`

Modul: `leadpipe.t0.http`.

Sprawdza HTTPS i HTTP, obsluguje przekierowania do limitu 10, wykrywa 429/503 jako bledy przejsciowe.

Zwraca `status_code`, `final_url`, `https_available`, `http_redirects_to_https`, `redirect_count`, `headers`, `transient_error`, `error`.

```python
from leadpipe.t0.http import scan_http

http = scan_http("example.pl")
print(http["final_url"], http["https_available"])
```

### `scan_ssl(domain: str) -> dict[str, Any]`

Modul: `leadpipe.t0.ssl`.

Nawiazuje polaczenie TLS na porcie 443, pobiera certyfikat, liczy dni do wygasniecia i wykrywa bledy SSL.

Zwraca `valid`, `expires_days`, `issuer`, `hostname_match`, `https_missing`, `cert_expired`, `ssl_invalid`, `error`.

```python
from leadpipe.t0.ssl import scan_ssl

cert = scan_ssl("example.pl")
print(cert["valid"], cert["expires_days"])
```

### `scan_html(html_text: str) -> dict[str, Any]`

Modul: `leadpipe.t0.html`.

Parsuje HTML przez BeautifulSoup i wyciaga podstawy dla T0: viewport, title/OG, formularze POST, CTA, ukryty kontakt i rozmiar HTML.

```python
from leadpipe.t0.html import scan_html

html = "<html><head><meta name='viewport'></head><body><a>Kontakt</a></body></html>"
print(scan_html(html)["cta_keywords_found"])
```

### `detect_tech(html_text: str, headers: dict[str, Any]) -> dict[str, Any]`

Modul: `leadpipe.t0.tech`.

Wykrywa WordPress, Joomla/Drupal, GTM, Meta Pixel, stare assety oraz serwer z naglowkow.

```python
from leadpipe.t0.tech import detect_tech

print(detect_tech("<script src='/wp-content/app.js'></script>", {})["wordpress"])
```

### `scan_performance(url: str) -> dict[str, Any]`

Modul: `leadpipe.t0.performance`.

Mierzy TTFB, pobiera do ok. 500 KB odpowiedzi i sprawdza gzip oraz naglowki cache.

```python
from leadpipe.t0.performance import scan_performance

perf = scan_performance("https://example.pl")
print(perf["ttfb_ms"], perf["gzip_enabled"])
```

### `normalize_host(value: str) -> str`

Modul: `leadpipe.t0.url`.

Normalizuje host: usuwa scheme, `www.`, slash i odrzuca niepoprawne znaki.

### `is_http_url(value: object) -> bool`

Modul: `leadpipe.t0.url`.

Sprawdza, czy wartosc jest poprawnym URL-em `http://` albo `https://`.

## T0.5: `leadpipe.t0_5`

### `run_t0_5(lead: Lead | dict[str, Any], html_text: str = "", *, nip_lookup: Any | None = None, vat_lookup: Any | None = None, cache: EnrichmentCache | None = None) -> dict[str, Any]`

Laczy enrichment NIP i VAT, aktualizuje payload leada i zwraca sygnaly biznesowe.

Parametry:

| Parametr | Typ | Opis |
|---|---|---|
| `lead` | `Lead | dict` | Lead z importu albo model Pydantic. |
| `html_text` | `str` | HTML z T0 do wyszukania NIP. |
| `nip_lookup` | `Any | None` | Opcjonalny mock/hook lookupu NIP dla testow lub integracji. |
| `vat_lookup` | `Any | None` | Opcjonalny mock/hook Bialej Listy VAT. |
| `cache` | `EnrichmentCache | None` | Cache po identyfikatorze leada i hashu HTML. |

Zwraca `{lead, enrichment, signals}`.

```python
from leadpipe.models import Lead
from leadpipe.t0_5 import run_t0_5

lead = Lead(input_domain="example.pl", normalized_domain="example.pl", nip="1234563218")
result = run_t0_5(lead, vat_lookup=lambda nip: {"vat_status": "czynny"})
print(result["signals"]["vat_active"])
```

### `EnrichmentCache(path: str | Path | None = None, ttl_seconds: int = 2592000)`

Plikowy lub pamieciowy cache enrichmentu.

Metody publiczne:

| Metoda | Opis |
|---|---|
| `get(key: str) -> dict[str, Any] | None` | Zwraca wartosc, jesli istnieje i nie wygasla. |
| `set(key: str, value: dict[str, Any]) -> None` | Zapisuje wartosc i opcjonalnie synchronizuje plik. |

```python
from leadpipe.t0_5 import EnrichmentCache

cache = EnrichmentCache("/tmp/leadpipe-cache.json")
cache.set("k", {"ok": True})
print(cache.get("k"))
```

### Funkcje NIP i VAT

Moduly: `leadpipe.t0_5.enrich_nip`, `leadpipe.t0_5.enrich_vat`.

| Funkcja | Sygnatura | Zwraca |
|---|---|---|
| `normalize_nip` | `normalize_nip(value: object) -> str | None` | Same cyfry albo `None`. |
| `is_valid_nip` | `is_valid_nip(value: object) -> bool` | Poprawnosc checksum NIP. |
| `extract_nips` | `extract_nips(text: str) -> list[str]` | Unikalne poprawne NIP-y z tekstu. |
| `lookup_gus_regon` | `lookup_gus_regon(nip: str, *, base_url: str = ...) -> dict[str, Any]` | Best-effort raw lookup. |
| `enrich_nip` | `enrich_nip(lead, html_text: str = "", lookup: Any | None = None) -> dict[str, Any]` | NIP i dane lookupu. |
| `validate_vat_number` | `validate_vat_number(value: object) -> bool` | Walidacja PL VAT/NIP. |
| `lookup_vat_status` | `lookup_vat_status(nip: str, *, at_date: date | None = None) -> dict[str, Any]` | Dane z Bialej Listy VAT. |
| `enrich_vat` | `enrich_vat(nip: str | None, lookup: Any | None = None) -> dict[str, Any]` | `vat_valid`, `vat_status`, opcjonalnie REGON/KRS/nazwa/adres. |

## T1: `leadpipe.t1`

### `run_t1(html_text: str, headers: dict[str, str] | None = None) -> dict[str, Any]`

Uruchamia parsery JSON-LD, kontaktu, formularzy, CTA i branzy. Zwraca sekcje parserow oraz `signals` dla engine.

```python
from leadpipe.t1 import run_t1

html = "<a href='mailto:biuro@example.pl'>Kontakt</a><button>Wyślij zapytanie</button>"
result = run_t1(html)
print(result["signals"]["has_email"], result["signals"]["contactability"])
```

### `extract_jsonld(html_text: str) -> dict[str, Any]`

Modul: `leadpipe.t1.jsonld`.

Zwraca `items` i pierwszy rozpoznany `organization`.

### `extract_contacts(html_text: str) -> dict[str, Any]`

Modul: `leadpipe.t1.contact`.

Wykrywa e-maile, telefony, linki social i liczy `contactability` do 100.

### `analyze_forms(html_text: str) -> dict[str, Any]`

Modul: `leadpipe.t1.forms`.

Zwraca `form_present`, `form_missing`, liste formularzy i `contact_form_present`.

### `analyze_ctas(html_text: str) -> dict[str, Any]`

Modul: `leadpipe.t1.cta`.

Zwraca liste CTA, `cta_count`, `cta_missing`, `weak_cta`.

### `classify_industry(text_or_html: str) -> dict[str, Any]`

Modul: `leadpipe.t1.industry`.

Klasyfikuje prosto po slowach kluczowych: `industrial`, `services`, `medical`, `digital` albo `unknown`. Dla digital ustawia `competitor=True`.

## Engine: `leadpipe.engine`

### `DecisionEngine(rules_dir: str | Path | None = None)`

Laduje wszystkie `*.yml` z `rules_dir` albo domyslnie z `leadpipe/rules/`, waliduje je modelami Pydantic i sortuje reguly po `(priority, key)`.

```python
from leadpipe.engine import DecisionEngine

engine = DecisionEngine()
print(engine.ruleset_version)
```

### `evaluate(lead: Lead | dict[str, Any], signals: dict[str, Any] | None = None) -> tuple[CampaignDecision, DecisionTrace]`

Buduje context z leada i sygnalow, ocenia reguly do pierwszego matcha, zwraca decyzje kampanijna oraz audytowalny trace.

```python
from leadpipe.engine import DecisionEngine
from leadpipe.models import Lead

lead = Lead(input_domain="example.pl", normalized_domain="example.pl", contact_email="biuro@example.pl")
signals = {
    "domain_present": True,
    "contactability": 80,
    "industry_fit": 70,
    "lead_value": 65,
    "cta_missing": True,
    "form_missing": True,
    "campaign_confidence": 0.8,
    "evidence_count": 2,
}
decision, trace = DecisionEngine().evaluate(lead, signals)
print(decision.action, decision.campaign, trace.winning_rule)
```

### Modele rulesetu

| Model | Pola |
|---|---|
| `Condition` | `signal`, `operator`, `value`, `weight` |
| `Rule` | `key`, `priority`, `conditions`, `combine`, `threshold`, `decision`, `campaign`, `confidence_threshold`, `min_evidence`, `subject`, `description` |
| `RuleFile` | `version`, `rules` |
| `RuleMatch` | `rule`, `score` |

Operatory warunkow: `exists`, `missing`, `eq`, `neq`, `in`, `contains`, `gte`, `gt`, `lte`, `lt`.

Tryby laczenia: `and`, `or`, `weighted`.

## Ruleset: `leadpipe.ruleset`

### `CURRENT_RULESET_VERSION: str`

Wersja bazowa w kodzie: `ruleset-2026-05-23-v1`. `DecisionEngine` uzywa najwyzszej wersji z plikow YAML, jesli sa zaladowane.

### `RulesetVersion`

Pydantic model z polami:

| Pole | Typ |
|---|---|
| `name` | `str` |
| `date` | `date` |
| `changes` | `list[str]` |

Wlasciwosc `audit_hash` zwraca SHA-256 z nazwy, daty i listy zmian.

### `load_current_ruleset_version() -> RulesetVersion`

Zwraca opis aktualnej wersji rulesetu w kodzie.

## Modele Pydantic: `leadpipe.models`

Wszystkie glowne modele dziedzicza po `StrictModel`, ktory ustawia `extra="forbid"`, walidacje assignmentu i serializacje enumow jako wartosci.

### Enumy

| Enum | Wartosci |
|---|---|
| `LeadStatus` | `new`, `scanned`, `decided`, `exported`, `suppressed`, `skipped` |
| `ScanStatus` | `ok`, `partial`, `failed`, `skipped` |
| `SignalSource` | `import`, `t0`, `t0_5`, `t1`, `t2`, `feedback` |
| `EvidenceType` | `http`, `dns`, `tls`, `html`, `contact`, `business`, `visual`, `feedback`, `manual` |
| `DecisionAction` | `skip`, `retry`, `manual_review`, `t2_required`, `t2_optional`, `send` |
| `CampaignKey` | `REDESIGN_OUTDATED`, `REDESIGN_ADS_WASTE`, `REDESIGN_CONVERSION`, `REDESIGN_TRUST`, `WORDPRESS_REWORK`, `MOBILE_REBUILD`, `TECH_REBUILD` |
| `OutreachEventType` | `sent`, `open`, `reply`, `positive_reply`, `meeting`, `soft_bounce`, `hard_bounce`, `opt_out`, `manual_reject` |
| `SuppressionScope` | `email`, `domain`, `nip`, `phone`, `lead`, `batch` |
| `BatchStatus` | `created`, `importing`, `ready`, `scanning`, `deciding`, `exported`, `failed` |

### Kluczowe schematy

#### `Lead`

Reprezentuje pojedynczy rekord firmy/domeny. Waliduje `nip` do 10 cyfr i normalizuje domeny do lowercase bez `www.`.

Najwazniejsze pola: `id`, `batch_id`, `input_domain`, `normalized_domain`, `registered_domain`, `url`, `company_name`, `nip`, `source`, `contact_email`, `phone`, `status`, `metadata`, `created_at`, `updated_at`.

```python
from leadpipe.models import Lead

lead = Lead(input_domain="https://www.Example.pl/", normalized_domain="www.Example.pl")
print(lead.normalized_domain)  # example.pl
```

#### `Signal`

Pojedynczy sygnal decyzyjny: `key`, `value`, `source`, `confidence`, `evidence_ids`, `observed_at`.

#### `Evidence`

Dowod audytowy: `type`, `key`, `value`, `source_url`, `confidence`, `captured_at`, `expires_at`, `metadata`.

#### `ScanResult`

Wynik warstwy skanu: `lead_id`, `status`, `layer`, `started_at`, `finished_at`, `http_status`, `final_url`, `signals`, `evidence`, `raw_snapshot_path`, `error`.

#### `ScoreBreakdown`

Pola scoringu: `evidence_strength`, `signal_confidence`, `contactability`, `industry_fit`, `lead_value`, `penalties`.

Wlasciwosc `campaign_score` liczy:

```text
0.45 * evidence_strength
+ 0.20 * signal_confidence
+ 0.15 * contactability
+ 0.15 * industry_fit
+ 0.05 * lead_value
- penalties
```

#### `DecisionTrace`

Audyt decyzji: `ruleset_version`, `evaluated_rules`, `winning_rule`, `blocked_by`, `score_breakdown`, `decision_reason`.

#### `CampaignDecision`

Decyzja koncowa: `action`, opcjonalna `campaign`, `subject`, `confidence`, `decision_reason`, `ruleset_version`, `rule_key`, `score_breakdown`, `metadata`.

Walidacja: `action="send"` wymaga niepustej kampanii.

#### `OutreachEvent`, `SuppressionEntry`, `Batch`, `ImportRecord`

Modele wspierajace feedback loop, suppression/cooldown, batch importu i walidacje rekordow wejscia.

## CSV: `leadpipe.csv_schemas`

### `parse_csv(path_or_text: str | Path, schema: type[T]) -> tuple[list[T], list[tuple[int, list[str]]]]`

Czyta CSV z pliku albo stringa i waliduje kazdy wiersz modelem Pydantic.

```python
from leadpipe.csv_schemas import ImportCsvSchema, parse_csv

records, errors = parse_csv("domain\nexample.pl\n", ImportCsvSchema)
```

### `dump_csv(records: Iterable[CsvModel]) -> str`

Serializuje liste modeli CSV do tekstu CSV.

Schematy:

| Schemat | Zastosowanie |
|---|---|
| `ImportCsvSchema` | Import leadow: `domain`, `url`, `company_name`, `nip`, `source`, `contact_email`, `notes`. |
| `ExportCsvSchema` | Eksport QA/outreach: firma, domena, email, telefon, kampania, subject, evidence, confidence, suppression. |
| `FeedbackCsvSchema` | Import feedbacku: `domain`, `email`, `event`, `timestamp`, `notes`. |

## DB: `leadpipe.db_schema`

Publiczne fabryki:

| Funkcja | Opis |
|---|---|
| `create_engine(database_url: str, **kwargs: Any) -> AsyncEngine` | Tworzy async engine SQLAlchemy. |
| `create_session_factory(engine: AsyncEngine) -> async_sessionmaker` | Tworzy async session factory z `expire_on_commit=False`. |

Mapowane tabele: `leads`, `batches`, `scan_results`, `decision_traces`, `campaign_decisions`, `outreach_events`, `suppression_entries`.

```python
from leadpipe.db_schema import create_engine, create_session_factory

engine = create_engine("postgresql+psycopg://user:pass@localhost/leadpipe")
Session = create_session_factory(engine)
```

## CLI: `leadpipe.cli`

### Komendy

```bash
leadpipe import FILE
leadpipe scan SELECTOR
leadpipe decide SELECTOR
leadpipe pipeline BATCH_SIZE [--file FILE]
```

`SELECTOR` to `batch` albo konkretne UUID leada.

### Flagi i zmienne

| Element | Opis |
|---|---|
| `--file FILE` | Dla `pipeline`: importuje CSV przed skanem. |
| `BATCH_SIZE` | Maksymalna liczba leadow przetworzonych przez `pipeline`. |
| `LEADPIPE_STATE` | Sciezka pliku stanu CLI; domyslnie `.leadpipe/state.json`. |

### Kody wyjscia

| Komenda | Kod | Znaczenie |
|---|---:|---|
| `import` | `0` | Import OK. |
| `import` | `2` | Bledy walidacji CSV. |
| `scan` | `0` | Scan zakonczony, nawet jesli `scanned=0`. |
| `decide` | `0` | Co najmniej jeden lead zdecydowany. |
| `decide` | `1` | Brak znalezionego leada. |
| `pipeline` | `0` | Pipeline OK. |
| `pipeline` | `2` | Bledy walidacji CSV. |
