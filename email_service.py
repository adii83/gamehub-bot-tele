from __future__ import annotations

import html

import resend

from config import Settings


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(self.settings.resend_api_key and self.settings.bot_link)

    def send_ticket_email(self, recipient_email: str, ticket_code: str) -> None:
        if not self.is_configured():
            raise ValueError("RESEND_API_KEY atau BOT_LINK belum lengkap di .env")

        resend.api_key = self.settings.resend_api_key
        resend.Emails.send(
            {
                "from": "NexaPlay <order@nexaplayid.store>",
                "reply_to": "nexaplayid@gmail.com",
                "to": [recipient_email],
                "subject": "Pesanan NexaPlay Anda Siap 🎉",
                "text": self._build_body(ticket_code),
                "html": self._build_html(ticket_code),
            }
        )

    def _build_body(self, ticket_code: str) -> str:
        return (
            "Pesanan Anda siap 🎉\n"
            "Terima kasih telah berbelanja di NexaPlay.\n\n"
            "KODE LISENSI / TIKET ANDA:\n"
            f"{ticket_code}\n\n"
            "LANGKAH PENGGUNAAN:\n"
            "1. Buka bot Telegram NexaPlay melalui link berikut.\n"
            f"{self.settings.bot_link}\n"
            "2. Tempel kode lisensi di atas ke bot.\n"
            "3. Ikuti tutorial yang dikirim bot sampai selesai.\n\n"
            "Gabung Discord NexaPlay:\n"
            "https://discord.gg/x4kmK3JMm\n\n"
            "🎮 UPDATE GAME TERBARU\n"
            "Lihat informasi dan update game terbaru NexaPlay melalui website resmi kami:\n"
            "https://nexaplayid.store\n\n"
            "📌 PENTING: Ikuti tutorial sampai tuntas agar proses instalasi berjalan lancar.\n\n"
            "🛟 BUTUH BANTUAN?\n"
            "Jika mengalami kendala, silakan hubungi admin Shopee NexaPlay secara langsung.\n\n"
            "Salam hangat,\n"
            "Tim NexaPlay\n"
        )

    def _build_html(self, ticket_code: str) -> str:
        safe_ticket = html.escape(ticket_code)
        safe_bot_link = html.escape(self.settings.bot_link, quote=True)
        discord_link = "https://discord.gg/x4kmK3JMm"
        return f"""\
<!doctype html>
<html lang="id">
  <body style="margin:0;padding:0;background:#f3f4f6;color:#1f2937;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;">
            <tr>
              <td style="background:#111827;padding:28px 30px;color:#ffffff;">
                <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:#a78bfa;">NEXAPLAY</div>
                <h1 style="margin:10px 0 5px;font-size:24px;line-height:1.25;">Pesanan Anda siap 🎉</h1>
                <p style="margin:0;color:#d1d5db;font-size:13px;">Terima kasih telah berbelanja di NexaPlay.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 30px;">
                <p style="margin:0 0 20px;font-size:14px;line-height:1.7;">Berikut kode lisensi dan panduan untuk mulai menggunakan NexaPlay.</p>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:24px;background:#f5f3ff;border:1px solid #c4b5fd;border-radius:12px;">
                  <tr><td align="center" style="padding:18px;">
                    <div style="font-size:11px;font-weight:700;color:#6d28d9;letter-spacing:.6px;">🔑 KODE LISENSI</div>
                    <div style="margin-top:10px;font-family:Consolas,Monaco,monospace;font-size:22px;font-weight:700;letter-spacing:1.5px;color:#111827;">{safe_ticket}</div>
                    <div style="margin-top:9px;font-size:11px;color:#6b7280;">Gunakan Kode Lisensi ini pada BOT Telegram dibawah.</div>
                  </td></tr>
                </table>

                <h2 style="margin:0 0 8px;font-size:16px;">🤖 Mulai melalui Telegram</h2>
                <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#4b5563;">Buka bot NexaPlay, tempel kode lisensi, lalu ikuti tutorial yang dikirim sampai selesai.</p>
                <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom:26px;"><tr><td style="background:#7c3aed;border-radius:8px;"><a href="{safe_bot_link}" style="display:inline-block;padding:12px 18px;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;">Buka Bot Telegram</a></td></tr></table>

                <h2 style="margin:0 0 8px;font-size:16px;">👾 Info dan komunitas</h2>
                <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#4b5563;">Gabung Discord NexaPlay untuk memperoleh informasi terbaru.</p>
                <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom:26px;"><tr><td style="background:#4f46e5;border-radius:8px;"><a href="{discord_link}" style="display:inline-block;padding:12px 18px;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;">Gabung Discord</a></td></tr></table>

                <h2 style="margin:0 0 8px;font-size:16px;">🎮 Update Game Terbaru</h2>
                <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#4b5563;">Lihat informasi dan update game terbaru NexaPlay melalui website resmi kami.</p>
                <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom:26px;"><tr><td style="background:#7c3aed;border-radius:8px;"><a href="https://nexaplayid.store" style="display:inline-block;padding:12px 18px;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;">Kunjungi NexaPlay</a></td></tr></table>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;"><tr><td style="padding:15px;font-size:12px;line-height:1.6;color:#92400e;"><strong>📌 Penting</strong><br>Ikuti tutorial sampai tuntas agar proses instalasi dan penggunaan berjalan lancar.<div style="margin-top:12px;padding-top:12px;border-top:1px solid #fcd34d;"><strong>🛟 Butuh Bantuan?</strong><br>Jika mengalami kendala, silakan hubungi admin Shopee NexaPlay secara langsung.</div></td></tr></table>

                <p style="margin:28px 0 0;font-size:13px;line-height:1.7;color:#4b5563;">Semoga pengalaman gaming Anda bersama NexaPlay makin menyenangkan!</p>
                <p style="margin:16px 0 0;font-size:13px;line-height:1.6;">Salam hangat,<br><strong>Tim NexaPlay</strong><br><span style="color:#7c3aed;">Game Your Way</span></p>
              </td>
            </tr>
            <tr><td align="center" style="padding:15px 20px;background:#f9fafb;border-top:1px solid #e5e7eb;font-size:10px;color:#9ca3af;">Email ini dikirim terkait pembelian lisensi NexaPlay Anda.</td></tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
