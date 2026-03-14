import html
import logging
import os

import requests


class TelegramNotifier:
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, test: bool = False):
        self.logger = logging.getLogger(__name__)
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.group_id = os.getenv("TELEGRAM_GROUP_ID_TEST" if test else "TELEGRAM_GROUP_ID")

    def send(self, record: dict) -> bool:
        if not self.token or not self.group_id:
            self.logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_ID not configured in .env")
            return False

        message = self._format_message(record)
        reply_markup = self._build_reply_markup(record["url"])

        if record.get("image_url"):
            return self._send_photo(record["image_url"], message, reply_markup)

        return self._send_message(message, reply_markup)
    
    def send_status(self) -> bool:
        if not self.token or not self.group_id:
            self.logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_ID not configured in .env")
            return False
        url = self.BASE_URL.format(token=self.token, method="sendMessage")
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.group_id,
                    "text": "✅ alert-rcb started",
                    "parse_mode": "HTML",
                    "disable_notification": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Status message sent")
            return True
        except requests.RequestException as e:
            body = e.response.text if e.response is not None else "no response"
            self.logger.error("Failed to send status message: %s | response: %s", e, body)
            return False



    def _build_reply_markup(self, url: str) -> dict:
        return {
            "inline_keyboard": [
                [
                    {"text": "Czytaj więcej", "url": url},
                    {"text": "RCB", "url": "https://www.gov.pl/web/rcb/komunikaty"},
                ]
            ]
        }

    def _send_photo(self, image_url: str, caption: str, reply_markup: dict) -> bool:
        url = self.BASE_URL.format(token=self.token, method="sendPhoto")
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.group_id,
                    "photo": image_url,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                    "protect_content": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Telegram message with photo sent")
            return True
        except requests.RequestException as e:
            body = e.response.text if e.response is not None else "no response"
            self.logger.error("Failed to send Telegram photo: %s | response: %s", e, body)
            self.logger.info("Falling back to text message")
            return self._send_message(caption, reply_markup)

    def _send_message(self, message: str, reply_markup: dict) -> bool:
        url = self.BASE_URL.format(token=self.token, method="sendMessage")
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.group_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                    "protect_content": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Telegram message sent")
            return True
        except requests.RequestException as e:
            body = e.response.text if e.response is not None else "no response"
            self.logger.error("Failed to send Telegram message: %s | response: %s", e, body)
            return False

    def _format_message(self, record: dict) -> str:
        lines = [
            f"<i>{html.escape(record['date'])}</i>",
            f"<b>{html.escape(record['title'])}</b>",
        ]

        if record.get("intro"):
            intro = record["intro"]
            if len(intro) > 300:
                intro = intro[:300] + "…"
            lines.append(f"\n{html.escape(intro)}")

        return "\n".join(lines)
