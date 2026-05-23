# KAMPANIE-REDESIGN: ruleset WWW-first dla MeNET

Data: 2026-05-23  
Wersja rulesetu: `ruleset-2026-05-23-www-redesign-v1`  
Zakres: kwalifikacja leadow dla uslug tworzenia stron WWW: nowa strona, redesign, audyt konwersji, rework strony firmowej.  
Rynek: polskie MSP, przede wszystkim B2B, uslugi profesjonalne, produkcja, dystrybucja, firmy lokalne z budzetem reklamowym.

## 1. Zalozenie strategiczne

Pipeline ma sprzedawac tworzenie stron WWW, nie pojedyncze naprawy techniczne. Sygnały security, DNS, performance, analytics i SEO sa dowodami wspierajacymi, ale glowny hook brzmi:

- firma istnieje i nie ma strony, mimo ze klienci moga jej szukac online;
- firma istnieje i ma strone, ale strona jest stara, niewiarygodna, wolna, slaba mobilnie albo nie wspiera zapytan;
- firma placi za ruch z Google/Meta, ale kieruje go na strone, ktora nie konwertuje;
- firma ma aktywnosc w social media lub wizytowke Google, ale jej strona nie dorownuje poziomowi widocznosci.

Kampanie techniczne z poprzedniego rulesetu zostaja zdegradowane do `evidence_modifier`. Nie wybieramy kampanii `SECURITY_SSL` jako glownej, jesli mozemy bezpiecznie wybrac `REDESIGN_TRUST_SECURITY`.

## 2. Dostepne sygnaly

### 2.1. T0: techniczne i strukturalne

| Sygnal | Zrodlo | Do czego uzywac |
|---|---|---|
| `status:active` | HTTP | Strona istnieje i mozna ocenic redesign. |
| `status:inactive`, `status:error`, `dns:none` | HTTP/DNS | Brak dzialajacej strony lub awaria; tylko jako ostrozny hook nowej strony/rescue. |
| `ssl:no`, cert invalid | TLS | Pilnosc i zaufanie, nie samodzielna kampania. |
| `speed:slow`, wysoki TTFB, duzy HTML, brak compression | HTTP | Redesign/performance/conversion audit. |
| brak `viewport`, brak media queries, stary charset/table layout | HTML | Slaby sygnal braku RWD/starej strony. |
| brak title/meta/OG/canonical/sitemap | HTML/SEO | Niska jakosc strony i slabsza widocznosc. |
| WordPress/CMS hints | HTML/headers | Redesign away from WordPress albo maintenance risk. |
| brak GA/GTM/Meta Pixel | HTML | Brak pomiaru, szczegolnie przy reklamach. |
| linki social | HTML | Firma aktywna, strona moze odstawaac od social proof. |

### 2.2. T0.5: firma

| Sygnal | Zrodlo | Do czego uzywac |
|---|---|---|
| poprawny NIP, VAT active | Biala Lista VAT | Potwierdzenie, ze firma istnieje. |
| nazwa, adres, REGON/KRS | VAT/import/T1 | Dedup, fit, personalizacja. |
| brak potwierdzenia firmy | T0.5/T1 | Obniza confidence, czasem manual review. |

### 2.3. T1: tresc, kontakt, fit

| Sygnal | Zrodlo | Do czego uzywac |
|---|---|---|
| email/telefon/formularz | HTML/import | Contactability i decyzja send/manual. |
| JSON-LD Organization/LocalBusiness | HTML | Potwierdzenie firmy i branza. |
| opis uslug, oferta, o nas, kontakt | HTML | Ocena kompletosci strony. |
| CTA/button/form detection | DOM | Redesign konwersji. |
| linki do Google Maps, Facebook, Instagram, LinkedIn | HTML | Istnienie online poza strona. |
| branza IT/software/digital/marketing | T1 | Suppression/konkurencja. |

### 2.4. T2: vision, tylko selektywnie

T2 jest wymagane, gdy decyzja zalezy od wygladu: "strona wyglada zle", "design jest przestarzaly", "CTA jest niewidoczne", "mobile wyglada slabo". T0/T1 moga jedynie stworzyc podejrzenie.

