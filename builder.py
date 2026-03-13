from __future__ import annotations

import logging
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from api_downloader import ApiDownloader
from api_registry import ApiRegistry
from config import Settings


logger = logging.getLogger(__name__)


class BuildError(Exception):
    pass


@dataclass(slots=True)
class BuildResult:
    output_zip: Path
    logs: list[str]


class PackageBuilder:
    def __init__(self, settings: Settings, downloader: ApiDownloader, api_registry: ApiRegistry) -> None:
        self.settings = settings
        self.downloader = downloader
        self.api_registry = api_registry

    async def build_ticket_package(
        self,
        ticket_code: str,
        appids: list[str],
        bypass: bool,
        bypass_cfg: str | None,
        api_mode: str,
        selected_api: str | None,
    ) -> BuildResult:
        ticket_dir = self.settings.builds_dir / ticket_code
        temp_ticket_dir = self.settings.temp_dir / ticket_code
        output_zip = ticket_dir / "GameHub.zip"
        build_logs: list[str] = []

        if ticket_dir.exists():
            shutil.rmtree(ticket_dir, ignore_errors=True)
        if temp_ticket_dir.exists():
            shutil.rmtree(temp_ticket_dir, ignore_errors=True)

        ticket_dir.mkdir(parents=True, exist_ok=True)
        temp_ticket_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files: list[Path] = []
        bypass_file: Path | None = None
        used_game_names: set[str] = set()

        try:
            sources = self._resolve_sources(api_mode=api_mode, selected_api=selected_api)
            source_names = ", ".join(x.name for x in sources)
            build_logs.append(f"Sumber API aktif: {source_names}")

            for appid in appids:
                game_zip_name = await self._build_game_zip_name(appid=appid, used_names=used_game_names)
                game_zip_path = temp_ticket_dir / game_zip_name
                _, used_api = await self.downloader.download_game_zip(
                    appid=appid,
                    destination_file=game_zip_path,
                    sources=sources,
                )
                downloaded_files.append(game_zip_path)
                build_logs.append(
                    f"Download appid {appid} berhasil lewat API: {used_api} -> {game_zip_path.name}"
                )

            if bypass:
                bypass_file = temp_ticket_dir / self.settings.bypass_template_zip.name
                self._build_bypass_zip(bypass_cfg=bypass_cfg, output_zip=bypass_file)
                build_logs.append("Bypass berhasil diproses")

            if not self.settings.addgame_path.exists():
                raise BuildError(
                    f"File Add Game tidak ditemukan di {self.settings.addgame_path}"
                )

            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in downloaded_files:
                    zf.write(file_path, arcname=file_path.name)
                if bypass_file is not None:
                    zf.write(bypass_file, arcname=bypass_file.name)
                zf.write(self.settings.addgame_path, arcname=self.settings.addgame_path.name)
                if self.settings.guide_text_path.exists():
                    zf.write(self.settings.guide_text_path, arcname=self.settings.guide_text_path.name)
                else:
                    build_logs.append("Peringatan: File panduan tidak ditemukan dan tidak diikutkan")

            logger.info("Build sukses ticket=%s output=%s", ticket_code, output_zip)
            build_logs.append("GameHub.zip final berhasil dibuat")
            return BuildResult(output_zip=output_zip, logs=build_logs)
        except Exception as exc:
            logger.exception("Build gagal ticket=%s error=%s", ticket_code, exc)
            shutil.rmtree(ticket_dir, ignore_errors=True)
            raise BuildError(str(exc)) from exc
        finally:
            shutil.rmtree(temp_ticket_dir, ignore_errors=True)

    def _build_bypass_zip(self, bypass_cfg: str | None, output_zip: Path) -> None:
        extract_dir = output_zip.parent / "bypass_extract"
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            if self.settings.bypass_template_zip.exists():
                with zipfile.ZipFile(self.settings.bypass_template_zip, "r") as template_zip:
                    template_zip.extractall(extract_dir)
            else:
                raise BuildError(
                    f"Template bypass tidak ditemukan di {self.settings.bypass_template_zip}"
                )

            cfg_content = self._normalize_bypass_cfg(bypass_cfg)
            cfg_path = self._find_gamefixer_cfg(extract_dir)
            cfg_path.write_text(cfg_content, encoding="utf-8")

            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in extract_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, arcname=str(path.relative_to(extract_dir)))
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

    @staticmethod
    def _normalize_bypass_cfg(value: str | None) -> str:
        raw = (value or "").replace(" ", "")
        if not raw:
            return ","
        parts = [x for x in raw.split(",") if x]
        if not parts:
            return ","
        return f"{','.join(parts)},"

    @staticmethod
    def _find_gamefixer_cfg(extract_dir: Path) -> Path:
        for path in extract_dir.rglob("gamefixer.cfg"):
            if path.is_file():
                return path
        return extract_dir / "gamefixer.cfg"

    def _resolve_sources(self, api_mode: str, selected_api: str | None):
        mode = api_mode.lower().strip()
        if mode == "manual":
            if not selected_api:
                raise BuildError("Mode API manual membutuhkan selected_api")
            return [self.api_registry.get_by_name(selected_api)]
        return self.api_registry.load_enabled()

    def delete_ticket_folder(self, ticket_code: str) -> None:
        ticket_dir = self.settings.builds_dir / ticket_code
        shutil.rmtree(ticket_dir, ignore_errors=True)

    async def _build_game_zip_name(self, appid: str, used_names: set[str]) -> str:
        try:
            base_name = await self.downloader.fetch_sanitized_game_name(appid)
        except Exception as exc:
            logger.warning("Gagal mengambil nama game Steam appid=%s: %s", appid, exc)
            base_name = f"APPID{appid}"

        unique_name = self._make_unique_name(base_name=base_name, appid=appid, used_names=used_names)
        used_names.add(unique_name)
        return f"{unique_name}.zip"

    @staticmethod
    def _make_unique_name(base_name: str, appid: str, used_names: set[str]) -> str:
        candidate = base_name or f"APPID{appid}"
        if candidate not in used_names:
            return candidate

        fallback = f"{candidate}{appid}"
        if fallback not in used_names:
            return fallback

        suffix = 2
        while True:
            numbered = f"{fallback}{suffix}"
            if numbered not in used_names:
                return numbered
            suffix += 1
