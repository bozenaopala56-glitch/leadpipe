T0 SCANNER — NOWY, od zera

Co robi
Bierze listę leadów (z domenami), skanuje każdą domenę i produkuje sygnały dla YAML DecisionEngine.

Sygnały które YAML potrzebuje (z campaigns.yml + gates.yml):

| Kategoria | Sygnał | Jak wykryć |
|-----------|--------|-----------|
| HTTP | `domain_present` | DNS resolves + HTTP response |
| HTTP | `scan_failed_final` | Timeout/refused po retry |
| HTTP | `transient_scan_error` | 429/503/connection reset |
| SSL | `https_missing` | HTTP 200 ale brak redirect na HTTPS |
| SSL | `ssl_invalid` | Cert self-signed/expired/nazwa nie match |
| SSL | `cert_expired` | Date check na cert |
| HTML | `viewport_missing` | `<meta name="viewport">` absent |
| HTML | `company_identity_missing` | Brak firmy w title/OG |
| HTML | `form_present` / `form_missing` | `<form>` z method=post |
| HTML | `cta_missing` / `weak_cta` | Brak buttonów "kontakt/zadzwoń/wyślij" |
| HTML | `contact_hidden` | Kontakt tylko w JS lub requires click |
| HTML | `html_too_large` | > 500KB HTML |
| Tech | `wordpress_detected` | `/wp-content/`, `/wp-json/`, `generator` meta |
| Tech | `cms_detected` | Inny CMS (Joomla/Drupal) |
| Tech | `old_assets` | Daty w CSS/JS starsze niż 3 lata |
| Tech | `gtm_detected` | `googletagmanager.com` w HTML |
| Tech | `meta_pixel_detected` | `connect.facebook.net` lub `fbq(` |
| Mobile | `not_mobile_friendly` | Brak viewport + media queries |
| Perf | `speed_slow` | TTFB > 2000ms |
| Perf | `compression_missing` | Brak Content-Encoding: gzip |
| Perf | `cache_missing` | Brak Cache-Control/Expires |


Pliki które Codex pisze:

leadpipe/t0/
+¦¦ __init__.py
+¦¦ http.py        # HTTP status, redirects, headers
+¦¦ dns.py         # DNS resolution
+¦¦ ssl.py         # Cert check
+¦¦ html.py        # HTML parse: meta, viewport, forms
+¦¦ tech.py        # CMS, GTM, Pixel detection
+¦¦ performance.py # TTFB, size, compression
+¦¦ signals.py     # Łączy wszystkie moduły › dict sygnałów
L¦¦ runner.py      # Skanuje listę leadów, zapisuje wyniki


http.py — skan HTTP

Python

def scan_http(domain: str) -> dict:
    """Sprawdza HTTP/HTTPS, redirects, status code.
    Zwraca: {status_code, final_url, https_available, redirect_count, headers}
    Obsługa: timeout 10s, retry 2x, 429 backoff
    """


dns.py — DNS

Python

def scan_dns(domain: str) -> dict:
    """A/AAAA/MX/TXT records.
    Zwraca: {has_a_record, has_mx, has_txt, ips: []}
    Używa socket.getaddrinfo + dns.resolver jeśli dostępny
    """


ssl.py — certyfikat

Python

def scan_ssl(domain: str) -> dict:
    """Połączenie TLS, pobiera cert.
    Zwraca: {valid, expires_days, issuer, hostname_match}
    Obsługa: timeout 5s, brak HTTPS › {valid: false, https_missing: true}
    """


html.py — parsowanie HTML

Python

def scan_html(html_text: str) -> dict:
    """Parsuje HTML, wyciąga meta, viewport, formularze, CTA.
    Zwraca: {viewport_present, company_in_title, form_present,
             cta_keywords_found: [...], contact_hidden, html_size}
    Używa html.parser lub BeautifulSoup
    """


tech.py — detekcja technologii

Python

def detect_tech(html_text: str, headers: dict) -> dict:
    """Wykrywa WordPress, GTM, Meta Pixel, inny CMS.
    Zwraca: {wordpress, gtm, meta_pixel, cms_type, old_assets}
    """


performance.py — wydajność

Python

def scan_performance(url: str) -> dict:
    """Mierzy TTFB, rozmiar, kompresję.
    Zwraca: {ttfb_ms, page_size_bytes, gzip_enabled, cache_headers}
    """


signals.py — agregacja

Python

def compute_t0_signals(domain: str) -> dict:
    """Uruchamia wszystkie moduły, scala wyniki.
    Zwraca dict gotowy do wstrzyknięcia do DecisionEngine.evaluate(signals)
    """
	
	Python

def run_t0_batch(leads: list[Lead], concurrency: int = 5, max_retries: int = 2) -> list[dict]:
    """Skanuje batch leadów z concurrency.
    Zwraca listę {lead_id, signals, scan_result} per lead
    """


Zależności do pyproject.toml:

toml

dependencies = [
  "beautifulsoup4>=4.12",
  "lxml>=5.0",
]


Czego NIE robić (bo już istnieje w starym systemie i nie potrzebujemy duplikować):
- NIE adapter do starych wyników T0
- NIE czytanie index.jsonl
- NIE czytanie vision_reports
- NIE czytanie outbox.jsonl

Co z T1 parserami, T0.5, T2?

T0 scanner to fundament. Bez niego DecisionEngine nie ma sygnałów. Dalej:

| Kolejność | Co | Zależność |
|-----------|-----|-----------|
| **1** | T0 scanner (http/dns/ssl/html/tech/performance) | — |
| **2** | T0.5 enrichment (NIP + VAT + cache) | T0 (HTML już pobrany) |
| **3** | T1 parsery (JSON-LD, contact, forms, CTA, industry) | T0 (HTML już pobrany) |
| **4** | CLI (import + scan + decide) | T0 + T1 + engine |