| Sygnal T2 | Zastosowanie |
|---|---|
| `visual:outdated` | Redesign strony starej lub szablonowej. |
| `visual:low_trust` | Redesign zaufania, branże B2B/uslugi. |
| `visual:weak_cta` | Audyt konwersji/redesign. |
| `visual:not_mobile_friendly` | Redesign RWD. |
| `visual:wordpress_poor_template` | Redesign z WordPress na kodowana strone. |
| `visual:modern_good` | Veto dla automatycznego send. |

## 3. Przemodelowane 8 kampanii

| Priorytet | Kampania | Cel | Glowny hook | Minimalne evidence | Prog send |
|---:|---|---|---|---|---:|
| 1 | `NEW_WEBSITE_GMB_NO_SITE` | Nowa strona | Firma istnieje online, ale nie ma dzialajacej strony | firma potwierdzona + brak strony/domena parkingowa + kontakt lub wizytowka/import | 0.78 |
| 2 | `NEW_WEBSITE_ACTIVE_COMPANY` | Nowa strona | Firma dziala, ale nie posiada wlasnego miejsca do prezentacji oferty | firma potwierdzona + brak www + branża MSP + kontakt | 0.76 |
| 3 | `REDESIGN_ADS_WASTE` | Redesign | Budzet reklamowy trafia na slaba/stara strone | ads/pixel/landing hints + slaba strona/CTA/performance + firma potwierdzona | 0.80 |
| 4 | `REDESIGN_OUTDATED_SITE` | Redesign | Strona dziala, ale wyglada lub zachowuje sie jak przestarzala | active site + stare HTML/brak RWD/T2 outdated + kontakt | 0.76 |
| 5 | `REDESIGN_CONVERSION_CTA` | Redesign/audyt konwersji | Strona nie prowadzi do zapytania | slabe CTA/brak formularza/wolno + oferta firmy + kontakt | 0.74 |
| 6 | `REDESIGN_TRUST_SECURITY` | Redesign z pilnoscia zaufania | Wyglad i podstawy zaufania moga obnizac liczbe zapytan | slaby design lub brak trust + SSL/cert/security/meta issue | 0.76 |
| 7 | `REDESIGN_WP_REWORK` | Redesign z WordPress | Strona na WordPress wyglada szablonowo, wolno albo ryzykownie | WP hints + slaby visual/performance/old assets + firma fit | 0.74 |
| 8 | `CUSTOM_WEBSITE_AUDIT` | Manual lub wysoki fit | Dobry lead, ale automatyka nie ma jednego mocnego hooka | fit + kontakt + 2 neutralne obserwacje | 0.70 manual, nie auto-send w MVP |

### 3.1. Kolejnosc wyboru kampanii

1. Suppression i compliance zawsze blokuja kampanie.
2. Firma nieistniejaca, domena parkingowa bez potwierdzonej firmy albo marketplace: `skip`.
3. Brak strony + firma potwierdzona: najpierw `NEW_WEBSITE_*`.
4. Firma z reklamami lub pixelami + slaba strona: `REDESIGN_ADS_WASTE`.
5. Strona aktywna + stara/slaba wizualnie: `REDESIGN_OUTDATED_SITE`.
6. Strona aktywna + wolna/slabe CTA/brak formularza: `REDESIGN_CONVERSION_CTA`.
7. WordPress nie jest sam w sobie problemem; dopiero WordPress + slaby wyglad/performance/maintenance risk daje `REDESIGN_WP_REWORK`.
8. Brak mocnego hooka przy dobrym fit: `CUSTOM_WEBSITE_AUDIT` jako `manual_review`, nie automatyczny send.

### 3.2. Bezpieczne subject patterns

| Kampania | Subject pattern |
|---|---|
| `NEW_WEBSITE_GMB_NO_SITE` | "`{firma}`: strona firmowa dla zapytan z Google" |
| `NEW_WEBSITE_ACTIVE_COMPANY` | "`{firma}`: wlasna strona dla oferty i kontaktu" |
| `REDESIGN_ADS_WASTE` | "Czy strona `{domena}` wykorzystuje ruch z reklam?" |
| `REDESIGN_OUTDATED_SITE` | "Pierwsze wrazenie na stronie `{domena}`" |
| `REDESIGN_CONVERSION_CTA` | "Zapytania ze strony `{firma}`" |
| `REDESIGN_TRUST_SECURITY` | "Zaufanie klienta na `{domena}`" |
| `REDESIGN_WP_REWORK` | "Odświeżenie strony `{domena}` bez WordPressa" |
| `CUSTOM_WEBSITE_AUDIT` | "Krotki audyt strony `{firma}`" |

