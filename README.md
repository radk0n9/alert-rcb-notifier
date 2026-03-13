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

```bash
cp .env.example .env
# fill in your credentials
nano .env
```

`.env` variables:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_GROUP_ID` | — | Target group chat ID |
| `TELEGRAM_GROUP_ID_TEST` | — | Test group chat ID (Optional) |
| `CHECK_INTERVAL` | `1800` | Seconds between checks |
| `LOG_LEVEL` | `INFO` | Log level (`INFO`, `DEBUG`, etc.) |
| `LOG_FORMAT` | `rich` | `rich` (colored console) or `plain` |
| `LOG_ROTATE_DAYS` | `30` | Days of log history to keep |

## Run

```bash
# Start
docker compose up -d

# Follow logs
docker compose logs -f

# Stop
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

## Test mode

Sends the latest DB record to the test Telegram group repeatedly on the configured interval. Useful for verifying Telegram delivery without waiting for a real alert.

```bash
docker compose --profile test up -d test
```

## Logs

Saved to `./logs/alert-rcb.log`, rotated daily, old files named `alert-rcb.log.YYYY-MM-DD`.

```bash
tail -f logs/alert-rcb.log
```
