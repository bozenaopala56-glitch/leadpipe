# REGULY-FINAL: T0/T0.5/T1/T2 Lead Scoring Pipeline

Data: 2026-05-23  
Ruleset: `ruleset-2026-05-23-www-final-v1`  
Cel: kwalifikowac firmy, ktore maja strone i potrzebuja lepszej.

## 1. Zasady nadrzedne

- Pipeline nie celuje w firmy bez strony. Brak strony, parking, social-only albo finalny scan failed daje `skip`, `retry` albo `manual_review`, ale nie kampanie wysylkowa.
- Kampanie sa zawsze WWW-first. SSL, mobile, performance, WordPress, reklamy i CTA sa dowodami przebudowy strony.
- `send` oznacza gotowosc do QA i eksportu, nie automatyczna wysylke.
- Kazda decyzja ma `ruleset_version`, `rule_key`, `winning_rule`, `blocked_by`, `score_breakdown`, `evidence_ids`, `confidence` i `decision_reason`.
- T2 uruchamia sie tylko wtedy, gdy screenshot moze zmienic decyzje lub confidence.

## 2. Decyzje

| Decyzja | Znaczenie |
|---|---|
| `send` | kampania ma progi, dowody i moze isc do QA/CSV |
| `manual_review` | czlowiek musi sprawdzic lead, kampanie albo dowody |
| `t2_required` | bez screenshotow nie da sie bezpiecznie rozstrzygnac |
| `t2_optional` | T2 moze poprawic personalizacje, ale nie blokuje QA |
| `retry` | blad przejsciowy T0/T2 |
| `skip` | compliance, niski fit, brak kontaktu, brak strony albo brak uczciwego hooka |

## 3. Finalne kampanie

| Priorytet | Kampania | Kiedy |
|---:|---|---|
| 1 | `REDESIGN_ADS_WASTE` | firma placi za ruch lub ma tracking, a strona marnuje ruch |
| 2 | `REDESIGN_OUTDATED` | strona jest stara, bez RWD albo wizualnie przestarzala |
| 3 | `REDESIGN_CONVERSION` | strona jest, ale nie prowadzi do zapytania |
| 4 | `REDESIGN_TRUST` | brak SSL, slaby trust albo nieprofesjonalny odbior |
| 5 | `WORDPRESS_REWORK` | WordPress/CMS wymaga przebudowy na custom kod |
| 6 | `MOBILE_REBUILD` | strona nie dziala poprawnie na telefonie |
| 7 | `TECH_REBUILD` | strona dziala, ale technicznie jest do wymiany |

### `REDESIGN_ADS_WASTE`

Wymaga sygnalu ruchu platnego lub trackingowego: `gtm_detected`, `ga_detected`, `meta_pixel_detected`, `utm_or_landing_hint`. Musi miec dodatkowy problem strony: `speed_slow`, `weak_cta`, `form_missing`, `low_trust` albo `not_mobile_friendly`.

Prog: confidence >=0.80, evidence >=3.  
T2: wymagane, gdy problemem jest tylko wyglad, CTA albo mobile.  
Subject: `Czy strona {domena} wykorzystuje ruch z reklam?`

### `REDESIGN_OUTDATED`

Wymaga aktywnej strony i dowodow: `visual_outdated`, `viewport_missing`, `legacy_html`, `table_layout`, `old_charset`, `media_queries_missing` albo `not_mobile_friendly`.

Prog: confidence >=0.76, evidence >=2.  
T2: wymagane dla claimu stricte wizualnego, opcjonalne przy twardym braku RWD/legacy HTML.  
Subject: `Pierwsze wrazenie na stronie {domena}`

### `REDESIGN_CONVERSION`

Wymaga aktywnej strony i oferty, ale slabego przejscia do kontaktu: `cta_missing`, `weak_cta`, `form_missing`, `contact_hidden`, `thin_offer_structure`, `speed_slow`.

Prog: confidence >=0.74, evidence >=2.  
T2: wymagane, gdy claim dotyczy widocznosci CTA above the fold.  
Subject: `Zapytania ze strony {firma}`

### `REDESIGN_TRUST`

Wymaga problemu z zaufaniem: `https_missing`, `ssl_invalid`, `cert_expired`, `hostname_mismatch`, `low_trust`, `company_identity_missing`, `privacy_missing`, formularz bez poprawnego HTTPS.

Prog: confidence >=0.76, evidence >=2.  
T2: wymagane, gdy nie ma twardego SSL/certyfikatu i claim opiera sie na odbiorze wizualnym.  
Subject: `Zaufanie klienta na {domena}`

### `WORDPRESS_REWORK`

Wymaga `wordpress_detected` albo `cms_detected` oraz problemu: `wordpress_poor_template`, `plugin_risk_hint`, `old_assets`, `speed_slow`, `weak_cta`, `visual_outdated`.

Prog: confidence >=0.74, evidence >=2.  
T2: wymagane dla claimu "szablonowo/slabo wyglada".  
Subject: `Odswiezenie strony {domena} bez WordPressa`

### `MOBILE_REBUILD`

Wymaga problemu mobilnego: `not_mobile_friendly`, `viewport_missing`, `mobile_layout_broken`, `tap_targets_bad`, `mobile_text_unreadable`.

