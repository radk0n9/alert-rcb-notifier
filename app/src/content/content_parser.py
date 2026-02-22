import logging
import os
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from src.tools.utils import set_directory_path


class ContentParser:
    BASE_DOMAIN = "https://www.gov.pl"

    def __init__(
        self,
        data_directory: str = "data",
    ):
        self.logger = logging.getLogger(__name__)
        self.data_directory = set_directory_path(data_directory)

    def parse_all_articles(self):
        records = []

        for filename in sorted(os.listdir(self.data_directory)):
            if not filename.endswith(".html"):
                continue

            article_path = os.path.join(self.data_directory, filename)
            parsed_articles = self.parse_article(article_path)

            records.extend(parsed_articles)

        return records

    def parse_article(self, article: str):
        records = []

        with open(article, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        items = soup.find_all("li")

        for item in items:
            link_tag = item.find("a")
            image_tag = item.find("img")
            date_tag = item.find("span", class_="date")
            title_tag = item.find("div", class_="title")
            intro_tag = item.find("div", class_="intro")

            if not title_tag or not date_tag or not link_tag:
                continue

            url = urljoin(self.BASE_DOMAIN, str(link_tag["href"]))
            image = urljoin(self.BASE_DOMAIN, str(image_tag["src"])) if image_tag else None
            title = title_tag.text.strip()
            intro = intro_tag.text.strip() if intro_tag else None

            date = date_tag.text.strip()
            date_parsed = datetime.strptime(date, "%d.%m.%Y")
            iso_date = date_parsed.strftime("%Y-%m-%d")

            record = {
                "url": url,
                "image_url": image,
                "title": title,
                "intro": intro,
                "date": iso_date,
            }

            records.append(record)

        return records
