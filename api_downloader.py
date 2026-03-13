from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import aiohttp

from api_registry import ApiSource


logger = logging.getLogger(__name__)
DEFAULT_USER_AGENT = "luatools-v61-stplugin-hoe"


class DownloadError(Exception):
    pass


class ApiDownloader:
    def __init__(self, timeout_seconds: int = 15) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async def fetch_sanitized_game_name(self, appid: str) -> str:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us"
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise DownloadError(f"Gagal mengambil nama game appid={appid}: HTTP {response.status}")

                payload = await response.json(content_type=None)

        raw_name = self._extract_steam_app_name(payload, appid)
        sanitized_name = self._sanitize_game_name(raw_name)
        if not sanitized_name:
            raise DownloadError(f"Nama game untuk appid={appid} kosong setelah sanitasi")
        return sanitized_name

    async def download_game_zip(
        self,
        appid: str,
        destination_file: Path,
        sources: list[ApiSource],
    ) -> tuple[Path, str]:
        destination_file.parent.mkdir(parents=True, exist_ok=True)

        last_error: Exception | None = None
        attempts: list[str] = []
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            for index, source in enumerate(sources, start=1):
                url = source.build_url(appid)
                headers = self._build_headers(source)
                try:
                    logger.info(
                        "Mencoba API%s (%s) untuk appid=%s",
                        index,
                        source.name,
                        appid,
                    )
                    async with session.get(url, headers=headers) as response:
                        if response.status != source.success_code:
                            raise DownloadError(f"HTTP {response.status} dari {url}")

                        data = await response.read()
                        if not data:
                            raise DownloadError(f"Data kosong dari {url}")

                        destination_file.write_bytes(data)
                        logger.info("Download sukses appid=%s via API=%s", appid, source.name)
                        return destination_file, source.name
                except Exception as exc:
                    last_error = exc
                    attempts.append(f"{index}.{source.name}={exc}")
                    logger.warning(
                        "API gagal index=%s api=%s appid=%s url=%s error=%s",
                        index,
                        source.name,
                        appid,
                        url,
                        exc,
                    )

        attempts_summary = " | ".join(attempts)
        raise DownloadError(
            f"Semua API gagal untuk appid={appid}: {last_error}. Urutan percobaan: {attempts_summary}"
        )

    @staticmethod
    def _build_headers(source: ApiSource) -> dict[str, str]:
        if source.name.strip().lower() == "gamehub":
            return {}
        return {"User-Agent": DEFAULT_USER_AGENT}

    @staticmethod
    def _extract_steam_app_name(payload: object, appid: str) -> str:
        if not isinstance(payload, dict):
            raise DownloadError(f"Respons Steam appdetails tidak valid untuk appid={appid}")

        app_entry = payload.get(str(appid))
        if not isinstance(app_entry, dict) or not app_entry.get("success"):
            raise DownloadError(f"Steam appdetails tidak menemukan appid={appid}")

        data = app_entry.get("data")
        if not isinstance(data, dict):
            raise DownloadError(f"Data Steam appdetails kosong untuk appid={appid}")

        name = str(data.get("name", "")).strip()
        if not name:
            raise DownloadError(f"Nama game Steam kosong untuk appid={appid}")
        return name

    @staticmethod
    def _sanitize_game_name(name: str) -> str:
        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^A-Za-z0-9]+", "", ascii_name)
