# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2026-03-12
### Added
- Telegram notifications via `src/notifier/telegram.py`
  - Sends photo + caption when `image_url` is present, falls back to text message on photo failure
  - `--test` CLI flag - sends latest DB record to `TELEGRAM_GROUP_ID_TEST` without scraping
  - Separate `TELEGRAM_GROUP_ID` / `TELEGRAM_GROUP_ID_TEST` env vars
  - HTML escaping on title and intro to prevent Telegram API rejections
- `DatabaseManager.get_latest_record()` — returns most recent alert by date
- `.env.example` with all required variables documented
- `load_env()` wired into `main.py` as the first call

### Fixed
- `SiteContent.fetch_page()` now catches `requests.RequestException` — network errors no longer crash the script
- `ContentParser._extract_records()` catches `ValueError` on date parsing — malformed dates skip the record, the rest of the page continues
- `TelegramNotifier._send_photo()` falls back to `_send_message()` on failure — alerts are never silently lost

### Changed
- Replaced file-based HTML caching with DB-driven early-stop pagination
  - `SiteContent`: removed `download_all()` and file saving methods; added `fetch_page(page)` returning HTML string directly
  - `ContentParser`: removed file-based parsing; added `parse_html(html)` to parse from string
  - `DatabaseManager`: added `filter_new_records()` — queries DB for known URLs before inserting
  - `main.py`: new pagination loop — stops as soon as a page contains zero new records
- Removed dependency on `data/` directory for normal operation

## 2026-02-19
### Added
- Fetching HTML content from URL to file
- HTML article parsing with BeautifulSoup
- SQLite database initialization and record insertion

## 2026-02-11
### Added
- Logging (Rich console handler + timestamped file handler)
- CLI argument parser (`-l`, `-lo` flags)
- isort and Black configuration in `pyproject.toml`
- Environment variable loading via `python-dotenv`

## 2026-01-24
### Added
- Python code formatter (Black)
