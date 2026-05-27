# Rules

Rulesety znajduja sie w `leadpipe/rules/` i sa ladowane automatycznie przez `DecisionEngine`. Wszystkie maja wersje `ruleset-2026-05-23-www-final-v1`.

Silnik sortuje reguly globalnie po `priority`, wiec pliki nie sa osobnymi fazami wykonania. W praktyce niskie priorytety tworza gates i suppression, srednie priorytety T2 eligibility, a kampanie zaczynaja sie od priorytetu 401.

## Format Reguly

```yaml
version: "ruleset-2026-05-23-www-final-v1"
rules:
  - key: CAMPAIGN_REDESIGN_CONVERSION
    priority: 403
    combine: weighted
    threshold: 0.55
    conditions:
      - signal: cta_missing
        operator: eq
        value: true
        weight: 0.30
    decision: send
    campaign: REDESIGN_CONVERSION
    confidence_threshold: 0.74
    min_evidence: 2
    subject: "Zapytania ze strony {firma}"
    description: "Strona dziala, ale CTA ogranicza zapytania."
```

## `campaigns.yml`

Plik definiuje 7 finalnych kampanii WWW-first. `send` w MVP oznacza gotowosc logiczna do QA/CSV, a nie automatyczna wysylke.

| Rule key | Priorytet | Kampania | Warunek | Prog |
|---|---:|---|---|---|
| `CAMPAIGN_REDESIGN_ADS_WASTE` | 401 | `REDESIGN_ADS_WASTE` | Tracking/ads hints plus dowod marnowania ruchu: GTM, Meta Pixel, UTM/landing, wolna strona, slabe CTA. | `weighted >= 0.65`, confidence `>= 0.80`, evidence `>= 3` |
| `CAMPAIGN_REDESIGN_OUTDATED` | 402 | `REDESIGN_OUTDATED` | Visual outdated, brak viewportu, legacy HTML, table layout lub brak mobile-friendly. | `or`, confidence `>= 0.76`, evidence `>= 2` |
| `CAMPAIGN_REDESIGN_CONVERSION` | 403 | `REDESIGN_CONVERSION` | Brak/slabe CTA, brak formularza, ukryty kontakt lub wolna strona. | `weighted >= 0.55`, confidence `>= 0.74`, evidence `>= 2` |
| `CAMPAIGN_REDESIGN_TRUST` | 404 | `REDESIGN_TRUST` | Brak HTTPS, invalid/expired cert, low trust, brak identity, formularz jako dodatkowy dowod. | `weighted >= 0.60`, confidence `>= 0.76`, evidence `>= 2` |
| `CAMPAIGN_WORDPRESS_REWORK` | 405 | `WORDPRESS_REWORK` | WordPress/CMS plus slaby template, stare assety, wolny stack albo plugin risk. | `weighted >= 0.60`, confidence `>= 0.74`, evidence `>= 2` |
| `CAMPAIGN_MOBILE_REBUILD` | 406 | `MOBILE_REBUILD` | Brak mobile-friendly, brak viewportu, broken mobile layout, zle tap targety albo nieczytelny tekst mobile. | `weighted >= 0.60`, confidence `>= 0.76`, evidence `>= 2` |
| `CAMPAIGN_TECH_REBUILD` | 407 | `TECH_REBUILD` | Wolna strona, stary stack/assets, brak cache/kompresji albo zbyt duzy HTML. | `weighted >= 0.60`, confidence `>= 0.74`, evidence `>= 2` |

### Subject templates

| Kampania | Subject |
|---|---|
| `REDESIGN_ADS_WASTE` | `Czy strona {domena} wykorzystuje ruch z reklam?` |
| `REDESIGN_OUTDATED` | `Pierwsze wrazenie na stronie {domena}` |
| `REDESIGN_CONVERSION` | `Zapytania ze strony {firma}` |
| `REDESIGN_TRUST` | `Zaufanie klienta na {domena}` |
| `WORDPRESS_REWORK` | `Odswiezenie strony {domena} bez WordPressa` |
| `MOBILE_REBUILD` | `Wersja mobilna strony {domena}` |
| `TECH_REBUILD` | `Techniczna przebudowa strony {firma}` |

## `decision_gates.yml`

Gates chronia jakosc danych, compliance i reputacje przed kampaniami.

| Rule key | Priorytet | Decyzja | Kiedy |
|---|---:|---|---|
| `GATE_COMPLIANCE_OPT_OUT` | 1 | `skip` | `opt_out == true` |
| `GATE_COMPLIANCE_SUPPRESSION` | 2 | `skip` | `suppressed == true` |
| `GATE_DATA_QUALITY_INVALID_INPUT` | 3 | `skip` | `domain_present == false` |
| `GATE_DATA_QUALITY_NOT_COMPANY` | 4 | `skip` | `not_company_confidence >= 0.75` |
| `GATE_DATA_QUALITY_COUNTRY_FIT` | 5 | `skip` | `country_fit == false` i `country_confidence >= 0.75` |
| `GATE_INDUSTRY_FIT_EXCLUSION` | 6 | `skip` | `competitor_confidence >= 0.85` |
| `GATE_SCAN_HEALTH_RETRY` | 7 | `retry` | Blad przejsciowy i `retry_count <= 1` |
| `GATE_SCAN_HEALTH_FAILED_FINAL` | 8 | `manual_review` | Finalny blad skanu, ale `lead_value >= 75` |
| `GATE_CONTACTABILITY_SKIP` | 9 | `skip` | `contactability < 40` |
| `GATE_CONTACTABILITY_MANUAL` | 10 | `manual_review` | `contactability < 55` |
| `GATE_EVIDENCE_AND_T2_MINIMUM` | 300 | `manual_review` | Jest kandydat kampanii, ale `evidence_count < 1` |
| `GATE_CAMPAIGN_READY_MANUAL_QA` | 390 | `manual_review` | Kampania logicznie gotowa, ale MVP wymaga QA |

