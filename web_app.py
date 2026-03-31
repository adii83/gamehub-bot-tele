from __future__ import annotations

import asyncio
import logging
import re
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, Update, BufferedInputFile
from urllib.parse import quote, unquote

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from api_downloader import ApiDownloader
from api_registry import ApiRegistry
from builder import PackageBuilder
from config import ensure_directories, load_settings
from database import Database
from email_service import EmailService
from ticket_service import TicketService


TICKET_REGEX = re.compile(r"^[A-Z0-9]{8}$")


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        handlers=[
            logging.FileHandler("logs/bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _normalize_appids(raw: str) -> list[str]:
    appids = [x.strip() for x in raw.split(",") if x.strip()]
    if not appids:
        raise ValueError("AppID wajib diisi")
    if any(not x.isdigit() for x in appids):
        raise ValueError("AppID harus numerik dipisah koma")
    return appids


def _is_logged_in(request: Request) -> bool:
    return bool(request.session.get("is_admin"))


def _redirect_login() -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=303)


settings = load_settings()
ensure_directories(settings)
setup_logging(settings.log_level)
logger = logging.getLogger("web_app")

app = FastAPI(title="GameHub Admin + Bot")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    max_age=60 * 60 * 24 * 30,
)
templates = Jinja2Templates(directory=str(settings.base_dir / "templates"))


db = Database(settings.database_url)
api_registry = ApiRegistry(settings.api_json_path)
downloader = ApiDownloader()
builder = PackageBuilder(settings=settings, downloader=downloader, api_registry=api_registry)
ticket_service = TicketService(db=db, builder=builder, delivery_delete_hours=settings.delivery_delete_hours)
email_service = EmailService(settings)

bot = Bot(
    token=settings.bot_token,
    session=AiohttpSession(timeout=120),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


WELCOME_MESSAGE = (
    "🎉 Terima kasih telah berbelanja di GameHub!\n\n"
    "Silakan kirimkan kodenya di sini.\n\n"
    "📌 Cara mengirim:\n"
    "1. Buka email Anda.\n"
    "2. Salin (Copy) kode Tiket / Lisensi yang Anda terima.\n"
    "3. Tempel (Paste) kode tersebut di sini.\n\n"
    "⚠️ Penting:\n"
    "Jangan lupa tonton tutorialnya sampai selesai agar proses berjalan lancar dan tidak terjadi error."
)


@dp.message(Command("start"))
async def on_start(message: Message) -> None:
    await message.answer(WELCOME_MESSAGE)


@dp.message(F.text)
async def on_any_text(message: Message) -> None:
    text = (message.text or "").strip().upper()
    if not TICKET_REGEX.fullmatch(text):
        return

    ticket = await ticket_service.get_redeemable_ticket(text)
    if ticket is None:
        await message.answer("Ticket tidak valid atau sudah dipakai.")
        return

    await message.answer("⚠️ PERHATIAN: File akan otomatis terhapus dalam 24 Jam")

    if ticket.bypass:
        first_appid = ticket.appid_list.split(",", 1)[0].strip()
        game_name = f"APPID {first_appid}" if first_appid else "ini"
        if first_appid:
            try:
                game_name = await downloader.fetch_game_name(first_appid)
            except Exception as exc:
                logger.warning(
                    "Gagal mengambil nama game untuk bypass appid=%s error=%s",
                    first_appid,
                    exc,
                )
        await message.answer(
            f"⚠️ PERHATIAN: Game {game_name} Membutuhkan Bypass Untuk bisa dijalankan. "
            "Setelah Game Berhasil Diinstall Harap tonton video Tutorial Bypass Game Dibawah."
        )

    links_text = [f"Link Tutorial Add Game:\n{settings.add_game_tutorial_url}"]
    if ticket.bypass:
        links_text.append(f"Link Tutorial Bypass Game:\n{settings.bypass_tutorial_url}")
    await message.answer("\n\n".join(links_text))

    try:
        # Read file into memory first to avoid flaky disk/stream transport issues.
        with open(ticket.file_path, "rb") as f:
            file_data = f.read()

        document = BufferedInputFile(file_data, filename="GameHub.zip")

        sent = await message.answer_document(
            document=document,
            caption="Silahkan download Setup Tersebut\n\nPassword File: gamehub",
        )

        await ticket_service.set_delivery_message(
            ticket_code=ticket.ticket_code,
            chat_id=message.chat.id,
            message_id=sent.message_id,
        )
        await ticket_service.finalize_redeem(ticket.ticket_code)
    except FileNotFoundError:
        await message.answer("File untuk ticket ini tidak ditemukan. Hubungi admin.")
    except Exception as exc:
        logger.exception("Gagal kirim file ticket=%s error=%s", ticket.ticket_code, exc)
        await message.answer("Terjadi error saat mengirim file. Coba lagi nanti.")


async def delivery_cleanup_worker() -> None:
    last_used_cleanup = datetime.utcnow() - timedelta(hours=2)
    while True:
        try:
            now = datetime.utcnow()
            due_rows = await ticket_service.get_due_delivery_deletes()
            for row in due_rows:
                if row.delivery_chat_id is None or row.delivery_message_id is None:
                    await ticket_service.mark_delivery_deleted(row.ticket_code)
                    continue
                try:
                    await bot.delete_message(
                        chat_id=row.delivery_chat_id,
                        message_id=row.delivery_message_id,
                    )
                except Exception as exc:
                    logger.warning("Gagal hapus pesan file ticket=%s error=%s", row.ticket_code, exc)
                finally:
                    await ticket_service.mark_delivery_deleted(row.ticket_code)

            if now - last_used_cleanup >= timedelta(hours=1):
                deleted_count = await ticket_service.cleanup_used_tickets(
                    settings.used_ticket_retention_days
                )
                last_used_cleanup = now
                if deleted_count > 0:
                    logger.info(
                        "Cleanup ticket used: %s baris dihapus (retensi=%s hari)",
                        deleted_count,
                        settings.used_ticket_retention_days,
                    )
        except Exception as exc:
            logger.exception("Error delivery cleanup worker: %s", exc)

        await asyncio.sleep(60)


@app.on_event("startup")
async def on_startup() -> None:
    await db.connect()
    if settings.telegram_mode == "webhook":
        webhook_url = f"{settings.public_base_url}/telegram/webhook"
        await bot.set_webhook(url=webhook_url, secret_token=settings.webhook_secret, drop_pending_updates=False)
        logger.info("Startup selesai. Webhook aktif di %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=False)
        app.state.polling_task = asyncio.create_task(dp.start_polling(bot))
        logger.info("Startup selesai. Telegram berjalan di mode polling untuk testing lokal")
    app.state.cleanup_task = asyncio.create_task(delivery_cleanup_worker())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    task = getattr(app.state, "cleanup_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    polling_task = getattr(app.state, "polling_task", None)
    if polling_task:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task
    if settings.telegram_mode == "webhook":
        await bot.delete_webhook(drop_pending_updates=False)
    await db.close()
    await bot.session.close()


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    secret = request.headers.get("x-telegram-bot-api-secret-token", "")
    if secret != settings.webhook_secret:
        return {"ok": False}

    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/favicon.png")
async def favicon():
    return FileResponse(str(settings.base_dir / "templates" / "favicon.png"), media_type="image/png")


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == settings.admin_username and password == settings.admin_password:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Username atau password salah"},
        status_code=401,
    )


@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return _redirect_login()


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not _is_logged_in(request):
        return _redirect_login()

    raw_flash = request.query_params.get("flash", "")
    flash = unquote(raw_flash) if raw_flash else None
    tickets = await ticket_service.list_recent_tickets()
    apis = api_registry.load_enabled()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tickets": tickets,
            "apis": apis,
            "flash": flash,
            "error": None,
            "build_logs": None,
        },
    )


