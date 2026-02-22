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

    def insert_alerts(self, records: list):

        if not records:
            return

        try:
            with self.get_connection() as connection:

                for record in records:
                    inserted = 0
                    ignored = 0

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
