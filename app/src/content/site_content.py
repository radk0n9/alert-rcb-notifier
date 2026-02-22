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
    DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(
        self,
        url: str,
        data_directory: str = "data",
        headers: Optional[dict] = None,
        page_size: int = 10,
    ):
        self.logger = logging.getLogger(__name__)
        self.url = url.rstrip("/")
        self.headers = headers or self.DEFAULT_HEADERS
        self.data_directory = set_directory_path(data_directory)
        self.page_size = page_size

        os.makedirs(self.data_directory, exist_ok=True)

    def download_all(self) -> None:

        first_page_path = self._build_file_path("article1.html")

        if not os.path.exists(first_page_path):
            self.logger.info("Downloading first page")
            response = self.send_request(self.url)
            article = self.find_article(response)

            if not article:
                self.logger.warning("Article not found, skipping saving")
                return

            self._save_article(article, first_page_path)
        else:
            self.logger.info("First page already exists!")

        total_pages = self._get_total_pages(first_page_path)

        if not total_pages:
            return

        self.logger.info("Detected %d pages. Downloading remaining pages...", total_pages)
        for page in range(2, total_pages + 1):
            filename = f"article{page}.html"
            file_path = self._build_file_path(filename=filename)

            if os.path.exists(file_path):
                self.logger.info("File '%s' aleready exists, skipping", file_path)
                continue

            url = f"{self.url}?page={page}&size={self.page_size}"
            self.logger.debug("Downloading page %d", page)

            response = self.send_request(url)

            article = self.find_article(response)

            if not article:
                self.logger.warning("Article not found, skipping saving")
                return

            self._save_article(article, file_path)

    def _get_total_pages(self, file_path: str) -> int:

        if not os.path.exists(file_path):
            self.logger.warning("Cannot detect pagination. File does not exists!")
            return 1

        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        total_pages_tag = soup.find("a", class_="pagination__total-count")

        if not total_pages_tag:
            self.logger.warning("Pagination not found!")
            return 1

        try:
            total_pages = int(total_pages_tag.text)
            return total_pages
        except ValueError as e:
            self.logger.warning("Invalid pagination value. Assuming 1 page, error: %s", e)
            return 1

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

    def _build_file_path(self, filename: str) -> str:
        return os.path.join(self.data_directory, filename)

    def _save_article(self, article: Tag, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(article.prettify())

        self.logger.info("Article save successfully: '%s'", file_path)