## 4. Drzewo decyzyjne

```text
START
  |
  v
Suppression? opt-out, klient, deal, konkurencja >=0.85
  |-- tak --> skip
  |
  v
Czy to firma PL / MSP?
  |-- nie / confidence >=0.75 --> skip
  |-- niepewne, lead_value >=70 --> manual_review
  |
  v
Contactability >=55?
  |-- nie, lead_value <75 --> skip
  |-- nie, lead_value >=75 --> manual_review
  |
  v
Strona dziala?
  |-- brak strony + firma potwierdzona --> NEW_WEBSITE
  |-- brak strony + brak firmy --> skip/manual
  |-- aktywna --> ocena redesign
  |
  v
Czy strona jest nowoczesna, szybka, ma SSL, RWD, CTA i kompletne info?
  |-- tak --> skip/manual low hook
  |
  v
Czy sa reklamy/pixel/landing/UTM?
  |-- tak + slaba strona --> REDESIGN_ADS_WASTE
  |
  v
Czy problem jest glownie wyglad/RWD/wiek strony?
  |-- T2/T1 potwierdza --> REDESIGN_OUTDATED_SITE
  |
  v
Czy problem jest glownie konwersja?
  |-- brak CTA/formularza/wolno --> REDESIGN_CONVERSION_CTA
  |
  v
Czy problem jest trust/security?
  |-- slaby wyglad + SSL/cert/meta/security --> REDESIGN_TRUST_SECURITY
  |
  v
Czy strona jest WP i slaba?
  |-- tak --> REDESIGN_WP_REWORK
  |
  v
CUSTOM_WEBSITE_AUDIT manual_review albo skip
```

## 5. Reguly kwalifikacji leadow

Skala:

- `Decyzja`: `send`, `manual_review`, `skip`.
- `Priorytet`: 1 najwyzszy, 5 najnizszy.
- `Confidence`: minimalny prog decyzji po uwzglednieniu dowodow.
- Reguly z `T2` jako warunkiem moga byc automatyczne dopiero po pilocie T2; w MVP bez T2 ida do `manual_review`, chyba ze T0/T1 maja twarde dowody.

### 5.1. Nowa strona

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_NEW_SITE_GOOD_1` | T0: brak dzialajacej strony (`status:inactive`/`dns:none`/parking) + T0.5/T1: firma potwierdzona + T1/import: kontakt >=55 | `send` | `NEW_WEBSITE_ACTIVE_COMPANY` | 1 | 0.78 | Producent ma NIP i telefon, ale domena pokazuje parking lub nie odpowiada. |
| `LEAD_NEW_SITE_GOOD_2` | T0: brak wlasnej domeny lub tylko profil/katalog w imporcie + T0.5: VAT active + T1/import: Google Business/source potwierdza firme | `send` | `NEW_WEBSITE_GMB_NO_SITE` | 1 | 0.80 | Firma widoczna w Google Maps, ma telefon, ale nie ma strony. |
| `LEAD_NEW_SITE_GOOD_3` | T0: domena przekierowuje na Facebook/Instagram/marketplace + T1: social aktywne + T0.5: firma potwierdzona | `send` | `NEW_WEBSITE_GMB_NO_SITE` | 2 | 0.76 | Salon uslugowy ma tylko Facebook jako "strone". |
| `LEAD_NEW_SITE_MANUAL_1` | T0: brak strony + T1: kontakt tylko telefon/formularz z importu + brak NIP/VAT, ale branza fit >=70 | `manual_review` | `NEW_WEBSITE_ACTIVE_COMPANY` | 3 | 0.66 | Lokalna firma instalacyjna z telefonu w bazie, ale bez NIP w HTML/import. |
| `LEAD_NEW_SITE_SKIP_1` | T0: domena parkingowa + T0.5/T1: brak potwierdzenia firmy + contactability <40 | `skip` | `SKIP` | 1 | 0.75 | Kupiona domena bez danych firmy i kontaktu. |

### 5.2. Redesign: reklamy i marnowany ruch

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_REDESIGN_ADS_GOOD_1` | T0/T1: Google Ads/landing/UTM/GTM/Meta Pixel hints + T0: `speed:slow` albo brak RWD + T1: kontakt >=55 | `send` | `REDESIGN_ADS_WASTE` | 1 | 0.80 | Firma ma GTM i pixel, ale strona laduje sie >3 s i nie ma wyraznego CTA. |
| `LEAD_REDESIGN_ADS_GOOD_2` | T1: landing page lub parametry kampanii + T2: `visual:weak_cta`/`low_trust` + firma potwierdzona | `send` | `REDESIGN_ADS_WASTE` | 1 | 0.82 | Reklama prowadzi na strone bez formularza i z przestarzalym hero. |
| `LEAD_REDESIGN_ADS_MANUAL_1` | T0/T1: GTM/Meta Pixel jest, ale strona technicznie OK; T2 niedostepne albo niejednoznaczne | `manual_review` | `REDESIGN_ADS_WASTE` | 3 | 0.68 | Pixel sugeruje kampanie, ale automatyka nie widzi slabej strony. |
| `LEAD_REDESIGN_ADS_SKIP_1` | T0/T1: ads/pixel + T2: `visual:modern_good` + szybka strona + CTA/formularz obecne | `skip` | `SKIP` | 4 | 0.82 | Nowoczesna strona z dobrym formularzem i trackingiem. |

