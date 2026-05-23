# RAPORT-SPOJNOSCI

Data: 2026-05-23  
Zakres: dokumenty, modele, engine, YAML rules, dashboard i plan implementacji w `/tmp/codex-review`.

## A. Co jest spojne i dziala w teorii?

- Strategia WWW-first jest sensowna: kampanie techniczne zostaly zdegradowane do dowodow wspierajacych, a glowny produkt to nowa strona, redesign, rework WP i opieka.
- Warstwy T0/T1/T0.5/Gates/T2/Campaign sa logiczne. T0/T1 zbieraja tanie dowody, T2 rozstrzyga tylko sprawy wizualne.
- `DecisionTrace` w modelach ma pola potrzebne do audytu: `ruleset_version`, `evaluated_rules`, `winning_rule`, `blocked_by`, `score_breakdown`, `decision_reason`.
- `OutreachEvent` jest wystarczajaco prosty dla MVP: bounce, opt-out i replies bez modelowania calego lejka CRM.
- `DecisionEngine` laduje YAML z `leadpipe/rules/*.yml`, sortuje reguly po priorytecie i obsluguje `and`, `or`, `weighted`.
- Dashboard ma dobre podstawy QA: lista leadow, filtry, szczegoly, evidence, akcje approve/reject/manual, eksport CSV i import feedbacku.
- Finalny zestaw 8 kampanii da sie obronic biznesowo i laczy sesje 1 oraz sesje 3.

## B. Co jest niespojne?

1. Kampanie w kodzie sa stare.

`leadpipe/models.py` ma enumy: `SITE_DOWN_RESCUE`, `SECURITY_TRUST_FIX`, `EMAIL_DELIVERABILITY_FIX`, `PERFORMANCE_CONVERSION_FIX`, `SEO_VISIBILITY_FIX`, `REDESIGN_CONVERSION_AUDIT`, `CARE_PLAN_MAINTENANCE`, `QUALIFIED_CUSTOM_AUDIT`. Finalny ruleset uzywa: `NEW_WEBSITE`, `REDESIGN_ADS_WASTE`, `REDESIGN_OUTDATED`, `REDESIGN_CONVERSION`, `REDESIGN_TRUST`, `WORDPRESS_REWORK`, `CARE_PLAN`, `QUALIFIED_CUSTOM`.

Efekt: po aktualizacji YAML obecny `DecisionEngine()` nie zaladuje finalnych kampanii bez migracji enumu.

2. `t2_optional` istnieje w kodzie i dashboardzie, ale finalne publiczne decyzje to `send/skip/manual_review/t2_required/retry`.

Rekomendacja: `t2_optional` traktowac jako wewnetrzny status eligibility albo usunac z publicznego `DecisionAction`.

3. Dashboard i sample data nadal sa oparte o stare kampanie.

`dashboard/app.js`, `subjectFor()` i `dashboard/data/sample-batch.json` pokazuja kampanie pocztowe, SEO i performance jako glowne typy. To nie pasuje do finalnego WWW-first.

4. CSV export dashboardu ma inne kolumny niz architektura.

Obecny eksport: `company, domain, nip, email, phone, campaign, subject, evidence_1, evidence_2, confidence, decision`. Docelowo powinny dojsc: `evidence_3`, `rule_key`, `ruleset_version`, `suppression_status`.

5. `ExportCsvSchema` w `leadpipe/csv_schemas.py` nie ma `decision`, `rule_key`, `ruleset_version`.

Dashboard eksportuje `decision`, ale schema backendowa nie opisuje tego kontraktu.

6. Engine konczy po pierwszej pasujacej regule.

To jest proste i audytowalne, ale moze byc zbyt wczesne dla finalnego wyboru kampanii, gdzie chcemy porownac kilku kandydatow i dopiero potem wybrac winnera. W szczegolnosci `evaluated_rules` nie obejmie regul po pierwszym matchu.

7. `min_evidence` w engine korzysta z globalnego `evidence_count`.

