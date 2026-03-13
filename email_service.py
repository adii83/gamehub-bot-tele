from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import Settings


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return all(
            [
                self.settings.smtp_host,
                self.settings.smtp_username,
                self.settings.smtp_password,
                self.settings.smtp_from_email,
                self.settings.bot_link,
            ]
        )

    def send_ticket_email(self, recipient_email: str, ticket_code: str) -> None:
        if not self.is_configured():
            raise ValueError("SMTP atau BOT_LINK belum lengkap di .env")

        message = EmailMessage()
        message["Subject"] = "GameHub Pluss"
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = recipient_email
        message.set_content(self._build_body(ticket_code))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
            if self.settings.smtp_use_tls:
                server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(message)

    def _build_body(self, ticket_code: str) -> str:
        return (
            "Terima kasih telah berbelanja di GameHub! 🎉\n\n"
            "LANGKAH PERTAMA (WAJIB):\n"
            "MOHON MENAMBAHKAN BOT TELEGRAM VERIFIKASI KAMI:\n"
            f"{self.settings.bot_link}\n\n"
            "================================\n"
            "KODE LISENSI / TIKET ANDA:\n"
            f"{ticket_code}\n"
            "================================\n\n"
            "PANDUAN MENAMBAHKAN GAME KE STEAM:\n"
            "1. Buka chat dengan bot di link di atas\n"
            "2. Tempel (Paste) kode di atas ke sana.\n"
            "3. Sistem akan otomatis memberikan Tutorial Panduannya.\n"
            "Pastikan tonton tutorialya sampai habis biar gak erorr.\n\n"
            "Terima Kasih.\n"
        )