Prog: confidence >=0.76, evidence >=2.  
T2: wymagane, gdy T0 widzi tylko poszlaki, a nie screenshot mobile.  
Subject: `Wersja mobilna strony {domena}`

### `TECH_REBUILD`

Wymaga aktywnej strony i technicznego dlugu: `speed_slow`, `old_stack`, `old_assets`, `cache_missing`, `compression_missing`, `html_too_large`, `js_error_blocking`.

Prog: confidence >=0.74, evidence >=2.  
T2: zwykle niewymagane, chyba ze performance i wyglad sa sprzeczne.  
Subject: `Techniczna przebudowa strony {firma}`

## 4. Reguly A-H

### A. T2 eligibility

| Rule key | Warunek | Decyzja |
|---|---|---|
| `T2_SKIP_NO_CONTACT` | `contactability < 40` | `skip` |
| `T2_SKIP_STRONG_CAMPAIGN` | `campaign_confidence >= 0.82` i evidence >=2 | bez T2, QA |
| `T2_MUST_AMBIGUOUS_HOOK` | T0 widzi problem, T1 confidence <0.70, evidence <2 | `t2_required` |
| `T2_MUST_VISUAL_DECISION_BLOCKER` | claim dotyczy wygladu/CTA/mobile/trust | `t2_required` |
| `T2_MUST_CAMPAIGN_TIE` | dwie kampanie w odleglosci <=8 pkt | `t2_required` |
| `T2_MUST_CONFLICTING_EVIDENCE` | T0/T1 sa sprzeczne dla aktywnej strony | `t2_required` |

Dynamiczny prompt T2:

```text
Ocen strone {domena} dla firmy {firma}. Kontekst T0/T1: {kontekst}.
Kandydaci kampanii: {kampanie}. Sprawdz tylko widoczne elementy:
pierwsze wrazenie, CTA, mobile, trust, szablon WordPress.
Zwroc JSON: labels[], evidence[], confidence, recommended_campaign, blockers.
Dozwolone kampanie: REDESIGN_OUTDATED, REDESIGN_ADS_WASTE,
REDESIGN_CONVERSION, REDESIGN_TRUST, WORDPRESS_REWORK, MOBILE_REBUILD,
TECH_REBUILD, INCONCLUSIVE.
```

Prompt konfliktowy:

```text
Rozstrzygnij tylko konflikt: {konflikt}. Uzyj tych samych screenshotow.
Zwroc JSON z recommended_campaign, confidence i maksymalnie 3 dowodami.
```

### B. Decision gates

1. `GATE_COMPLIANCE`: opt-out, active customer, active deal, hard bounce, cooldown -> `skip`.
2. `GATE_DATA_QUALITY`: brak domeny, domena prywatna, katalog, portal, marketplace, kraj poza PL -> `skip/manual_review`.
3. `GATE_INDUSTRY_FIT`: konkurencja web/design/SEO/ads/hosting/software -> `skip/manual_review`.
4. `GATE_SCAN_HEALTH`: timeout, 429, 5xx, SERVFAIL -> `retry`; final failed -> `manual_review/skip`.
5. `GATE_CONTACTABILITY`: <40 `skip`, 40-54 `manual_review`, >=55 dalej.
6. `GATE_EVIDENCE_AND_T2`: brak min. dowodow albo claim wizualny bez T2 -> `manual_review/t2_required`.
7. `GATE_CAMPAIGN_READY`: kampania z progami -> `send`; brak kampanii -> `manual_review/skip`.

### C. Campaign engine

Engine wybiera jedna kampanie. Kolejnosc konfliktow:

1. `REDESIGN_ADS_WASTE`, gdy jest platny ruch i strona marnuje budzet.
2. `MOBILE_REBUILD`, gdy mobile jest ewidentnie zepsuty.
3. `REDESIGN_TRUST`, gdy problem SSL/trust jest krytyczny.
4. `REDESIGN_OUTDATED`, gdy glowny dowod to starosc/RWD/visual.
5. `REDESIGN_CONVERSION`, gdy glowny dowod to CTA/formularz/contact flow.
6. `WORDPRESS_REWORK`, gdy WP/CMS plus realny problem.
7. `TECH_REBUILD`, gdy problem jest glownie techniczny.

### D. Suppression

Opt-out permanent. Hard bounce blokuje email permanent i firme 180 dni. Soft bounce blokuje email 14 dni. Ten sam domain/company po wysylce ma cooldown 90 dni, a ta sama kampania 180 dni.

### E. Evidence

Dowod ma `type`, `key`, `value`, `source_url`, `confidence`, `captured_at`, `expires_at`. Tekst dowodu jest faktograficzny, bez obietnic. CSV pokazuje maksymalnie 3 dowody.

### F. Feedback

Importowane eventy MVP: `positive_reply`, `negative_reply`, `bounce_hard`, `bounce_soft`, `opt_out`, `manual_reject`, `manual_approve`. Feedback aktualizuje suppression i metryki kampanii.

### G. Rate limits

HTTP: start 50 concurrent. DNS: 100 concurrent. Playwright: 2 konteksty. T2: limit dzienny kosztu i limit per batch. Retry transportowy 1 raz z jitterem.

### H. Import i deduplikacja

Dedup po registered domain, NIP, REGON/KRS, email i telefonie. NIP z poprawna suma kontrolna jest najsilniejszym kluczem. Konflikty zrodel: VAT/KRS > HTML > import.
