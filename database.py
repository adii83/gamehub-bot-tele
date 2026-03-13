from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import asyncpg


CREATE_TICKETS_SQL = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_code TEXT PRIMARY KEY,
    appid_list TEXT NOT NULL,
    bypass BOOLEAN NOT NULL,
    bypass_cfg TEXT,
    api_mode TEXT NOT NULL DEFAULT 'auto',
    selected_api TEXT,
    file_path TEXT NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_chat_id BIGINT,
    delivery_message_id BIGINT,
    delivery_delete_at TIMESTAMP,
    delivery_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP
);
"""


MIGRATION_SQL = [
    "ALTER TABLE tickets ALTER COLUMN expires_at DROP NOT NULL",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS bypass_cfg TEXT",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS api_mode TEXT NOT NULL DEFAULT 'auto'",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS selected_api TEXT",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS delivery_chat_id BIGINT",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS delivery_message_id BIGINT",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS delivery_delete_at TIMESTAMP",
    "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS delivery_deleted BOOLEAN NOT NULL DEFAULT FALSE",
]


@dataclass(slots=True)
class TicketRow:
    ticket_code: str
    appid_list: str
    bypass: bool
    bypass_cfg: str | None
    api_mode: str
    selected_api: str | None
    file_path: str
    used: bool
    delivery_chat_id: int | None
    delivery_message_id: int | None
    delivery_delete_at: datetime | None
    delivery_deleted: bool
    created_at: datetime
    expires_at: datetime | None


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=10)
        async with self.pool.acquire() as conn:
            await conn.execute(CREATE_TICKETS_SQL)
            for stmt in MIGRATION_SQL:
                await conn.execute(stmt)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()

    async def create_ticket(
        self,
        ticket_code: str,
        appid_list: str,
        bypass: bool,
        bypass_cfg: str | None,
        api_mode: str,
        selected_api: str | None,
        file_path: str,
        created_at: datetime,
        expires_at: datetime | None,
    ) -> None:
        assert self.pool is not None
        query = """
        INSERT INTO tickets (
            ticket_code, appid_list, bypass, bypass_cfg, api_mode, selected_api,
            file_path, used, created_at, expires_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE, $8, $9)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                ticket_code,
                appid_list,
                bypass,
                bypass_cfg,
                api_mode,
                selected_api,
                file_path,
                created_at,
                expires_at,
            )

    async def get_ticket(self, ticket_code: str) -> TicketRow | None:
        assert self.pool is not None
        query = "SELECT * FROM tickets WHERE ticket_code = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, ticket_code)
        if row is None:
            return None
        return TicketRow(**dict(row))

    async def mark_ticket_used(self, ticket_code: str) -> None:
        assert self.pool is not None
        query = "UPDATE tickets SET used = TRUE WHERE ticket_code = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(query, ticket_code)

    async def set_delivery_info(
        self,
        ticket_code: str,
        chat_id: int,
        message_id: int,
        delete_at: datetime,
    ) -> None:
        assert self.pool is not None
        query = """
        UPDATE tickets
        SET delivery_chat_id = $2,
            delivery_message_id = $3,
            delivery_delete_at = $4,
            delivery_deleted = FALSE
        WHERE ticket_code = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, ticket_code, chat_id, message_id, delete_at)

    async def get_due_delivery_deletes(self, now: datetime) -> list[TicketRow]:
        assert self.pool is not None
        query = """
        SELECT * FROM tickets
        WHERE delivery_deleted = FALSE
          AND delivery_chat_id IS NOT NULL
          AND delivery_message_id IS NOT NULL
          AND delivery_delete_at IS NOT NULL
          AND delivery_delete_at <= $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, now)
        return [TicketRow(**dict(r)) for r in rows]

    async def mark_delivery_deleted(self, ticket_code: str) -> None:
        assert self.pool is not None
        query = "UPDATE tickets SET delivery_deleted = TRUE WHERE ticket_code = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(query, ticket_code)

    async def list_recent_tickets(self, limit: int = 50) -> list[TicketRow]:
        assert self.pool is not None
        query = "SELECT * FROM tickets ORDER BY created_at DESC LIMIT $1"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [TicketRow(**dict(r)) for r in rows]

    async def get_expired_unused_tickets(self, now: datetime) -> list[TicketRow]:
        assert self.pool is not None
        query = "SELECT * FROM tickets WHERE used = FALSE AND expires_at IS NOT NULL AND expires_at < $1"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, now)
        return [TicketRow(**dict(r)) for r in rows]

    async def ticket_exists(self, ticket_code: str) -> bool:
        assert self.pool is not None
        query = "SELECT 1 FROM tickets WHERE ticket_code = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, ticket_code)
        return row is not None

    async def delete_used_tickets_before(self, cutoff: datetime) -> int:
        assert self.pool is not None
        query = "DELETE FROM tickets WHERE used = TRUE AND created_at < $1"
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, cutoff)
        # asyncpg execute result format: "DELETE <count>"
        return int(result.split()[-1])
