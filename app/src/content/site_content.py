import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.models import Response


class SiteContent:
    DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(
        self,
        url: str,
        headers: Optional[dict] = None,
        page_size: int = 10,
    ):
        self.logger = logging.getLogger(__name__)
        self.url = url.rstrip("/")
        self.headers = headers or self.DEFAULT_HEADERS
        self.page_size = page_size

    def fetch_page(self, page: int = 1) -> Optional[str]:
        url = self.url if page == 1 else f"{self.url}?page={page}&size={self.page_size}"
        self.logger.info("Fetching page %d", page)

        try:
            response = self.send_request(url)
        except requests.RequestException as e:
            self.logger.error("Failed to fetch page %d: %s", page, e)
            return None

        article = self.find_article(response)

        if not article:
            return None

        return article.prettify()

    def find_article(self, response: Response) -> Optional[Tag]:
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article", class_="article-area__article")

        if not article:
            self.logger.warning("Unable to find article")
            return None

        return article

    def send_request(self, url: str) -> Response:
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response
