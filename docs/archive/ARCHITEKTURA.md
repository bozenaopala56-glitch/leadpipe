# ARCHITEKTURA: T0/T0.5/T1/T2 Lead Scoring Pipeline

Data: 2026-05-23  
Ruleset: `ruleset-2026-05-23-www-final-v1`  
Zakres: firmy z istniejaca strona, ktora wymaga redesignu, reworku, mobile rebuild albo technical rebuild.

## 1. Przeplyw

```text
CSV/CRM input
  -> normalize + dedupe
  -> T0 scanner
  -> T0.5 enrichment
  -> T1 parser
  -> decision gates
  -> campaign engine
  -> T2 selective vision
  -> final decision + DecisionTrace
  -> QA dashboard
  -> CSV export
  -> feedback import + suppression
```

T0, T0.5 i T1 zapisuja sygnaly oraz dowody. Gates chronia compliance i jakosc. Campaign engine wybiera jedna z 7 kampanii. T2 jest selektywnym rozszerzeniem dla claimow wizualnych.

## 2. Warstwy

### T0 scanner

Moduly: HTTP, DNS, SSL/TLS, HTML snapshot, robots, sitemap, lightweight performance, tech detection.

Wynik: `ScanResult`, `Signal[]`, `Evidence[]`, raw HTML snapshot i metryki retry. T0 nie renderuje JS i nie ocenia estetyki.

### T0.5 enrichment

Moduly: NIP extraction, checksum, Biala Lista VAT, cache, business identity merge.

Wynik: `business_confirmed`, `vat_active`, `company_name`, `address`, `regon/krs` jesli dostepne, `business_confidence`.

### T1 parser

Moduly: JSON-LD, meta/OG, headings, email, telefon, formularz, CTA, industry hints, contactability, lead value.

Wynik: `contactability`, `industry_fit`, `lead_value`, `cta_missing`, `form_missing`, `contact_hidden`, `wordpress_detected`, `ads/tracking` i dowody tekstowe.

### Gates

Siedem bramek: compliance, data quality, industry fit, scan health, contactability, evidence/T2, campaign ready. Gates zwracaja `skip`, `retry`, `manual_review`, `t2_required` albo przepuszczaja do kampanii.

### Campaign engine

Engine laduje YAML, waliduje kampanie przez `CampaignKey`, wybiera pierwsza pasujaca regule wedlug priorytetu i zapisuje `DecisionTrace`.

Finalne kampanie:

- `REDESIGN_OUTDATED`
- `REDESIGN_ADS_WASTE`
- `REDESIGN_CONVERSION`
- `REDESIGN_TRUST`
- `WORDPRESS_REWORK`
- `MOBILE_REBUILD`
- `TECH_REBUILD`

### Evidence engine

Evidence engine formatuje dowody do QA i CSV. Nie generuje agresywnego copywritingu. Kazdy dowod musi byc powiazany z sygnalem i zrodlem.

### T2 vision

Playwright robi screenshot desktop oraz mobile albo desktop plus podstrona kontakt/o nas/oferta. Kimi k2.5 vision dostaje dynamiczny prompt z kontekstem T0/T1 i lista dozwolonych kampanii. Wynik wraca jako sygnaly T2 oraz dowody.

### Dashboard

Dashboard obsluguje QA workflow: lista leadow, filtry, kampanie, trace, evidence, approve/reject/manual, batch view, eksport CSV, import feedbacku i preview subject/copywritingu.

## 3. Model danych

Minimalne encje:

- `Lead`: input, domena, firma, NIP, kontakt, status, batch.
- `ScanResult`: status warstwy, HTTP, final URL, snapshot, error.
- `Signal`: key/value/source/confidence/evidence_ids.
- `Evidence`: type/key/value/source_url/confidence/TTL.
- `CampaignDecision`: action, campaign, subject, confidence, rule_key, score.
- `DecisionTrace`: evaluated_rules, winning_rule, blocked_by, reason.
- `OutreachEvent`: feedback, bounce, opt-out, manual QA.
- `SuppressionEntry`: scope, value, reason, TTL/permanent.

## 4. Storage i kolejki

Postgres jest zrodlem prawdy dla leadow, scanow, decyzji, trace, suppression i feedbacku. Redis + RQ obsluguja joby T0, T0.5, T1, T2 i eksport. Snapshoty HTML/screenshoty moga byc plikami z referencja w DB.

## 5. Deploy

VM uruchamia:

- Postgres
- Redis
- RQ worker dla T0/T1/T2
- backend dashboardu
- systemd unit dla workerow i API
- cron/systemd timer dla batch importu, retry i cleanup cache

## 6. Granice MVP

MVP jest gotowe, gdy pipeline wykonuje:

```text
import -> T0 -> T0.5 -> T1 -> gates -> campaign -> QA -> CSV -> feedback
```

Dla smoke batcha 100 leadow:

- kazdy lead ma status koncowy albo retry;
- zadna suppression nie trafia do eksportu;
- `send` zawsze ma jedna z 7 kampanii;
- kazda decyzja ma `DecisionTrace`;
- dashboard pokazuje batch, kampanie i eksport;
- `pytest -q` przechodzi.
