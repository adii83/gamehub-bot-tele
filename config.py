from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    database_url: str
    admin_username: str
    admin_password: str
    session_secret: str
    telegram_mode: str
    public_base_url: str
    webhook_secret: str
    delivery_delete_hours: int
    used_ticket_retention_days: int
    add_game_tutorial_url: str
    bypass_tutorial_url: str
    bot_link: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_tls: bool
    api_json_path: Path
    base_dir: Path
    tools_dir: Path
    bypass_dir: Path
    builds_dir: Path
    temp_dir: Path
    logs_dir: Path
    addgame_path: Path
    bypass_template_zip: Path
    guide_text_path: Path
    log_level: str


def _parse_admin_ids(value: str) -> set[int]:
    if not value.strip():
        return set()
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def _choose_addgame_file(tools_dir: Path, override_name: str) -> Path:
    if override_name.strip():
        return tools_dir / override_name.strip()
    candidates = sorted([p for p in tools_dir.glob("*.exe") if p.is_file()])
    if not candidates:
        return tools_dir / "_Add_Game (RUN ADMINISTRATOR).exe"
    return candidates[0]


def _choose_bypass_template(bypass_dir: Path, override_name: str) -> Path:
    if override_name.strip():
        return bypass_dir / override_name.strip()
    candidates = sorted([p for p in bypass_dir.glob("*.zip") if p.is_file()])
    if not candidates:
        return bypass_dir / "Bypass.zip"
    return candidates[0]


def load_settings() -> Settings:
    base_dir = Path(__file__).resolve().parent
    tools_dir = base_dir / "tools"
    bypass_dir = base_dir / "bypass"
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN belum diatur")

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL belum diatur")

    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD belum diatur")

    session_secret = os.getenv("SESSION_SECRET", "").strip()
    if not session_secret:
        raise ValueError("SESSION_SECRET belum diatur")

    telegram_mode = os.getenv("TELEGRAM_MODE", "polling").strip().lower()
    if telegram_mode not in {"polling", "webhook"}:
        raise ValueError("TELEGRAM_MODE harus polling atau webhook")

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if telegram_mode == "webhook" and not public_base_url:
        raise ValueError("PUBLIC_BASE_URL belum diatur")

    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if telegram_mode == "webhook" and not webhook_secret:
        raise ValueError("TELEGRAM_WEBHOOK_SECRET belum diatur")

    settings = Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        database_url=database_url,
        admin_username=admin_username,
        admin_password=admin_password,
        session_secret=session_secret,
        telegram_mode=telegram_mode,
        public_base_url=public_base_url,
        webhook_secret=webhook_secret,
        delivery_delete_hours=int(os.getenv("DELIVERY_DELETE_HOURS", "24")),
        used_ticket_retention_days=int(os.getenv("USED_TICKET_RETENTION_DAYS", "7")),
        add_game_tutorial_url=os.getenv("ADD_GAME_TUTORIAL_URL", "").strip(),
        bypass_tutorial_url=os.getenv("BYPASS_TUTORIAL_URL", "").strip(),
        bot_link=os.getenv("BOT_LINK", "").strip(),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", "").strip(),
        smtp_from_name=os.getenv("SMTP_FROM_NAME", "GameHub Pluss").strip(),
        smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").strip().lower() == "true",
        api_json_path=base_dir / "api.json",
        base_dir=base_dir,
        tools_dir=tools_dir,
        bypass_dir=bypass_dir,
        builds_dir=base_dir / "builds",
        temp_dir=base_dir / "temp",
        logs_dir=base_dir / "logs",
        addgame_path=_choose_addgame_file(tools_dir, os.getenv("ADD_GAME_FILENAME", "")),
        bypass_template_zip=_choose_bypass_template(bypass_dir, os.getenv("BYPASS_TEMPLATE_FILENAME", "")),
        guide_text_path=base_dir / "BACA INI JIKA GAME GAK BISA MUNCUL.txt",
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
    return settings


def ensure_directories(settings: Settings) -> None:
    settings.tools_dir.mkdir(parents=True, exist_ok=True)
    settings.bypass_dir.mkdir(parents=True, exist_ok=True)
    settings.builds_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