### 5.3. Redesign: stara lub slaba strona

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_REDESIGN_OLD_GOOD_1` | T0: `status:active` + brak `viewport` lub table layout/HTML legacy + T1: kontakt >=55 + firma fit >=60 | `send` | `REDESIGN_OUTDATED_SITE` | 1 | 0.78 | Firma produkcyjna ma strone w starym HTML bez wersji mobilnej. |
| `LEAD_REDESIGN_OLD_GOOD_2` | T2: `visual:outdated` confidence >=0.80 + T1: oferta/kontakt istnieje + T0.5/T1: firma potwierdzona | `send` | `REDESIGN_OUTDATED_SITE` | 1 | 0.80 | Strona dziala, ale wyglada jak katalog z lat 2000. |
| `LEAD_REDESIGN_OLD_GOOD_3` | T0: brak meta/OG, brak sitemap, brak RWD hints + T1: oferta jest, ale struktura uboga | `send` | `REDESIGN_OUTDATED_SITE` | 2 | 0.74 | Firma ma oferte w jednym bloku tekstu, bez podstron uslug. |
| `LEAD_REDESIGN_OLD_MANUAL_1` | T0: strona OK technicznie, ale brak RWD hints; T2 brak lub screenshot niepewny | `manual_review` | `REDESIGN_OUTDATED_SITE` | 3 | 0.66 | Desktop HTML wyglada poprawnie, ale brak viewport moze oznaczac slaby mobile. |
| `LEAD_REDESIGN_OLD_SKIP_1` | T0: strona aktywna, SSL, szybka, viewport, analytics, meta + T2: `visual:modern_good` | `skip` | `SKIP` | 5 | 0.84 | Firma ma nowoczesna, szybka strone i dobry kontakt. |

### 5.4. Redesign: konwersja, CTA, formularze

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_CONVERSION_GOOD_1` | T0: `speed:slow` + T1: brak wyraznego CTA/formularza + kontakt email/telefon obecny | `send` | `REDESIGN_CONVERSION_CTA` | 2 | 0.76 | Strona uslugowa ma opis, ale jedyny kontakt jest w stopce. |
| `LEAD_CONVERSION_GOOD_2` | T1: oferta jest, ale brak podstrony kontakt/o nas/formularza + firma potwierdzona + industry_fit >=60 | `send` | `REDESIGN_CONVERSION_CTA` | 2 | 0.74 | Firma B2B pokazuje uslugi, ale nie prowadzi klienta do zapytania. |
| `LEAD_CONVERSION_GOOD_3` | T2: `visual:weak_cta` + T0: wolno albo brak mobile hints + contactability >=70 | `send` | `REDESIGN_CONVERSION_CTA` | 2 | 0.78 | CTA jest niewidoczne, a mobile screenshot wymaga przewijania do kontaktu. |
| `LEAD_CONVERSION_MANUAL_1` | T1: strona minimalistyczna, brak CTA, ale szybka i nowoczesna wedlug T0 | `manual_review` | `REDESIGN_CONVERSION_CTA` | 3 | 0.64 | Strona premium ma malo tresci; moze byc zamierzone. |
| `LEAD_CONVERSION_MANUAL_2` | T1: tylko email bez formularza + firma fit >=70 + brak innych problemow | `manual_review` | `REDESIGN_CONVERSION_CTA` | 4 | 0.62 | Firma konsultingowa ma tylko adres email, bez formularza. |

