# SPECYFIKACJA T0/T1/T2 — Pipeline Lead Scoring i Automatyzacji Outreachu

> **Data:** 2026-05-23
> **Autor:** B B / MeNET
> **Cel:** Kompleksowy opis obecnego stanu pipeline'a T0/T1/T2 dla Codex CLI do analizy krytycznej
> **Repozytorium kodu:** https://github.com/bozenaopala56-glitch/MeNET
> **Dane badawcze:** `/mnt/hermes-free/` na VM hermes-agent (10.186.0.2)

---

## Spis treści

1. [Kontekst biznesowy](#1-kontekst-biznesowy)
2. [Architektura ogólna](#2-architektura-ogólna)
3. [T0 — Sygnały techniczne](#3-t0--sygnały-techniczne)
4. [T1 — Analiza tekstu](#4-t1--analiza-tekstu)
5. [T2 — Vision](#5-t2--vision)
6. [Stan obecny — co jest zrobione, co nie](#6-stan-obecny--co-jest-zrobione-co-nie)
7. [Dane badawcze i artefakty](#7-dane-badawcze-i-artefakty)
8. [Pytania do Codex CLI](#8-pytania-do-codex-cli)

---

## 1. Kontekst biznesowy

### MeNET — Ekosystem Agencji Digitalowej

MeNET to grupa 10 usług digitalowych pod wspólnym szyldem:

| Usługa | Marka | Co robi |
|--------|-------|---------|
| Strony WWW | BRDesign | Kodowane strony firmowe (Astro, hand-coded, zero WordPress) |
| SEO | OctoSEO | Audyty SEO, pozycjonowanie, content marketing |
| Reklamy | AuraAds | Google Ads, Meta Ads, TikTok Ads |
| Design/Rework | Design/Rework | UI/UX redesign, branding, rebranding |
| Tłumaczenia | LingoTranslate | Wielojęzyczne strony, lokalizacja SEO |
| Bezpieczeństwo | CyberPakt | Audyty bezpieczeństwa, WAF, skanery |
| Hosting/Cloud | StratumCloud | Serwery, domeny, SSL, cloud |
| Utrzymanie | StayOnline | Monitoring, backup, aktualizacje CMS |
| Chatboty AI | BRDesign AI | Automatyzacja sprzedaży i supportu |
| Labs/Innowacje | NXT Factory | WebGL, GSAP, eksperymenty technologiczne |

**Model biznesowy:** Abonamentowy. Strony kodowane ręcznie (zero WordPress/szablonów). Brak e-commerce. Każda usługa to osobna marka z własną domeną.

**Rynek:** Polskie MŚP (małe i średnie przedsiębiorstwa), głównie usługowe i produkcyjne.

**Cel pipeline'a:** Automatyczne skanowanie polskich firm (leadów) → wykrywanie problemów technicznych/biznesowych → generowanie spersonalizowanego outreachu sprzedażowego → automatyzacja całego cyklu sprzedaży.

---

## 2. Architektura ogólna

### 3-warstwowy pipeline

```
                     ┌─────────────────────────────┐
                     │     LISTA LEADÓW (URL-e)     │
                     │  Skąd: domeny .pl, baza NIP, │
                     │  scraping, API, manual       │
                     └─────────────┬───────────────┘
                                   │
                                   ▼
                     ┌─────────────────────────────┐
                     │   T0 — SYGNAŁY TECHNICZNE   │
                     │   ~40-85 sygnałów binarnych  │
                     │   HTTP, SSL, DNS, WHOIS,     │
                     │   Shodan, HTML parse         │
                     │   ~4s/lead, $0               │
                     └─────────────┬───────────────┘
                                   │
                                   ▼
                     ┌─────────────────────────────┐
                     │   T1 — ANALIZA TEKSTU       │
                     │   JSON-LD, OG, meta, title, │
                     │   Biała Lista VAT (NIP)      │
                     │   $0, 0ms (dane już są)     │
                     └─────────────┬───────────────┘
                                   │
                                   ▼
                     ┌─────────────────────────────┐
                     │   T2 — VISION (AI)          │
                     │   2 prompty: BŁĘDY + WRAŻENIE│
                     │   Screenshot → Gemini Vision │
                     │   Koszt: ~$0.01/lead         │
                     └─────────────┬───────────────┘
                                   │
                                   ▼
                     ┌─────────────────────────────┐
                     │   SCORING / KAMPANIE         │
                     │   8 kampanii, 47 archetypów  │
                     │   Mapowanie na usługę MeNET  │
                     │   Generowanie spersonalizo-  │
                     │   wanego maila               │
                     └─────────────────────────────┘
```

### Założenia architektoniczne

- **Zero kosztów API** dla T0 i T1 (tylko darmowe źródła)
- **T2 z AI** tylko gdy T0+T1 nie wystarcza (wizualna ocena)
- **Offline-first** — wszystko może działać na jednej VM
- **Skalowanie** — 5000+ leadów na batch
- **Język:** Polski (rynek docelowy)
- **Dane przechowywane** w JSON + GCS (/mnt/hermes-free)

---

## 3. T0 — Sygnały techniczne

### Status: ✅ RESEARCH ZROBIONY, ❌ KOD NIE WDROŻONY

### Co robi T0

Skanuje domenę/URL i zbiera **40-85 binarnych sygnałów** w ~4 sekundy, za $0 (tylko darmowe API):

| Kategoria | Sygnały (przykłady) |
|-----------|-------------------|
| **HTTP Status** | code, redirects, headers, server type |
| **SSL/TLS** | cert validity, issuer, protocol version |
| **DNS** | A/AAAA/MX/TXT/SPF records, nameservers |
| **WHOIS** | registrant, creation/expiration dates |
| **HTML** | title, meta description, viewport, charset |
| **SEO** | robots.txt, sitemap.xml, hreflang, canonical |
| **Security** | HSTS, CSP, X-Frame-Options, CORS |
| **Performance** | response time, page size, compression |
| **Tech Stack** | CMS detection, framework, analytics, CDN |
| **Email** | SPF, DKIM (detectable via DNS), DMARC |
| **Social** | OG tags, social media links, schema.org |
| **Mobile** | viewport, media queries, responsive meta |

### Zredukowany zestaw core'owy: 12 tagów

Po analizie 4529 leadów, zidentyfikowano **12 core tagów** które niosą 95% informacji:

| # | Tag | % leadów | Co oznacza |
|---|-----|----------|------------|
| 1 | `status:active` | 84.5% | Strona działa (default) |
| 2 | `status:inactive` | 9.1% | Strona martwa, jest DNS |
| 3 | `status:error` | 6.9% | Strona zwraca błąd HTTP |
| 4 | `status:unknown` | 6.4% | Nie udało się ustalić statusu |
| 5 | `ssl:no` | 16.6% | Brak HTTPS (security gap) |
| 6 | `speed:slow` | 22.3% | >2000ms (performance problem) |
| 7 | `speed:none` | 15.5% | Brak odpowiedzi HTTP |
| 8 | `dns:minimal` | 6.5% | Tylko A+MX, brak TXT/SPF |
| 9 | `dns:none` | 6.4% | Brak rekordów DNS |
| 10 | `infra:modern` | 5.2% | IPv6 + multi-IP (CDN/cloud) |
| 11 | `whois:no` | 50.4% | Brak danych WHOIS |
| 12 | `crisis:yes` | 8.2% | ≥3 problemów jednocześnie |

**Wszystkie pozostałe sygnały (28+) są inferowalne z tych 12.** Redundancja wykryta przez implication lattice (conf ≥95%).

### 47 Archetypów leadów

Z 12 core tagów wyłoniono **47 naturalnych archetypów** (unikalnych kombinacji tagów). Top 4 pokrywają **75.6% leadów**:

| Archetyp | Core Tags | % | Co oznacza |
|----------|-----------|-----|------------|
| A001 | `status:active, whois:no` | 29.3% | Aktywna strona, brak WHOIS (anonimowy rejestrator) |
| A002 | `status:active` | 25.5% | Czysta, aktywna strona |
| A003 | `speed:slow, status:active` | 13.1% | Wolna strona |
| A004 | `speed:slow, status:active, whois:no` | 7.6% | Wolna + anonimowy rejestrator |

### 8 Kampanii (mapowanie archetypów → akcje)

| Kampania | Trigger (core tags) | Priorytet | Subiekt maila |
|----------|---------------------|-----------|--------------|
| **RESCUE** | `status:inactive` lub `status:error` | 1 | "Twoja strona nie działa — szybka diagnoza" |
| **CRISIS_AUDIT** | `crisis:yes` | 1 | "5 problemów na Twojej stronie — darmowy audyt" |
| **SECURITY_SSL** | `status:active` + `ssl:no` | 2 | "Brak HTTPS ostrzega klientów — poprawmy to" |
| **PERFORMANCE** | `speed:slow` | 2 | "Strona wolna? Sprawdźmy dlaczego" |
| **DNS_SETUP** | `dns:none` | 2 | "Brakuje rekordów DNS — e-mail może nie dochodzić" |
| **PROFESSIONAL_EMAIL** | `dns:minimal` | 3 | "Profesjonalna konfiguracja e-mail i SPF" |
| **MODERNIZE** | `status:active` + brak `infra:modern` | 3-4 | "Czas na nowoczesną infrastrukturę" |
| **UPSELL_PREMIUM** | brak wszystkich problemowych | 5 | "Twoja strona działa dobrze — a może jeszcze lepiej?" |
| **WHOIS_RECOVERY** | `whois:no` + `status:active` | 4 | "Uzupełnij dane firmy w rejestrze" |

### Problemy T0 (znane):

1. **Brak kodu produkcyjnego** — pipeline istnieje tylko jako skrypty researchowe
2. **Brak automatyzacji** — skanowanie leadów trzeba uruchamiać ręcznie
3. **Brak kolejki** — brak BullMQ/Redis do zarządzania skanowaniem
4. **Brak cache** — każde skanowanie od zera
5. **Brak API endpointu** — nie można zintegrować z innymi systemami
6. **Shodan API klucz** — nie wdrożony, choć zbadany
7. **Sygnały security** (<2% leadów) — zbyt rzadkie by mieć sens w masowym skanowaniu

---

## 4. T1 — Analiza tekstu

### Status: ✅ KONCEPCJA, ❌ KOD NIE ISTNIEJE

### Cel

T1 wypełnia lukę między T0 (sygnały techniczne) a T2 (vision). Analizuje HTML który T0 już ściągnął — $0, 0ms (żadnych dodatkowych API calli oprócz Białej Listy VAT).

### Źródła danych

| Źródło | Co daje | Pewność |
|--------|---------|---------|
| JSON-LD (Schema.org) | opis + usługi + zasięg firmy | 100% |
| OG:description | opis firmy | 70% |
| Meta description | opis firmy | 60% |
| Title tag | nazwa + opis | 50% |
| Biała Lista VAT (jeśli NIP w HTML) | oficjalna nazwa + status + REGON + KRS + adres | 100% |

### Co T1 daje

- **"co_firma_robi"** — kontekst biznesowy leada
- **Nazwa firmy** — z tytułu, OG, lub VAT
- **Branża** — z JSON-LD @type + PKD z VAT
- **Lokalizacja** — adres z VAT + geo meta
- **Zasięg** — lokalny/krajowy/międzynarodowy

### Zaplanowane źródła (niezaimplementowane)

- CEIDG API (klucz wymagany — nie mamy)
- KRS API (darmowe, ale endpoint nieodkryty)

### Problemy T1:

1. **Kod nie istnieje** — tylko koncepcja w `RAPORT-FINAL-T0-REDUKCJA-T1T2-GAP.md`
2. **Moduł `text_analysis.py`** — wspomniany w architekturze, ale nie znaleziony w repo
3. **CEIDG i KRS** — API istnieją ale nie są zintegrowane
4. **NIP detection** — regex na NIP w HTML, ale niesprawdzony w praktyce
5. **Brak testów** na realnych danych (czy NIP faktycznie występuje w HTML polskich firm?)

---

## 5. T2 — Vision

### Status: ✅ KONCEPCJA, ❌ KOD NIE ISTNIEJE

### Cel

T2 używa AI (Gemini Vision / LLM vision) do wizualnej oceny strony — rzeczy których T0 ani T1 nie są w stanie wykryć.

### 2 prompty

| Prompt | Co daje | Zastosowanie |
|--------|---------|-------------|
| **BŁĘDY** | Wizualne błędy: kontrast, kolory, stock zdjęcia, nieczytelność | HAK do maila |
| **WRAŻENIE** | Feeling, trust, profesjonalizm, nowoczesność | Ton kampanii |

### Co T2 mogłoby wykrywać (z gap analysis)

- Jakość designu (czy strona wygląda profesjonalnie)
- Mobile experience (wizualnie)
- Call-to-action (czy są przyciski, formularze)
- Social proof (logotypy, gwiazdki, referencje)
- Wiek strony (przestarzałe grafiki)
- Branżowe wzorce wizualne

### Problemy T2:

1. **Koszt** — każde zapytanie do Gemini Vision to pieniądze (~$0.01/lead)
2. **Kod nie istnieje** — tylko koncepcja
3. **Nieprzetestowane** — czy Gemini dobrze ocenia polskie strony?
4. **Latency** — vision API to 2-5 sekund per prompt
5. **2 prompty to minimum** — ale czy wystarczy? (gap analysis wskazuje 10 wymiarów)
6. **Brak pipeline'u** — jak łączyć wyniki T2 z T0+T1?

---

## 6. Stan obecny — co jest zrobione, co nie

### ✅ ZROBIONE (Research + analiza)

| Element | Pliki |
|---------|-------|
| 86 darmowych sygnałów T0 | `/mnt/hermes-free/WINNET-86-SYGNALOW-FREE.html` |
| 12 core tagów (redukcja z 28) | `RAPORT-FINAL-T0-REDUKCJA-T1T2-GAP.md` |
| 47 archetypów leadów | `T0-ARCHETYPE-SUMMARY.json` |
| 8 kampanii + subject lines | `T0-FINAL-ARTIFACT.json` |
| 255 reguł asocjacyjnych (FP-Growth) | `RAPORT-KORELACJE-LIFT-600.md` |
| 12 klastrów HDBSCAN | `RAPORT-DEEP-RESEARCH-600.md` |
| Sieć korelacji (Louvain) | `RAPORT-COMMUNITIES-LOUVAIN-600.md` |
| Analiza informacyjna (entropia, CMI) | `WINNET-INFO-THEORY/` |
| T1/T2 Gap Analysis (10 wymiarów) | `T1-T2-GAP-ANALYSIS.json` |
| Pełny scoring 4529 leadów | `V3-LEADS-4598-T0-SIGNALS.json` |

### ❌ NIE ZROBIONE (Kod)

| Element | Status |
|---------|--------|
| T0 skaner (produkcyjny) | ❌ |
| T1 moduł text_analysis.py | ❌ |
| T2 vision pipeline | ❌ |
| Kolejka skanowania (BullMQ/Redis) | ❌ |
| API endpoint dla pipeline'u | ❌ |
| Baza danych leadów (SQLite/Postgres) | ❌ |
| Dashboard/widok wyników | ❌ |
| Automatyczny scoring leadów | ❌ |
| Generowanie maili | ❌ |
| Integracja z CRM | ❌ |
| Testy na realnych danych (T1, T2) | ❌ |

---

## 7. Dane badawcze i artefakty

Wszystkie pliki w `/mnt/hermes-free/`:

### Kluczowe raporty

| Plik | Rozmiar | Co zawiera |
|------|---------|------------|
| `T0-T1-T2-ARCHITEKTURA.md` | 1.4 KB | Ostateczna architektura 3 warstw |
| `RAPORT-FINAL-T0-REDUKCJA-T1T2-GAP.md` | 7 KB | 12 core tagów, 47 archetypów, 8 kampanii, 10 luk T1/T2 |
| `FULL-SIGNAL-INVENTORY.md` | 13 KB | Pełny inwentarz 86 sygnałów |
| `T0-ENGINE-V3-RESULTS.json` | 5.3 MB | 4529 leadów z pełnym T0 scoringiem |
| `T0-FINAL-ARTIFACT.json` | 4.5 MB | Finalny artifact z archetypami i kampaniami |
| `T0-ARCHETYPE-SUMMARY.json` | 18 KB | 47 archetypów z mappingiem |
| `T1-T2-GAP-ANALYSIS.json` | 4.6 KB | 10 wymiarów poza T0 |
| `RAPORT-DEEP-RESEARCH-600.md` | 13 KB | MCA + HDBSCAN + NetworkX na 610 leadach |
| `RAPORT-KORELACJE-LIFT-600.md` | — | 255 reguł FP-Growth z lift ≥ 2.0 |
| `RAPORT-COMMUNITIES-LOUVAIN-600.md` | — | 3 główne community (Protected, Dead, Cloud/CDN) |
| `PLAN-10-ITERACJI-WINNET-v2-FINAL.md` | 13 KB | Plan 10 iteracji rozwoju |
| `SPECYFIKACJA-WINNET-ANALYZER.md` | 13 KB | Specyfikacja TUI Analyzera |
| `WINNET-86-SYGNALOW-FREE.html` | — | Wizualny kompendium 86 sygnałów |

### Zbiory danych

| Plik | Rozmiar | Zawiera |
|------|---------|---------|
| `ALL-610-SIGNAL-DATA.json` | 968 KB | 610 leadów z pełnymi sygnałami |
| `V3-LEADS-4598-T0-SIGNALS.json` | 4.7 MB | 4598 leadów z T0 scoringiem |
| `T0-FINAL-ARTIFACT.json` | 4.5 MB | Finalny artifact z kampaniami |
| `WINNET-MASTER-DATASET-600.json` | 1.2 MB | Master dataset 600 leadów |
| `WINNET-SCORING-V1-RESULTS.json` | 1.9 MB | Scoring v1 wyników |

### Algorytmy użyte w researchu

- FP-Growth (association rules, min support 2%, lift ≥ 2.0)
- HDBSCAN (Hamming distance, min_cluster_size=30)
- MCA (Multiple Correspondence Analysis)
- Louvain (community detection)
- t-SNE / UMAP (dimensionality reduction)
- NetworkX centrality (degree, betweenness, eigenvector)
- Conviction / Lift / Leverage metrics
- Entropy / Conditional Mutual Information
- SBA (Scoring Based on Associations — Liu et al. formula)

---

## 8. Pytania do Codex CLI

### Do krytyki i analizy:

1. **Czy architektura T0→T1→T2 ma sens?**
   - Czy kolejność warstw jest optymalna?
   - Czy T1 i T2 powinny być połączone?
   - Czy brakuje warstwy (np. T0.5 dla danych biznesowych)?

2. **Czy 12 core tagów to wystarczająca reprezentacja?**
   - Czy redukcja z 28 do 12 nie straciła istotnych informacji?
   - Czy implication lattice jest poprawny?
   - Czy brakuje tagów które mogłyby być użyteczne?

3. **Czy 8 kampanii to optymalny zestaw?**
   - Czy cannibalization (nakładanie się) jest problemem?
   - Czy priorytety są poprawne?
   - Czy subject lines są skuteczne?

4. **Jak powinien wyglądać produkcyjny pipeline?**
   - Jaka technologia/biblioteki do skanowania?
   - Jak zarządzać kolejką leadów?
   - Gdzie przechowywać wyniki?
   - Jak często skanować (refresh rate)?

5. **Czy T2 (vision) w ogóle ma sens ekonomiczny?**
   - Koszt ~$0.01/lead vs wartość dodana
   - Czy da się zastąpić tańszymi sygnałami?
   - Jaki ROI z wizualnej analizy?

6. **Jakie są alternatywy dla obecnej architektury?**
   - LLM-first (zamiast T0+T1+T2, jeden prompt do Gemini)?
   - ML klasyfikator (zamiast ręcznych progów)?
   - Gotowe rozwiązania (OpenReplay, Hotjar insights)?

7. **Co robić z 28 anomaliami HDBSCAN?**
   - To błędy danych czy unikalne wysokowartościowe leady?
   - Jak je analizować i wykorzystać?

8. **Czy pipeline powinien być rozszerzalny?**
   - Jak dodawać nowe sygnały?
   - Jak dodawać nowe kampanie?
   - Jak integrować z CRM (np. HubSpot)?

### Format odpowiedzi:

```
## [Numer pytania]: [Krótka odpowiedź]

**Analiza:**
- Szczegółowa analiza problemu
- Dowody/argumenty

**Rekomendacja:**
- Co zmienić/będzie tak jak jest
- Priorytet: HIGH / MEDIUM / LOW
- Szacowany wysiłek

**Alternatywy:**
- Opcja A: ...
- Opcja B: ...
- Opcja C: ...

**Ryzyka:**
- Co może pójść nie tak
- Jak minimalizować
```