Finalny ruleset wymaga dowodow per kampania i czasem roznych typow dowodow, np. ads + slaba strona + kontakt. Globalny licznik nie wystarczy.

8. `Lead` ma za malo pol jawnych dla WWW-first.

Sporo informacji moze wejsc do `metadata`, ale brakuje jawnych pol typu `regon`, `krs`, `vat_status`, `legal_form`, `industry`, `city`, `voivodeship`, `contact_phone` vs `phone`, `source_priority`.

9. Ruleset version jest rozjechany.

Kod ma `ruleset-2026-05-23-v1`, REGULY-v2 mialo `ruleset-2026-05-23-v2`, finalne dokumenty maja `ruleset-2026-05-23-www-final-v1`.

## C. Co brakuje przed codingiem?

- Jedna migracja kontraktu kampanii w `leadpipe/models.py`.
- Aktualizacja testow pod finalne kampanie.
- Mapa sygnalow: nazwy z YAML musza odpowiadac outputowi T0/T1/T0.5/T2.
- Walidacja YAML niezalezna od enumow albo enum z finalnymi ID.
- Per-campaign evidence matching, nie tylko globalne `evidence_count`.
- Dashboard labels/sample data dla finalnych kampanii.
- CSV contract wspolny dla backendu i dashboardu.
- Fixtures HTML dla polskich stron: brak strony, parking, WP, brak viewportu, slabe CTA, SSL/trust, social-only.
- Definicja `business_confirmed`: czy wystarczy NIP, VAT active, import CRM, JSON-LD, czy kombinacja.

## D. Co jest nadmiarowe?

- `EMAIL_DELIVERABILITY_FIX` jako kampania glowna: poza zakresem WWW-first.
- `SEO_VISIBILITY_FIX` jako kampania glowna: zostaje dowodem dla redesign/visibility, nie osobnym typem outreachu.
- `SECURITY_TRUST_FIX` jako czysty SSL fix: zastapione przez `REDESIGN_TRUST`.
- `PERFORMANCE_CONVERSION_FIX` jako osobna kampania: wchloniete przez `REDESIGN_CONVERSION` albo `REDESIGN_ADS_WASTE`.
- `SITE_DOWN_RESCUE`: w finalnym zestawie zwykle podpada pod `NEW_WEBSITE` lub `retry/manual_review`.
- Rozbudowane feedback events typu open/meeting w enumie MVP: moga zostac future scope, ale nie powinny sterowac MVP.

## E. Ryzyka

- False positive dla "starej strony" bez T2. Brak viewportu lub stary HTML nie zawsze oznacza zly mobile.
- Ads inference po GTM/Meta Pixel moze byc mylace, bo tracking nie dowodzi aktywnego budzetu reklamowego.
- WordPress rework moze brzmiec agresywnie, jesli jedynym dowodem jest sam WP.
- Brak NIP w HTML moze niepotrzebnie obnizac dobre leady z firm uslugowych.
- Dynamiczne T2 prompty bez kalibracji moga dawac ogolne oceny zamiast konkretnych dowodow.
- Engine first-match moze blokowac najlepsza kampanie, jesli gate lub fallback ma zbyt wysoki priorytet.
- Po aktualizacji YAML do finalnych kampanii obecny kod nie jest gotowy do uruchomienia.

## F. Rekomendacja

Nie zaczynac jeszcze implementacji skanerow T0/T1. Najpierw poprawic kontrakt kampanii w kodzie, testach, dashboardzie i CSV.

Projekt jest gotowy koncepcyjnie do codingu po wykonaniu Fazy 0 z `PLAN-IMPLEMENTACJI.md`:

1. migracja enumow kampanii;
2. usuniecie albo ukrycie `t2_optional`;
3. aktualizacja testow engine;
4. dopasowanie dashboardu i sample data;
5. wspolny kontrakt CSV;
6. walidacja finalnego YAML.

Po tych poprawkach mozna zaczac kodzic T0/T1/T0.5.
