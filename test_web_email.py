from __future__ import annotations

import os
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

os.environ.update(
    {
        "BOT_TOKEN": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk",
        "DATABASE_URL": "postgresql://localhost/test",
        "ADMIN_PASSWORD": "password",
        "SESSION_SECRET": "secret",
        "TELEGRAM_MODE": "polling",
    }
)

resend = ModuleType("resend")
resend.api_key = None
resend.Emails = SimpleNamespace(send=lambda params: {"id": "email_test"})
sys.modules.setdefault("resend", resend)

import web_app


class AdminEmailTests(unittest.IsolatedAsyncioTestCase):
    async def test_created_ticket_survives_email_delivery_failure(self) -> None:
        request = SimpleNamespace(session={"is_admin": True})

        with (
            patch.object(web_app.ticket_service, "list_recent_tickets", AsyncMock(return_value=[])),
            patch.object(web_app.ticket_service, "create_ticket", AsyncMock(return_value=SimpleNamespace(ticket_code="ABC12345"))),
            patch.object(web_app.api_registry, "load_enabled", return_value=[]),
            patch.object(web_app.email_service, "send_ticket_email", side_effect=RuntimeError("Resend unavailable")),
        ):
            response = await web_app.admin_create_ticket(
                request=request,
                appids="570",
                bypass="false",
                bypass_cfg="",
                api_mode="auto",
                selected_api="",
                customer_email="user@example.com",
            )

        self.assertEqual(response.status_code, 303)
        self.assertIn("Ticket berhasil dibuat: ABC12345", unquote(response.headers["location"]))
        self.assertIn("Email gagal dikirim", unquote(response.headers["location"]))


if __name__ == "__main__":
    unittest.main()