### 5.5. Redesign: zaufanie, SSL, security jako pilnosc

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_TRUST_GOOD_1` | T0: `ssl:no` lub cert invalid + T2/T1: slaby/stary wyglad albo brak trust elements + kontakt >=55 | `send` | `REDESIGN_TRUST_SECURITY` | 2 | 0.78 | Strona wyglada archaicznie i pokazuje ostrzezenie HTTPS. |
| `LEAD_TRUST_GOOD_2` | T0: brak SSL + T1: formularz kontaktowy lub zapytaniowy na stronie + firma potwierdzona | `send` | `REDESIGN_TRUST_SECURITY` | 2 | 0.76 | Klient moze wysylac dane przez formularz bez HTTPS. |
| `LEAD_TRUST_MANUAL_1` | T0: SSL jest, ale brak polityki prywatnosci/cookie/contact identity + T2: low trust | `manual_review` | `REDESIGN_TRUST_SECURITY` | 3 | 0.66 | Strona ma formularz, ale brak danych firmy i zaufania. |
| `LEAD_TRUST_SKIP_1` | T0: brak SSL, ale strona nieaktywna lub parking + brak firmy | `skip` | `SKIP` | 1 | 0.75 | Brak SSL na pustej domenie nie jest leadem redesign. |

### 5.6. WordPress i rework bez WordPressa

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_WP_GOOD_1` | T0: WordPress hints + T2: `visual:wordpress_poor_template`/`outdated` + T1: firma fit >=60 | `send` | `REDESIGN_WP_REWORK` | 2 | 0.76 | Strona na WP wyglada jak gotowy szablon i nie buduje zaufania. |
| `LEAD_WP_GOOD_2` | T0: WordPress + `speed:slow` + brak cache/compression hints + T1: CTA/formularz slabe | `send` | `REDESIGN_WP_REWORK` | 2 | 0.74 | WP jest wolny, a formularz jest ukryty nisko na stronie. |
| `LEAD_WP_MANUAL_1` | T0: WordPress + stare assety/plugin hints + brak T2 + firma wysokiej wartosci | `manual_review` | `REDESIGN_WP_REWORK` | 3 | 0.66 | Producent B2B ma WP, ale sam fakt WP nie wystarcza do maila. |
| `LEAD_WP_SKIP_1` | T0: WordPress, ale szybki, nowoczesny, SSL, CTA, T2 good | `skip` | `SKIP` | 5 | 0.82 | Dobra strona WP bez widocznego problemu. |

### 5.7. Social proof kontra slaba strona

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_SOCIAL_GOOD_1` | T1: linki do aktywnych social + T2/T0: strona stara/brak RWD + kontakt >=55 | `send` | `REDESIGN_OUTDATED_SITE` | 2 | 0.74 | Firma publikuje na Facebooku/LinkedIn, ale strona wyglada duzo slabiej. |
| `LEAD_SOCIAL_GOOD_2` | T1: social media + brak kompletnej oferty/kontaktu na stronie + firma potwierdzona | `send` | `REDESIGN_CONVERSION_CTA` | 3 | 0.72 | Social jest aktywny, ale strona nie zamienia zainteresowania w zapytania. |
| `LEAD_SOCIAL_MANUAL_1` | T1: social media + strona OK technicznie, brak T2 | `manual_review` | `CUSTOM_WEBSITE_AUDIT` | 4 | 0.62 | Firma moze miec dobry brand, ale potrzeba oceny wizualnej. |

### 5.8. Analytics i brak pomiaru

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_ANALYTICS_GOOD_1` | T1/T0: brak GA/GTM/Meta Pixel + T1: formularz/CTA obecny + T0: `speed:slow` lub slabe meta | `send` | `REDESIGN_CONVERSION_CTA` | 3 | 0.72 | Firma ma formularz, ale brak widocznego pomiaru i wolna strone. |
| `LEAD_ANALYTICS_MANUAL_1` | Brak analytics jako jedyny problem + strona nowoczesna/szybka | `manual_review` | `CUSTOM_WEBSITE_AUDIT` | 5 | 0.58 | Sam brak GTM nie dowodzi potrzeby redesignu. |
| `LEAD_ANALYTICS_SKIP_1` | Brak analytics + brak kontaktu + niski fit | `skip` | `SKIP` | 5 | 0.70 | Lokalna mikrostrona bez sygnalow budzetu i bez kontaktu. |

