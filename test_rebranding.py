from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.modules.setdefault("aiohttp", ModuleType("aiohttp"))
dotenv = ModuleType("dotenv")
dotenv.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv)

from builder import PackageBuilder
from email_service import EmailService


class FakeSMTP:
    sent_message = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        pass

    def starttls(self) -> None:
        pass

    def login(self, username: str, password: str) -> None:
        pass

    def send_message(self, message) -> None:
        FakeSMTP.sent_message = message


class FakeDownloader:
    async def fetch_sanitized_game_name(self, appid: str) -> str:
        return f"Game{appid}"

    async def download_game_zip(self, appid: str, destination_file: Path, sources):
        with zipfile.ZipFile(destination_file, "w") as archive:
            archive.writestr("manifest.txt", appid)
        return destination_file, sources[0].name


class FakeRegistry:
    def load_enabled(self):
        return [SimpleNamespace(name="Primary")]


class RebrandingTests(unittest.TestCase):
    def test_ticket_email_uses_nexaplay_brand(self) -> None:
        settings = SimpleNamespace(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="bot@example.com",
            smtp_password="secret",
            smtp_from_email="bot@example.com",
            smtp_from_name="NexaPlay",
            smtp_use_tls=True,
            bot_link="https://t.me/nexaplay_bot",
        )

        with patch("email_service.smtplib.SMTP", FakeSMTP):
            EmailService(settings).send_ticket_email("user@example.com", "ABC123")

        message = FakeSMTP.sent_message
        self.assertIsNotNone(message)
        self.assertEqual(message["Subject"], "Pesanan NexaPlay Anda Siap 🎉")
        self.assertIsNotNone(message["Date"])
        self.assertIsNotNone(message["Message-ID"])
        self.assertTrue(message.is_multipart())

        plain_body = message.get_body(preferencelist=("plain",)).get_content()
        html_body = message.get_body(preferencelist=("html",)).get_content()

        self.assertIn("ABC123", plain_body)
        self.assertIn("https://t.me/nexaplay_bot", plain_body)
        self.assertIn("https://discord.gg/x4kmK3JMm", plain_body)
        self.assertIn("Pesanan Anda siap", html_body)
        self.assertIn("ABC123", html_body)
        self.assertIn("Buka Bot Telegram", html_body)
        self.assertIn("Gabung Discord", html_body)
        self.assertIn("https://t.me/nexaplay_bot", html_body)
        self.assertIn("https://discord.gg/x4kmK3JMm", html_body)
        self.assertNotIn("GameHub", plain_body + html_body)
        self.assertNotIn("ADD_GAME_TUTORIAL_URL", plain_body + html_body)


class PackageRebrandingTests(unittest.IsolatedAsyncioTestCase):
    async def test_ticket_package_uses_nexaplay_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            addgame = root / "AddGame.exe"
            addgame.write_bytes(b"tool")
            guide = root / "guide.txt"
            guide.write_text("guide", encoding="utf-8")
            settings = SimpleNamespace(
                builds_dir=root / "builds",
                temp_dir=root / "temp",
                addgame_path=addgame,
                guide_text_path=guide,
                bypass_template_zip=root / "Bypass.zip",
            )
            builder = PackageBuilder(settings, FakeDownloader(), FakeRegistry())

            result = await builder.build_ticket_package(
                ticket_code="ABC123",
                appids=["570"],
                bypass=False,
                bypass_cfg=None,
                api_mode="auto",
                selected_api=None,
            )

            self.assertEqual(result.output_zip.name, "NexaPlay.zip")
            self.assertTrue(result.output_zip.is_file())


if __name__ == "__main__":
    unittest.main()
