import logging

import requests
from bs4 import BeautifulSoup


class SiteContent:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.url = "https://www.gov.pl/web/rcb/komunikaty"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def get_content(self):
        resposne = requests.get(self.url, headers=self.headers)
        resposne.raise_for_status()

        if resposne.status_code != 200:
            self.logger.warning(
                "Cannot acces provided website: '%s', status: %s", self.url, resposne.status_code
            )
            raise

        soup = BeautifulSoup(resposne.text, "html.parser")

        article = soup.find("article", class_="article-area__article")
        if not article:
            self.logger.warning("Unable to find article")
            return

        content = article.prettify()
        with open("article.html", "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info("Article save successfully")