### 5.9. Manual review: przypadki srednie

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_MANUAL_RWD_1` | Firma istnieje, strona OK, ale T0: brak viewport/RWD hints | `manual_review` | `REDESIGN_OUTDATED_SITE` | 3 | 0.65 | Strona moze byc responsywna przez CSS, ale T0 tego nie potwierdza. |
| `LEAD_MANUAL_MINIMAL_1` | Firma istnieje, strona minimalistyczna, brak CTA, ale T2 nie wskazuje niskiego trust | `manual_review` | `REDESIGN_CONVERSION_CTA` | 4 | 0.62 | Minimalistyczny design moze byc celowy. |
| `LEAD_MANUAL_STRUCTURE_1` | Firma istnieje, brakuje "o nas", "oferta" lub "kontakt", ale kontakt jest w stopce | `manual_review` | `REDESIGN_CONVERSION_CTA` | 3 | 0.66 | Strona ma dane, lecz slabo prowadzi uzytkownika. |
| `LEAD_MANUAL_REBUILD_1` | T1/T0: teksty typu "nowa strona w budowie", "under construction", "coming soon", staging/dev hints | `manual_review` | `CUSTOM_WEBSITE_AUDIT` | 2 | 0.70 | Firma moze juz przebudowywac strone; nie wysylac automatu. |
| `LEAD_MANUAL_WP_SECURITY_1` | WordPress + stare pluginy/assets hints + brak innych problemow | `manual_review` | `REDESIGN_WP_REWORK` | 3 | 0.66 | Ryzyko techniczne istnieje, ale hook redesignu wymaga oceny. |

### 5.10. Skip i suppression

| ID | Warunek | Decyzja | Kampania | Priorytet | Confidence | Przyklad |
|---|---|---|---|---:|---:|---|
| `LEAD_SKIP_COMPETITOR_1` | T1: software house, agencja digital, web design, SEO, ads, hosting; confidence >=0.85 | `skip` | `SKIP` | 1 | 0.85 | Firma sama tworzy strony lub jest konkurencja. |
| `LEAD_SKIP_COMPETITOR_MANUAL_1` | T1: IT/digital hints confidence 0.65-0.84 | `manual_review` | `SKIP` | 2 | 0.65 | Integrator IT moze byc partnerem albo konkurencja. |
| `LEAD_SKIP_SMALL_1` | T0.5/T1/import: jednoosobowa mikro firma, niski lead_value <45, brak reklam/social, kontakt slaby | `skip` | `SKIP` | 5 | 0.70 | Drobna dzialalnosc bez widocznego budzetu. |
| `LEAD_SKIP_OUT_OF_SCOPE_1` | Branza poza MSP/B2B, czysty B2C niskobudzetowy lub portal/katalog/marketplace | `skip` | `SKIP` | 2 | 0.78 | Katalog firm albo prywatny blog. |
| `LEAD_SKIP_NO_HOOK_1` | Firma istnieje, strona dziala, SSL, szybka, RWD, CTA, analytics, T2 good | `skip` | `SKIP` | 5 | 0.82 | Brak uczciwego powodu do outreachu. |
| `LEAD_SKIP_NO_CONTACT_1` | Contactability <40 + lead_value <75 | `skip` | `SKIP` | 3 | 0.70 | Brak emaila, telefonu i formularza. |
| `LEAD_SKIP_PARKING_1` | Parking/NXDOMAIN + brak potwierdzonej firmy + brak kontaktu | `skip` | `SKIP` | 1 | 0.80 | Sama domena bez firmy. |

## 6. Progi scoringowe

### 6.1. Punktacja pomocnicza

```text
website_need_score =
  0.25 * company_existence
  + 0.20 * website_problem_strength
  + 0.15 * contactability
  + 0.15 * industry_fit
  + 0.10 * lead_value
  + 0.10 * conversion_waste
  + 0.05 * evidence_recency
  - penalties
