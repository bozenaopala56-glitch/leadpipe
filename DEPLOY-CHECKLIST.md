# Deploy Checklist

Docelowa VM: Ubuntu 22.04. Zakladana sciezka aplikacji: `/opt/leadpipe`.

## Krok 1: Zainstaluj Dockera

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv python3-pip
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Wyloguj sie i zaloguj ponownie, zeby grupa `docker` zaczela dzialac.

## Krok 2: docker compose up -d (Postgres + Redis)

Na swiezej VM najpierw pobierz repo, bo `docker-compose.yml` jest w katalogu projektu.

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin leadpipe || true
sudo mkdir -p /opt/leadpipe
sudo chown "$USER":"$USER" /opt/leadpipe
git clone <REPO_URL> /opt/leadpipe
cd /opt/leadpipe
docker compose up -d
docker compose ps
```

## Krok 3: git clone + pip install -e .

```bash
cd /opt/leadpipe
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e ".[postgres,csv,test]"
sudo chown -R leadpipe:leadpipe /opt/leadpipe /mnt/hermes-free 2>/dev/null || true
```

## Krok 4: playwright install chromium

```bash
cd /opt/leadpipe
. .venv/bin/activate
pip install playwright
playwright install chromium
```

## Krok 5: skopiuj .env.example -> .env i uzupelnij klucze

```bash
cd /opt/leadpipe
cp .env.example .env
mkdir -p /mnt/hermes-free/lead-pipeline/{imports,exports,logs,reports,snapshots}
sudo chown -R leadpipe:leadpipe /mnt/hermes-free/lead-pipeline
$EDITOR .env
```

Minimum do uzupelnienia: `POSTGRES_DSN`, `REDIS_URL`, `OPENCODE_GO_API_KEY`, `PIPELINE_DATA_DIR`, `USER_AGENT`.

## Krok 6: systemd dla dashboardu

```bash
sudo cp /opt/leadpipe/deploy/leadpipe-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now leadpipe-dashboard.service
sudo systemctl status leadpipe-dashboard.service
```

Dashboard slucha domyslnie na `127.0.0.1:8080`. Logi:

```bash
journalctl -u leadpipe-dashboard.service -f
```

## Krok 7: cron/timer dla periodic scan

```bash
sudo cp /opt/leadpipe/deploy/leadpipe-scan.service /etc/systemd/system/
sudo cp /opt/leadpipe/deploy/leadpipe-scan.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now leadpipe-scan.timer
systemctl list-timers leadpipe-scan.timer
```

Reczne uruchomienie:

```bash
sudo systemctl start leadpipe-scan.service
journalctl -u leadpipe-scan.service -f
```

## Krok 8: zainstaluj skill Hermesa

```bash
mkdir -p "$CODEX_HOME/skills/leadpipe"
cp /opt/leadpipe/hermes/leadpipe/SKILL.md "$CODEX_HOME/skills/leadpipe/SKILL.md"
```

Po instalacji komendy Telegrama obslugiwane przez Hermesa:

```text
/leadpipe scan leads.csv --batch test-001 --layers t0,t1,t0_5
/leadpipe decide --batch test-001
/leadpipe report --batch test-001
/leadpipe qa --batch test-001
/leadpipe export --batch test-001
```

## Krok 9: smoke test

```bash
cd /opt/leadpipe
deploy/smoke-test.sh
```

Oczekiwany wynik koncowy:

```text
SMOKE OK
```

## Krok 10: gotowe

Sprawdz:

```bash
docker compose ps
systemctl status leadpipe-dashboard.service
systemctl list-timers leadpipe-scan.timer
ls -la /mnt/hermes-free/lead-pipeline
```
