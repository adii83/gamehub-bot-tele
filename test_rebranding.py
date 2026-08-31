from __future__ import annotations

import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

class FakeResendEmails:
    sent_params = None

    @classmethod
    def send(cls, params):
        cls.sent_params = params
        return {"id": "email_test"}


resend = ModuleType("resend")
resend.api_key = None
resend.Emails = FakeResendEmails
sys.modules.setdefault("resend", resend)

from builder import PackageBuilder
from config import load_settings
from email_service import EmailService


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
    def test_ticket_email_uses_verified_sender_and_gmail_reply_to(self) -> None:
        settings = SimpleNamespace(
            resend_api_key="re_test_key",
            bot_link="https://t.me/nexaplay_bot",
        )

        EmailService(settings).send_ticket_email("user@example.com", "ABC123")

        params = FakeResendEmails.sent_params
        self.assertIsNotNone(params)
        self.assertEqual(resend.api_key, "re_test_key")
        self.assertEqual(params["from"], "NexaPlay <order@nexaplayid.store>")
        self.assertEqual(params["reply_to"], "nexaplayid@gmail.com")
        self.assertEqual(params["to"], ["user@example.com"])
        self.assertEqual(params["subject"], "Pesanan NexaPlay Anda Siap 🎉")

        plain_body = params["text"]
        html_body = params["html"]

        self.assertIn("ABC123", plain_body)
        self.assertIn("https://t.me/nexaplay_bot", plain_body)
        self.assertIn("https://discord.gg/x4kmK3JMm", plain_body)
        self.assertIn("UPDATE GAME TERBARU", plain_body)
        self.assertIn("https://nexaplayid.store", plain_body)
        self.assertIn("hubungi admin Shopee NexaPlay secara langsung", plain_body)
        self.assertIn("Pesanan Anda siap", html_body)
        self.assertIn("ABC123", html_body)
        self.assertIn("Buka Bot Telegram", html_body)
        self.assertIn("Gabung Discord", html_body)
        self.assertIn("https://t.me/nexaplay_bot", html_body)
        self.assertIn("https://discord.gg/x4kmK3JMm", html_body)
        self.assertIn("🎮 Update Game Terbaru", html_body)
        self.assertIn('href="https://nexaplayid.store"', html_body)
        self.assertIn("Kunjungi NexaPlay", html_body)
        self.assertIn("🛟 Butuh Bantuan?", html_body)
        self.assertIn("hubungi admin Shopee NexaPlay secara langsung", html_body)
        self.assertNotIn("GameHub", plain_body + html_body)
        self.assertNotIn("ADD_GAME_TUTORIAL_URL", plain_body + html_body)

    def test_ticket_email_requires_resend_api_key(self) -> None:
        settings = SimpleNamespace(
            resend_api_key="",
            bot_link="https://t.me/nexaplay_bot",
        )

        with self.assertRaisesRegex(ValueError, "RESEND_API_KEY atau BOT_LINK belum lengkap di .env"):
            EmailService(settings).send_ticket_email("user@example.com", "ABC123")

    def test_settings_load_resend_api_key(self) -> None:
        env = {
            "BOT_TOKEN": "token",
            "DATABASE_URL": "postgresql://localhost/test",
            "ADMIN_PASSWORD": "password",
            "SESSION_SECRET": "secret",
            "RESEND_API_KEY": "re_test_key",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()

        self.assertEqual(settings.resend_api_key, "re_test_key")


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
