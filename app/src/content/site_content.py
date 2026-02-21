import logging
import os
from time import sleep
from typing import Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.models import Response
from src.tools.utils import set_directory_path


class SiteContent:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.url = "https://www.gov.pl/web/rcb/komunikaty"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.data_directory = set_directory_path("data")

    def get_content(self, filename: str | None = None):

        filename = filename or "article1.html"
        file = os.path.join(self.data_directory, filename)

        if os.path.exists(file):
            self.logger.info("File already exists, skipping download")
            total_pages = self.get_total_pages(file)
            if total_pages:
                self.logger.info("More pages to download...")
                self.download_all_pages(total_pages)
            return

        response = self.send_request(self.url)

        if not os.path.exists(self.data_directory):
            os.makedirs("data", exist_ok=True)

        if response.status_code != 200:
            self.logger.warning(
                "Cannot acces provided website: '%s', status: %s", self.url, response.status_code
            )
            raise

        article = self.find_article(response)

        if not article:
            self.logger.warning("Article not found, skipping saving")
            return

        content = article.prettify()
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info("Article save successfully")

    def get_total_pages(self, file) -> int:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        total_pages_tag = soup.find("a", class_="pagination__total-count")

        if not total_pages_tag:
            self.logger.warning("Pagination not found!")
            return 1

        total_pages = int(total_pages_tag.text)
        self.logger.info("Detected %s total pages", total_pages)

        return total_pages

    def find_article(self, response: Response) -> Optional[Tag]:
        soup = BeautifulSoup(response.text, "html.parser")

        article = soup.find("article", class_="article-area__article")
        if not article:
            self.logger.warning("Unable to find article")
            return
        return article

    def send_request(self, url: str) -> Response:
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()

        return response

    def download_all_pages(self, total_pages: int):

        for page in range(2, total_pages + 1):
            url = f"{self.url}/?page={page}&size=10"
            file = os.path.join(self.data_directory, f"article{page}.html")

            if os.path.exists(file):
                self.logger.info("File '%s' aleready exists, skipping", file)
                continue

            self.logger.debug("Downloading page %d", page)

            response = self.send_request(url)

            article = self.find_article(response)

            if not article:
                self.logger.warning("Article not found, skipping saving")
                return

            content = article.prettify()
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
