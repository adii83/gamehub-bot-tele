# Telegram GameHub Bot (VPS Mode)

Sistem ini menjalankan:
- Bot Telegram user (redeem ticket) via webhook
- Admin web panel (buat ticket + pilih API + bypass config)
- Build GameHub.zip per-ticket
- Auto hapus pesan file Telegram setelah 24 jam

## Arsitektur VPS

- Satu aplikasi FastAPI: `web_app.py`
- PostgreSQL untuk data ticket
- Folder lokal untuk build/package

## Struktur Penting

```text
bot.py                       # launcher uvicorn
web_app.py                   # admin web + telegram webhook
config.py
database.py
ticket_service.py
builder.py
api_downloader.py
api_registry.py
api.json
BACA INI JIKA GAME GAK BISA MUNCUL.txt

/tools                        # taruh file exe Add Game asli
/bypass                       # taruh file zip bypass template asli
/builds
/temp
/logs
/templates
```

## Kebutuhan Runtime

- Python 3.11 atau 3.12 (disarankan)
- PostgreSQL
- Domain HTTPS yang mengarah ke VPS (untuk webhook Telegram)

## Setup

1. Copy `.env.example` menjadi `.env`
2. Isi semua variabel pada `.env`
3. Pastikan file berikut ada:
   - `tools/<nama exe asli>`
   - `bypass/<nama zip bypass asli>`
   - `api.json`
   - `BACA INI JIKA GAME GAK BISA MUNCUL.txt`
4. Install dependency:

```bash
pip install -r requirements.txt
```

5. Jalankan aplikasi:

```bash
python bot.py
```

Server akan berjalan di port `8000`.

## Yang Wajib Diganti Di .env

- `BOT_TOKEN`: token bot dari BotFather
- `ADMIN_PASSWORD`: password login admin web
- `SESSION_SECRET`: string acak panjang untuk session web
- `TELEGRAM_MODE`: pakai `polling` untuk test lokal, `webhook` untuk VPS
- `PUBLIC_BASE_URL`: isi domain HTTPS hanya saat mode webhook
- `TELEGRAM_WEBHOOK_SECRET`: isi secret hanya saat mode webhook
- `ADD_GAME_TUTORIAL_URL`: link tutorial Add Game YouTube/halaman Anda
- `BYPASS_TUTORIAL_URL`: link tutorial bypass
- `BOT_LINK`: link bot Telegram Anda, contoh `https://t.me/nama_bot_anda`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`: isi jika ingin kirim ticket otomatis via email dari admin web
- `ADD_GAME_FILENAME`: nama file exe asli di folder `tools`
- `BYPASS_TEMPLATE_FILENAME`: nama file zip bypass asli di folder `bypass`

## Testing Lokal

Untuk testing lokal, gunakan konfigurasi berikut:

- `TELEGRAM_MODE=polling`
- `PUBLIC_BASE_URL` boleh dikosongkan
- `TELEGRAM_WEBHOOK_SECRET` boleh dikosongkan

Langkah test lokal:

1. Siapkan Python 3.11 atau 3.12
2. Install PostgreSQL dan buat database
3. Isi `.env`
4. Taruh file aset di folder:
  - `tools/<nama exe asli>`
  - `bypass/<nama zip bypass asli>`
5. Jalankan app:

```bash
python bot.py
```

6. Buka admin web di:

```text
http://127.0.0.1:8000/admin/login
```

7. Login dengan `ADMIN_USERNAME` dan `ADMIN_PASSWORD`
8. Buat ticket dari dashboard
9. Jika bot Telegram aktif dan token benar, kirim kode ticket ke bot di Telegram untuk test redeem

## Endpoint

- `GET /admin/login` -> login admin
- `GET /admin` -> dashboard admin
- `POST /admin/tickets/create` -> create ticket
- `POST /telegram/webhook` -> endpoint webhook Telegram

## Fitur Utama Yang Sudah Sesuai Requirement

- Ticket valid selamanya sampai dipakai
- Admin bisa pilih API mode:
  - `auto` -> fallback urut sesuai `api.json` dari atas ke bawah
  - `manual` -> pakai 1 API yang dipilih
- Bypass edit `gamefixer.cfg` otomatis tambah koma terakhir
- Nama file bypass dan add game mengikuti nama asli file sumber
- Selalu include `BACA INI JIKA GAME GAK BISA MUNCUL.txt` ke `GameHub.zip`
- Urutan pesan user saat redeem:
  1. Peringatan auto-hapus 24 jam
  2. Peringatan bypass (jika diperlukan)
  3. Link tutorial Add Game (+ link bypass jika diperlukan)
  4. Kirim file dengan caption: `Silahkan download Setup Tersebut`
- Pesan peringatan/tutorial tidak dihapus
- Hanya pesan file yang dihapus otomatis setelah 24 jam

## Catatan

Jika dependency gagal di Python 3.14, gunakan Python 3.11/3.12 di VPS agar paket aiogram/fastapi stack lebih stabil.
