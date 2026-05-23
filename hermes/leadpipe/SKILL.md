# Leadpipe Hermes Skill

Skill obsluguje komendy Telegrama przekazywane przez Hermesa do pipeline leadow na VM.

## Konfiguracja

- Repozytorium: `/opt/leadpipe`
- Virtualenv: `/opt/leadpipe/.venv`
- Env file: `/opt/leadpipe/.env`
- Dane pipeline: `${PIPELINE_DATA_DIR:-/mnt/hermes-free/lead-pipeline}`
- Importy CSV: `${PIPELINE_DATA_DIR}/imports`
- Eksporty CSV: `${PIPELINE_DATA_DIR}/exports`
- Logi: `${PIPELINE_DATA_DIR}/logs`
- Raporty: `${PIPELINE_DATA_DIR}/reports`

Przed kazda komenda:

```bash
cd /opt/leadpipe
set -a
. /opt/leadpipe/.env
set +a
. /opt/leadpipe/.venv/bin/activate
mkdir -p "$PIPELINE_DATA_DIR"/{imports,exports,logs,reports,snapshots}
```

## /leadpipe scan leads.csv --batch test-001 --layers t0,t1,t0_5

Cel: zaimportowac CSV i uruchomic skan wskazanych warstw.

```bash
cp leads.csv "$PIPELINE_DATA_DIR/imports/leads.csv"
leadpipe import "$PIPELINE_DATA_DIR/imports/leads.csv" --source telegram --batch test-001 \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-import.log"
leadpipe scan --batch test-001 --layers t0,t1,t0_5 --concurrency 10 \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-scan.log"
```

Odpowiedz w Telegramie: podaj batch id, liczbe zaimportowanych leadow i sciezke logu.

## /leadpipe decide --batch test-001

Cel: przeliczyc bramki, kampanie, suppression i decyzje.

```bash
leadpipe decide --batch test-001 \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-decide.log"
```

Odpowiedz w Telegramie: pokaz liczby `send`, `manual`, `skip`, `retry` i link/sciezke do raportu, jezeli CLI go zwroci.

## /leadpipe report --batch test-001

Cel: wygenerowac raport operacyjny batcha.

```bash
leadpipe report --batch test-001 --output "$PIPELINE_DATA_DIR/reports/test-001.md" \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-report.log"
```

Odpowiedz w Telegramie: wklej krotkie podsumowanie i sciezke `${PIPELINE_DATA_DIR}/reports/test-001.md`.

## /leadpipe qa --batch test-001

Cel: podsumowac ile rekordow wymaga QA.

```bash
leadpipe qa --batch test-001 \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-qa.log"
```

Odpowiedz w Telegramie: podaj liczbe leadow do QA, ile jest `manual`, ile wymaga T2 i ile ma brakujace evidence.

## /leadpipe export --batch test-001

Cel: wyeksportowac zatwierdzone leady do CSV.

```bash
leadpipe export --batch test-001 --format csv --output "$PIPELINE_DATA_DIR/exports/test-001.csv" \
  2>&1 | tee -a "$PIPELINE_DATA_DIR/logs/test-001-export.log"
```

Odpowiedz w Telegramie: podaj link albo sciezke do CSV: `${PIPELINE_DATA_DIR}/exports/test-001.csv`.

## Zasady obslugi bledow

- Jezeli komenda zwroci kod inny niz 0, odpowiedz `FAIL` i pokaz ostatnie 20 linii logu.
- Jezeli CSV eksportu nie istnieje albo ma tylko naglowek, odpowiedz `FAIL: pusty eksport`.
- Jezeli brakuje `.env`, odpowiedz `FAIL: brak /opt/leadpipe/.env`.
- Nie wysylaj kluczy API ani pelnego `.env` w Telegramie.