Uwaga: przez priorytet 390 bramka QA moze zatrzymac lead przed regulami kampanii, jesli sygnal `campaign_candidate` jest ustawiony w context.

## `evidence.yml`

Ruleset opisuje fallback dla przypadkow, gdzie dowody sa mocne, ale nie ma dopasowanej kampanii lub dowody sa sprzeczne.

| Rule key | Priorytet | Decyzja | Kiedy |
|---|---:|---|---|
| `EVIDENCE_CONFLICTING` | 35 | `manual_review` | `conflicting_evidence == true` |
| `EVIDENCE_STRONG_ENOUGH` | 900 | `manual_review` | `evidence_strength >= 70` i `evidence_count >= 2`, ale brak kampanii przed fallbackiem |

Dowody powinny byc faktograficzne, powiazane z sygnalem i zrodlem, a w CSV maksymalnie trzy.

## `suppression.yml`

Suppression blokuje kontakt przed campaign engine.

| Rule key | Priorytet | Decyzja | Kiedy |
|---|---:|---|---|
| `SUPPRESSION_HARD_BOUNCE` | 20 | `skip` | `hard_bounce_active == true` |
| `SUPPRESSION_ACTIVE_CUSTOMER` | 21 | `skip` | `active_customer == true` |
| `SUPPRESSION_COOLDOWN` | 22 | `skip` | `cooldown_active == true` |

Zgodnie z dokumentami zrodlowymi:

- opt-out jest permanentny;
- hard bounce blokuje email permanentnie i firme czasowo;
- cooldown ogranicza ponowny kontakt po poprzedniej kampanii;
- suppression powinno dzialac po emailu, domenie, NIP, telefonie, leadzie albo batchu.

## `feedback.yml`

Feedback loop zamienia zdarzenia outreachowe na decyzje/suppression.

| Rule key | Priorytet | Decyzja | Kiedy |
|---|---:|---|---|
| `FEEDBACK_OPT_OUT` | 15 | `skip` | `latest_event == "opt_out"` |
| `FEEDBACK_MEETING` | 16 | `skip` | `latest_event == "meeting"` |

W modelach runtime dostepne sa tez eventy: `sent`, `open`, `reply`, `positive_reply`, `soft_bounce`, `hard_bounce`, `manual_reject`. Dokumenty specyfikacyjne rozszerzaja feedback o negative reply, deal i revenue jako future scope.

## `t2_eligibility.yml`

Ruleset T2 decyduje, kiedy vision jest niepotrzebne, kiedy lead trafia do QA, a kiedy potrzebne sa screenshoty.

| Rule key | Priorytet | Decyzja | Kiedy |
|---|---:|---|---|
| `T2_SKIP_NO_CONTACT` | 120 | `skip_t2` -> engine normalizuje do `skip` | `contactability < 40` |
| `T2_SKIP_STRONG_CAMPAIGN` | 121 | `manual_review` | `campaign_confidence >= 0.82` i `evidence_count >= 2`; dowody wystarczaja bez T2, MVP kieruje do QA |
| `T2_MUST_AMBIGUOUS_HOOK` | 310 | `t2_required` | `t0_confidence >= 0.70`, `t1_confidence < 0.70`, `evidence_count < 2` |
| `T2_MUST_VISUAL_DECISION_BLOCKER` | 311 | `t2_required` | Claim wymaga oceny wygladu/CTA/mobile/trust, confidence kampanii <0.76, fit i kontakt OK |
| `T2_MUST_CAMPAIGN_TIE` | 312 | `t2_required` | Dwie kampanie sa blisko: `campaign_tie_delta <= 8`, lead value i kontakt OK |
| `T2_MUST_CONFLICTING_EVIDENCE` | 313 | `t2_required` | Sprzeczne dowody dla aktywnej strony i sensowny industry fit |

## Relacja Do Dokumentow Zrodlowych

Najwazniejsze decyzje rulesetu pochodza z:

- `REGULY-FINAL.md`: finalne 7 kampanii, gates, T2 i zasady nadrzedne;
- `KAMPANIE-REDESIGN.md`: uzasadnienie WWW-first i kolejnosc konfliktow;
- `ANALIZA-KRYTYCZNA.md`: selektywne T2, feedback loop i rozdzielenie diagnostyki od decyzji sprzedazowej;
- `RAPORT-SPOJNOSCI.md`: znane niespojnosci i ryzyka first-match engine.

## Znane Ograniczenia Rulesetow

- Engine konczy ocene po pierwszym matchu, wiec `evaluated_rules` nie zawiera regul po zwyciezcy.
- `min_evidence` korzysta z globalnego `evidence_count`, nie z dowodow per kampania.
- Niektore sygnaly w YAML sa future/T2-only, np. `visual_outdated`, `mobile_layout_broken`, `wordpress_poor_template`, `low_trust`.
- `CURRENT_RULESET_VERSION` w kodzie bazowym rozni sie od wersji YAML; engine wybiera wersje z plikow YAML.