```

| Skladnik | Skala | Przyklad |
|---|---:|---|
| `company_existence` | 0-100 | VAT active, NIP, JSON-LD, kontakt firmowy. |
| `website_problem_strength` | 0-100 | Brak strony, slaba/stara strona, wolno, brak RWD. |
| `conversion_waste` | 0-100 | Ads/pixel/social/ruch, ale slaby landing/CTA. |
| `contactability` | 0-100 | Email firmowy, formularz, telefon. |
| `industry_fit` | 0-100 | Polskie MSP B2B/uslugi/produkcja. |
| `lead_value` | 0-100 | Wielkosc, branza, zasieg, sygnaly budzetu. |

### 6.2. Kary i veto

| Warunek | Kara / efekt |
|---|---:|
| Brak potwierdzenia firmy | -15 i maks. `manual_review` dla new website. |
| Brak kontaktu | -20; przy contactability <40 zwykle `skip`. |
| T2 `visual:modern_good` | Veto dla redesign, chyba ze sa twarde problemy ads/performance. |
| Konkurencja/IT >=0.85 | Auto `skip`. |
| Strona w przebudowie | Auto `manual_review`, bez send. |
| Jedyny problem to brak analytics | Maks. `manual_review`. |
| Jedyny problem to WordPress | Maks. `manual_review`, zwykle `skip`. |
| Jedyny problem to brak SSL na pustej domenie | `skip`. |

## 7. Evidence requirements

| Kampania | Minimalne dowody do `send` | Co nie wystarcza |
|---|---|---|
| `NEW_WEBSITE_GMB_NO_SITE` | firma potwierdzona + brak strony/wlasnej domeny + kontakt | sama domena parkingowa |
| `NEW_WEBSITE_ACTIVE_COMPANY` | firma potwierdzona + brak www + fit/contact | import bez kontaktu i bez NIP |
| `REDESIGN_ADS_WASTE` | reklamy/pixel/landing + slaba strona/CTA/performance | sam GTM/pixel |
| `REDESIGN_OUTDATED_SITE` | stary/RWD/visual problem + firma/kontakt | sam brak meta description |
| `REDESIGN_CONVERSION_CTA` | brak CTA/formularza lub wolno + oferta/contact | sam wolny jednorazowy pomiar |
| `REDESIGN_TRUST_SECURITY` | trust/design issue + SSL/cert/form/privacy issue | sam brak HSTS/CSP |
| `REDESIGN_WP_REWORK` | WordPress + slaby visual/performance/maintenance risk | sam WordPress |
| `CUSTOM_WEBSITE_AUDIT` | dobry fit + kontakt + 2 neutralne obserwacje | automatyczny fallback bez QA |

## 8. Weryfikacja rulesetu

### 8.1. Reguly odrzucone lub zdegradowane

| Pomysl | Decyzja | Powod |
|---|---|---|
| "Brak DMARC/SPF" jako kampania glowna | Odrzucone | To nie sprzedaje strony WWW; moze byc tylko dodatkowa obserwacja. |
| "Brak HSTS/CSP" jako automatyczny send | Odrzucone | Zbyt techniczne i slabe biznesowo bez formularza/trust issue. |
| "WordPress = lead" | Odrzucone | WordPress sam w sobie nie oznacza potrzeby redesignu. |
| "Brak Google Analytics = lead" | Zdegradowane do manual | Brak analytics nie musi oznaczac problemu, szczegolnie bez reklam. |
| "Whois:no" jako hook | Odrzucone | Dla domen .pl to slaby i ryzykowny argument. |
| "Strona aktywna bez infra:modern" | Odrzucone | Nie jest widocznym problemem klienta. |
| "Jednorazowy timeout = strona nie dziala" | Odrzucone | Wymaga retry i drugiego dowodu. |

### 8.2. Sprawdzenie pokrycia danych T0/T1

| Typ reguly | Pokrycie T0/T1 | Status |
|---|---|---|
| Brak strony / parking / DNS | T0 | Automatyczne przy firmie potwierdzonej. |
| Firma istnieje / VAT active / NIP | T0.5/T1/import | Automatyczne, jesli dane sa dostepne; brak danych obniza confidence. |
| Kontakt email/telefon/formularz | T1/import | Automatyczne. |
| Stara strona przez brak viewport/table layout/meta | T0/T1 | Automatyczne tylko przy 2+ dowodach; inaczej manual. |
| Slaby wyglad / outdated design | T2 | Bez T2 tylko manual, chyba ze T0 ma twarde legacy sygnaly. |
| Reklamy Google/Facebook | T0/T1 przez GTM, pixel, UTM, landing hints | Dobre jako wzmacniacz; nie zawsze dowodzi aktywnej kampanii. |
| Brak GA/GTM | T0/T1 | Slaby samodzielny sygnal; tylko wzmacniacz. |
| Social aktywne | T1 wykrywa linki, nie aktywnosc po stronie social | Linki social jako sygnal umiarkowany; "aktywnosc" wymaga importu albo manual/T2. |
| Strona w przebudowie | T1 teksty, T0 staging/dev hints | Manual review, bo latwo o falszywy pozytyw. |

### 8.3. Korekty progow po weryfikacji

| Obszar | Korekta |
|---|---|
| New website | Podniesiono `send` do 0.76-0.80, bo brak strony bez potwierdzonej firmy generuje duzo smieci. |
| Ads waste | Podniesiono do 0.80, bo ads/pixel hints nie zawsze oznaczaja aktywny budzet. |
| Outdated site | 0.76 z T2 lub twardymi T0; bez T2 manual od 0.65. |
| WordPress rework | Sam WP nie daje send; wymagany drugi problem. |
| Analytics | Brak analytics nie daje send bez problemu konwersji albo reklam. |
| Skip good site | Ustalono veto przy T2 good + komplet T0, zeby nie wysylac bez hooka. |

## 9. Finalny zestaw decyzji operacyjnych

1. W MVP automatyczny `send` moze wyjsc tylko z regul opartych o T0/T0.5/T1 z minimum dwoma dowodami.
2. Reguly wymagajace oceny wizualnej sa `manual_review` do czasu pilota T2.
3. Kampanie techniczne nie istnieja jako glowne kampanie outreachowe; ich sygnaly podbijaja pilnosc redesignu.
4. `CUSTOM_WEBSITE_AUDIT` jest manualnym koszykiem dla dobrych leadow bez mocnego hooka.
5. Kazdy `send` musi miec `company_existence >=60`, `contactability >=55`, `industry_fit >=55` i co najmniej jeden dowod problemu strony.
6. Kazdy lead z konkurencji/digital/IT przy confidence >=0.85 jest suppression.
7. Kazda decyzja `skip` z powodu "strona dobra" musi miec pozytywne dowody, nie tylko brak bledow.

## 10. Przyklady calych scenariuszy

| Scenariusz | Sygnaly | Decyzja |
|---|---|---|
| Producent ma stara strone bez RWD, telefon i NIP | T0 active, no viewport, legacy HTML; T0.5 VAT active; T1 phone | `send` -> `REDESIGN_OUTDATED_SITE` |
| Firma z Google Maps bez strony | Import GMB, VAT active, phone, no domain | `send` -> `NEW_WEBSITE_GMB_NO_SITE` |
| Uslugodawca ma WP, ale szybki i nowoczesny | WP hints, SSL, fast, CTA, T2 good | `skip` |
| Firma ma Meta Pixel, wolna strone i slabe CTA | Pixel, speed slow, weak CTA, email | `send` -> `REDESIGN_ADS_WASTE` |
| Firma ma strone OK, tylko brak GA | Active, modern, no analytics | `manual_review` albo `skip`, nie send |
| Agencja SEO ma slaba strone | T1 competitor confidence 0.90 | `skip` suppression |
| Strona pokazuje "w budowie" | T1 construction phrase, firma fit | `manual_review` |
| Domena parkingowa bez NIP i kontaktu | Parking, no company evidence | `skip` |
