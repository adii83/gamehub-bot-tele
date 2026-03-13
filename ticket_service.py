from __future__ import annotations

import asyncio
import logging
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from builder import BuildResult, PackageBuilder
from database import Database, TicketRow


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TicketCreateResult:
    ticket_code: str
    file_path: str
    build_logs: list[str]


class TicketService:
    def __init__(self, db: Database, builder: PackageBuilder, delivery_delete_hours: int = 24) -> None:
        self.db = db
        self.builder = builder
        self.delivery_delete_hours = delivery_delete_hours
        self._locks: dict[str, asyncio.Lock] = {}

    async def create_ticket(
        self,
        appids: list[str],
        bypass: bool,
        bypass_cfg: str | None,
        api_mode: str,
        selected_api: str | None,
        created_by: str | None = None,
    ) -> TicketCreateResult:
        if not appids:
            raise ValueError("appid_list tidak boleh kosong")

        ticket_code = await self._generate_unique_ticket_code()
        build_result: BuildResult = await self.builder.build_ticket_package(
            ticket_code=ticket_code,
            appids=appids,
            bypass=bypass,
            bypass_cfg=bypass_cfg,
            api_mode=api_mode,
            selected_api=selected_api,
        )

        now = datetime.utcnow()
        appid_list_str = ",".join(appids)

        await self.db.create_ticket(
            ticket_code=ticket_code,
            appid_list=appid_list_str,
            bypass=bypass,
            bypass_cfg=bypass_cfg,
            api_mode=api_mode,
            selected_api=selected_api,
            file_path=str(build_result.output_zip),
            created_at=now,
            expires_at=None,
        )

        logger.info(
            "ticket created code=%s appids=%s bypass=%s api_mode=%s selected_api=%s created_by=%s",
            ticket_code,
            appid_list_str,
            bypass,
            api_mode,
            selected_api,
            created_by,
        )
        return TicketCreateResult(
            ticket_code=ticket_code,
            file_path=str(build_result.output_zip),
            build_logs=build_result.logs,
        )

    async def get_redeemable_ticket(self, ticket_code: str) -> TicketRow | None:
        lock = self._locks.setdefault(ticket_code, asyncio.Lock())
        async with lock:
            ticket = await self.db.get_ticket(ticket_code)
            if ticket is None:
                return None

            if ticket.used:
                return None

            if not Path(ticket.file_path).exists():
                logger.warning("File ticket tidak ditemukan code=%s path=%s", ticket.ticket_code, ticket.file_path)
                return None

            return ticket

    async def finalize_redeem(self, ticket_code: str) -> None:
        lock = self._locks.setdefault(ticket_code, asyncio.Lock())
        async with lock:
            await self.db.mark_ticket_used(ticket_code)
            self.builder.delete_ticket_folder(ticket_code)
            logger.info("ticket redeemed code=%s", ticket_code)

    async def set_delivery_message(self, ticket_code: str, chat_id: int, message_id: int) -> None:
        delete_at = datetime.utcnow() + timedelta(hours=self.delivery_delete_hours)
        await self.db.set_delivery_info(
            ticket_code=ticket_code,
            chat_id=chat_id,
            message_id=message_id,
            delete_at=delete_at,
        )

    async def get_due_delivery_deletes(self) -> list[TicketRow]:
        return await self.db.get_due_delivery_deletes(datetime.utcnow())

    async def mark_delivery_deleted(self, ticket_code: str) -> None:
        await self.db.mark_delivery_deleted(ticket_code)

    async def list_recent_tickets(self, limit: int = 50) -> list[TicketRow]:
        return await self.db.list_recent_tickets(limit=limit)

    async def cleanup_used_tickets(self, retention_days: int) -> int:
        if retention_days <= 0:
            return 0
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        return await self.db.delete_used_tickets_before(cutoff)

    async def _generate_unique_ticket_code(self) -> str:
        for _ in range(100):
            candidate = self._generate_ticket_code()
            if not await self.db.ticket_exists(candidate):
                return candidate
        raise RuntimeError("Gagal menghasilkan ticket unik")

    @staticmethod
    def _generate_ticket_code() -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choices(alphabet, k=8))
