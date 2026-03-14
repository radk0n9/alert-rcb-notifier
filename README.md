# alert-rcb

Monitors the Polish Government Emergency Alert System ([RCB](https://www.gov.pl/web/rcb/komunikaty)) and sends new alerts to a Telegram group.

## How it works

1. Fetches the RCB alerts page, stopping as soon as all records on a page are already known
2. Inserts new records into a local SQLite database
3. Sends the latest new alert to Telegram (with photo and a link button)
4. Sleeps and repeats

## Requirements

- Docker + Docker Compose

## Setup

**On a fresh VPS (Ubuntu):**
```bash
bash scripts/setup-vps.sh
```
Installs Docker, creates directories, and walks you through `.env` configuration interactively.

**Manual setup:**
```bash
cp .env.example .env
nano .env   # fill in credentials
```

`.env` variables:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_GROUP_ID` | — | Target group chat ID |
| `TELEGRAM_GROUP_ID_TEST` | — | Test group chat ID (optional) |
| `CHECK_INTERVAL` | `1800` | Seconds between checks |
| `LOG_LEVEL` | `INFO` | Log level (`INFO`, `DEBUG`, etc.) |
| `LOG_FORMAT` | `rich` | `rich` (colored console) or `plain` |
| `LOG_ROTATE_DAYS` | `30` | Days of log history to keep |

## Run

```bash
# Start production
./scripts/run.sh

# Start test mode
./scripts/run.sh --test

# Follow logs
docker compose logs -f

# Stop
docker compose down

# Rebuild after code changes
./scripts/run.sh
```

## Test mode

Sends the latest DB record to `TELEGRAM_GROUP_ID_TEST` repeatedly on the configured interval. Useful for verifying Telegram delivery without waiting for a real alert. Sends a silent startup notification on launch.

```bash
./scripts/run.sh --test

# Follow logs
docker compose logs -f test

# Stop
docker compose --profile test down
```

## Logs

Saved to `./logs/alert-rcb.log`, rotated daily, kept for `LOG_ROTATE_DAYS` days.

```bash
tail -f logs/alert-rcb.log
```