@app.post("/admin/tickets/create", response_class=HTMLResponse)
async def admin_create_ticket(
    request: Request,
    appids: str = Form(...),
    bypass: str = Form("false"),
    bypass_cfg: str = Form(""),
    api_mode: str = Form("auto"),
    selected_api: str = Form(""),
    customer_email: str = Form(""),
):
    if not _is_logged_in(request):
        return _redirect_login()

    tickets = await ticket_service.list_recent_tickets()
    apis = api_registry.load_enabled()

    try:
        parsed_appids = _normalize_appids(appids)
        bypass_bool = bypass.strip().lower() == "true"
        mode = api_mode.strip().lower()
        if mode not in {"auto", "manual"}:
            raise ValueError("api_mode harus auto/manual")
        if mode == "manual" and not selected_api.strip():
            raise ValueError("selected_api wajib diisi saat mode manual")

        result = await ticket_service.create_ticket(
            appids=parsed_appids,
            bypass=bypass_bool,
            bypass_cfg=bypass_cfg,
            api_mode=mode,
            selected_api=selected_api.strip() or None,
            created_by=settings.admin_username,
        )

        email_status = None
        if customer_email.strip():
            email_service.send_ticket_email(customer_email.strip(), result.ticket_code)
            email_status = f" Ticket juga berhasil dikirim ke email: {customer_email.strip()}"

        flash = f"Ticket berhasil dibuat: {result.ticket_code}"
        if email_status:
            flash += email_status
        return RedirectResponse(url=f"/admin?flash={quote(flash)}", status_code=303)
    except Exception as exc:
        logger.exception("Gagal create ticket via admin web: %s", exc)
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "tickets": tickets,
                "apis": apis,
                "flash": None,
                "error": str(exc),
                "build_logs": None,
            },
            status_code=400,
        )
