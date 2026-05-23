# T0/T0.5/T1/T2 Lead Scoring Dashboard

Lekki dashboard operacyjny dla pipeline lead scoring. Dziala jako statyczny frontend serwowany przez prosty backend z biblioteki standardowej Pythona.

## Uruchomienie

```bash
cd /tmp/codex-review/dashboard
python3 backend.py
```

Otworz:

```text
http://localhost:8080
```

Alternatywnie bez `backend.py`:

```bash
cd /tmp/codex-review/dashboard
python3 -m http.server 8080
```

## Pliki

- `index.html` - struktura dashboardu i widoki.
- `style.css` - ciemny, responsywny UI.
- `app.js` - filtrowanie, QA workflow, wykresy, eksport CSV i import feedbacku.
- `backend.py` - prosty serwer HTTP.
- `data/sample-batch.json` - dane demo: batch, 60 leadow, alerty, eksporty, feedback kampanii.

## Widoki

- `Dashboard` - statystyki batcha, progress, alerty, wykresy i ostatnie decyzje.
- `QA workflow` - lista leadow, filtry, szczegoly leada, sygnaly, evidence i akcje QA.
- `Kampanie` - tabela kampanii, avg confidence, reply rate i lista leadow kampanii.
- `Eksport` - eksport CSV aktualnego batcha i import feedback CSV.
- `Batch` - historia batchy i wybor aktywnego batcha.

## Feedback CSV

Import akceptuje CSV z kolumnami typu:

```csv
domain,email,event
metalformpro.pl,biuro@metalformpro.pl,reply
```

Eksport CSV jest generowany w przegladarce dla leadow `send` oraz `approved`, z pominieciem suppression i reject.
