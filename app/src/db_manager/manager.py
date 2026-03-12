import logging
import os
import sqlite3

from src.tools.utils import set_directory_path


class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_directory = set_directory_path("db")
        self.db_path = os.path.join(self.db_directory, "alertrcb.db")

        os.makedirs(self.db_directory, exist_ok=True)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):

        self.logger.info("Attempting to initialize database")

        if os.path.exists(self.db_path):
            self.logger.info("Database existing: '%s'. Skipping initialization", self.db_path)
            return

        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alertrcb (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            date TEXT NOT NULL,
                            intro TEXT,
                            url TEXT NOT NULL UNIQUE,
                            image_url TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                            )
                    """
                )
            self.logger.info("Successfully created database - '%s'", self.db_path)

        except Exception as e:
            self.logger.warning("Some problem occurred during process: %s", e)

    def get_latest_record(self) -> dict | None:
        try:
            with self.get_connection() as connection:
                cursor = connection.execute(
                    "SELECT title, date, intro, url, image_url FROM alertrcb ORDER BY date DESC LIMIT 1"
                )
                row = cursor.fetchone()
        except sqlite3.Error as e:
            self.logger.error("Database error while fetching latest record: %s", e)
            return None

        if not row:
            return None

        return {"title": row[0], "date": row[1], "intro": row[2], "url": row[3], "image_url": row[4]}

    def filter_new_records(self, records: list) -> list:
        urls = [r["url"] for r in records if r]

        if not urls:
            return []

        placeholders = ",".join("?" * len(urls))

        try:
            with self.get_connection() as connection:
                cursor = connection.execute(
                    f"SELECT url FROM alertrcb WHERE url IN ({placeholders})", urls
                )
                existing_urls = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            self.logger.error("Database error while filtering records: %s", e)
            return records

        new_records = [r for r in records if r and r["url"] not in existing_urls]
        self.logger.debug("Records on page: %d, new: %d", len(records), len(new_records))
        return new_records

    def insert_alerts(self, records: list):

        if not records:
            return

        try:
            with self.get_connection() as connection:
                inserted = 0
                ignored = 0

                for record in records:
                    if not record:
                        continue

                    self.logger.debug("Inserting record: %s", record)

                    cursor = connection.execute(
                        """
                        INSERT OR IGNORE INTO alertrcb
                        (title, date, intro, url, image_url)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            record["title"],
                            record["date"],
                            record["intro"],
                            record["url"],
                            record["image_url"],
                        ),
                    )
                    if cursor.rowcount == 1:
                        inserted += 1
                    else:
                        ignored += 1

                self.logger.info("Inserted: %s, Ignored: %s", inserted, ignored)
        except sqlite3.Error as e:
            self.logger.error("Database error: %s", e)
