import logging
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class ContentParser:
    BASE_DOMAIN = "https://www.gov.pl"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_html(self, html: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        return self._extract_records(soup)

    def _extract_records(self, soup) -> list:
        records = []
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
            try:
                date_parsed = datetime.strptime(date, "%d.%m.%Y")
                iso_date = date_parsed.strftime("%Y-%m-%d")
            except ValueError:
                self.logger.warning("Unrecognized date format '%s', skipping record", date)
                continue

            records.append(
                {
                    "url": url,
                    "image_url": image,
                    "title": title,
                    "intro": intro,
                    "date": iso_date,
                }
            )

        return records
