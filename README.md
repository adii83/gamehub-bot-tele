# Telegram NexaPlay Bot — Panduan Production VPS

Panduan ini mendokumentasikan deployment production yang sudah berhasil digunakan end-to-end.

Sistem menjalankan:

- Bot Telegram untuk redeem ticket melalui webhook
- Panel admin FastAPI untuk membuat ticket dan memilih API/bypass
- Build `NexaPlay.zip` per ticket
- Pengiriman email melalui Resend
- Penghapusan otomatis pesan file Telegram setelah 24 jam

## Kondisi Production Terverifikasi

| Komponen | Nilai final |
|---|---|
| VPS | Ubuntu 24.04, `103.103.20.78` |
| SSH user | `nexaplay` |
| Project | `/home/nexaplay/telegram_bot_nexaplay` |
| Python app | `bot.py`, FastAPI/Uvicorn di `127.0.0.1:8000` |
| Service | `nexaplay-telegram.service` |
| PostgreSQL | PostgreSQL 16, `127.0.0.1:5432` |
| Database | `nexaplay_bot` |
| Database user | `nexaplay_user` |
| Domain | `https://tele.nexaplayid.store` |
| Webhook | `https://tele.nexaplayid.store/telegram/webhook` |
| Panel admin | `https://tele.nexaplayid.store/admin/login` |
| HTTPS | Certbot / Let's Encrypt |
| Swap | `/swapfile`, 2 GB |

Production sudah membuktikan kondisi berikut bekerja:

- Nginx aktif dan meneruskan request ke `127.0.0.1:8000`
- PostgreSQL cluster online
- HTTPS aktif dan Certbot auto-renew aktif
- Panel admin dapat dibuka
- `getWebhookInfo` menghasilkan `ok=true`
- `POST /telegram/webhook` menghasilkan HTTP 200
- Telegram menerima, memproses, dan redeem ticket
- Service berstatus `enabled` dan `active (running)`
- Service otomatis hidup setelah VPS reboot

## Pemisahan Bot

Telegram dipisahkan dari bot lain agar folder, dependency, `.env`, dan service tidak bercampur:

```text
/home/nexaplay/
├── telegram_bot_nexaplay/
└── discord_bot_nexaplay/
```

Service yang digunakan:

```text
nexaplay-telegram.service
nexaplay-discord.service
```

Panduan ini hanya mengelola bot Telegram.

## Struktur Project Telegram

```text
/home/nexaplay/telegram_bot_nexaplay/
├── bot.py
├── web_app.py
├── config.py
├── database.py
├── ticket_service.py
├── builder.py
├── api_downloader.py
├── api_registry.py
├── email_service.py
├── api.json
├── requirements.txt
├── .env
├── BACA INI JIKA GAME GAK BISA MUNCUL.txt
├── tools/
│   └── _Add_Game (RUN ADMINISTRATOR).exe
├── bypass/
│   └── Bypass.zip
├── builds/
├── temp/
├── logs/
├── templates/
└── .venv/
```

`builds`, `temp`, dan `logs` dibuat/digunakan aplikasi. Jangan menggabungkan folder ini dengan project Discord.

# Deployment Awal dari Windows

## 1. Siapkan SSH Private Key

Private key Windows:

```text
D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem
```

Login dari PowerShell:

```powershell
ssh -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" nexaplay@103.103.20.78
```

Untuk pekerjaan administratif di VPS:

```bash
sudo -i
```

Keluar dari shell root dan kembali menjadi user `nexaplay`:

```bash
exit
```

Jangan menggunakan login root langsung melalui SSH.

## 2. Buat Archive Project di Windows

Jalankan PowerShell dari root project lokal. Archive tidak menyertakan file development, output runtime, atau `.env`. `.env` di-upload terpisah agar permission-nya tidak salah.

```powershell
tar `
  --exclude=".git" `
  --exclude=".venv" `
  --exclude="__pycache__" `
  --exclude=".claude" `
  --exclude="graphify-out" `
  --exclude="builds" `
  --exclude="temp" `
  --exclude="logs" `
  --exclude=".env" `
  -czf "$env:TEMP\nexaplay-telegram.tar.gz" .
```

Upload archive:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" "$env:TEMP\nexaplay-telegram.tar.gz" nexaplay@103.103.20.78:/home/nexaplay/
```

## 3. Extract Project ke Path Final

Login ke VPS sebagai `nexaplay`, lalu jalankan:

```bash
mkdir -p /home/nexaplay/telegram_bot_nexaplay
tar -xzf /home/nexaplay/nexaplay-telegram.tar.gz \
  -C /home/nexaplay/telegram_bot_nexaplay
rm /home/nexaplay/nexaplay-telegram.tar.gz
```

Atur ownership dan permission sebelum membuat virtualenv:

```bash
sudo chown -R nexaplay:nexaplay /home/nexaplay/telegram_bot_nexaplay
sudo find /home/nexaplay/telegram_bot_nexaplay -type d -exec chmod 755 {} +
sudo find /home/nexaplay/telegram_bot_nexaplay -type f ! -name '.env' -exec chmod 644 {} +
```

Permission final:

- Directory: `755`
- File biasa: `644`
- `.env`: `600`

Jangan menjalankan `chmod -R 777`.

## 4. Install Dependency Sistem

Project menyediakan script instalasi untuk Ubuntu. Jalankan sebagai administrator:

```bash
sudo -i
cd /home/nexaplay/telegram_bot_nexaplay
bash deploy/setup_vps_ubuntu.sh
exit
```

Script memasang Python, Nginx, PostgreSQL, Certbot, Git, Curl, dan Unzip.

Verifikasi Ubuntu dan PostgreSQL:

```bash
lsb_release -ds
psql --version
sudo pg_lsclusters
```

Production memakai PostgreSQL 16. Cluster harus berstatus `online`.

## 5. Siapkan Swap 2 GB

Swap menjadi cadangan ketika RAM sekitar 2 GB mengalami spike. Swap bukan pengganti RAM dan tidak membuat proses secepat RAM.

Jalankan:

```bash
sudo -i
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
fi
swapon --show | grep -q '^/swapfile' || swapon /swapfile
grep -q '^/swapfile none swap sw 0 0$' /etc/fstab || \
  printf '/swapfile none swap sw 0 0\n' >> /etc/fstab
exit
```

Verifikasi:

```bash
free -h
swapon --show
grep '^/swapfile none swap sw 0 0$' /etc/fstab
```

Hasil final harus menunjukkan `/swapfile` sekitar 2 GB.

## 6. Buat Database PostgreSQL

Buat password aman tanpa menulis password asli ke dokumentasi:

```bash
openssl rand -hex 24
```

Simpan hasilnya di password manager sebagai `PASSWORD_DATABASE`, lalu buka PostgreSQL:

```bash
sudo -u postgres psql
```

Jalankan di prompt PostgreSQL:

```sql
CREATE USER nexaplay_user WITH PASSWORD 'PASSWORD_DATABASE';
CREATE DATABASE nexaplay_bot OWNER nexaplay_user;
\q
```

Format `DATABASE_URL` production:

```text
postgresql://nexaplay_user:PASSWORD_DATABASE@127.0.0.1:5432/nexaplay_bot
```

Aplikasi membuat tabel dan menjalankan migrasi saat startup. Tidak perlu import SQL manual.

Verifikasi koneksi tanpa menampilkan password ke log atau dokumentasi:

```bash
sudo -u postgres psql -d nexaplay_bot -c 'SELECT current_database(), current_user;'
```

## 7. Buat Virtual Environment Python

Jalankan sebagai user `nexaplay`:

```bash
cd /home/nexaplay/telegram_bot_nexaplay
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Virtualenv final:

```text
/home/nexaplay/telegram_bot_nexaplay/.venv
```

Jika dependency gagal pada Python 3.14, gunakan Python 3.11 atau 3.12 karena stack aiogram/FastAPI project sudah diuji dengan versi tersebut.

## 8. Kelola `.env` dari Windows

`.env` production dikelola di root project lokal Windows. Jangan mengedit ulang seluruh `.env` secara manual di VPS setiap update.

Template referensi VPS tersedia di `deploy/.env.telegram.vps.example`. Salin nilainya ke `.env` lokal lalu ganti seluruh placeholder; jangan upload template yang belum diisi sebagai `.env` production.

Variabel penting:

```env
BOT_TOKEN=REPLACE_BOT_TOKEN
ADMIN_IDS=REPLACE_TELEGRAM_ADMIN_ID
DATABASE_URL=postgresql://nexaplay_user:PASSWORD_DATABASE@127.0.0.1:5432/nexaplay_bot
ADMIN_USERNAME=nexaplay
ADMIN_PASSWORD=REPLACE_ADMIN_PASSWORD
SESSION_SECRET=REPLACE_RANDOM_SESSION_SECRET
TELEGRAM_MODE=webhook
PUBLIC_BASE_URL=https://tele.nexaplayid.store
TELEGRAM_WEBHOOK_SECRET=REPLACE_RANDOM_WEBHOOK_SECRET
DELIVERY_DELETE_HOURS=24
USED_TICKET_RETENTION_DAYS=7
ADD_GAME_TUTORIAL_URL=https://youtu.be/L10MShYM4Os
BYPASS_TUTORIAL_URL=https://youtu.be/4ELIls9wr6o
BOT_LINK=https://t.me/REPLACE_BOT_USERNAME
RESEND_API_KEY=REPLACE_RESEND_API_KEY
ADD_GAME_FILENAME=_Add_Game (RUN ADMINISTRATOR).exe
BYPASS_TEMPLATE_FILENAME=Bypass.zip
LOG_LEVEL=INFO
```

Nilai `REPLACE_*` hanya placeholder. Jangan commit atau menampilkan nilai asli berikut:

- `BOT_TOKEN`
- Password database
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `TELEGRAM_WEBHOOK_SECRET`
- `RESEND_API_KEY`

Buat secret acak bila diperlukan:

```bash
openssl rand -hex 32
```

### Line Ending Windows

Opsi terbaik: buka `.env` di VS Code, klik indikator `CRLF` di status bar, pilih `LF`, lalu simpan sebelum upload.

Upload `.env` dari PowerShell saat sudah berada di root project:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".env" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/.env
```

Jika file masih memakai CRLF, bersihkan karakter `\r` setelah upload:

```bash
sed -i 's/\r$//' /home/nexaplay/telegram_bot_nexaplay/.env
```

Selalu lindungi permission `.env`:

```bash
chmod 600 /home/nexaplay/telegram_bot_nexaplay/.env
```

Jangan menggunakan `cat .env`, `grep` seluruh `.env`, atau memasukkan isinya ke log/chat.

## 9. Periksa File Wajib

```bash
ls -lah "/home/nexaplay/telegram_bot_nexaplay/tools/_Add_Game (RUN ADMINISTRATOR).exe"
ls -lah "/home/nexaplay/telegram_bot_nexaplay/bypass/Bypass.zip"
ls -lah /home/nexaplay/telegram_bot_nexaplay/api.json
ls -lah "/home/nexaplay/telegram_bot_nexaplay/BACA INI JIKA GAME GAK BISA MUNCUL.txt"
```

Nama file dalam `tools/` dan `bypass/` harus sama dengan `ADD_GAME_FILENAME` dan `BYPASS_TEMPLATE_FILENAME` di `.env`.

## 10. Konfigurasi DNS

DNS final:

```text
Type: A
Name: tele
Target: 103.103.20.78
```

Verifikasi dari Windows:

```powershell
nslookup tele.nexaplayid.store
```

Hasil harus mengarah ke `103.103.20.78`.

## 11. Konfigurasi Nginx

Pasang virtual host final dari template khusus Telegram:

```bash
sudo cp \
  /home/nexaplay/telegram_bot_nexaplay/deploy/nexaplay-telegram.nginx.conf \
  /etc/nginx/sites-available/nexaplay-telegram
sudo ln -sfn /etc/nginx/sites-available/nexaplay-telegram \
  /etc/nginx/sites-enabled/nexaplay-telegram
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Template `deploy/nexaplay-telegram.nginx.conf` menetapkan `server_name tele.nexaplayid.store` dan meneruskan request ke `127.0.0.1:8000`.

`nginx -t` harus menghasilkan `syntax is ok` dan `test is successful`.

Aplikasi hanya mendengarkan `127.0.0.1:8000`. Jangan membuka port 8000 ke internet.

## 12. Konfigurasi UFW

Buka SSH sebelum mengaktifkan firewall agar koneksi tidak terkunci:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Port publik final:

- `22`: SSH
- `80`: HTTP
- `443`: HTTPS

Port PostgreSQL `5432` dan aplikasi `8000` tidak dibuka ke internet.

## 13. Aktifkan HTTPS

```bash
sudo certbot --nginx -d tele.nexaplayid.store
```

Pilih redirect HTTP ke HTTPS ketika diminta.

Verifikasi sertifikat dan auto-renew:

```bash
sudo certbot certificates
systemctl status certbot.timer --no-pager
sudo certbot renew --dry-run
```

URL final:

```text
https://tele.nexaplayid.store
```

## 14. Buat Service systemd Final

Pasang file service final dari template khusus Telegram:

```bash
sudo cp \
  /home/nexaplay/telegram_bot_nexaplay/deploy/nexaplay-telegram.service \
  /etc/systemd/system/nexaplay-telegram.service
```

Template memakai `WorkingDirectory=/home/nexaplay/telegram_bot_nexaplay` dan menjalankan `bot.py` melalui `.venv/bin/python`.

Aktifkan dan mulai service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
```

`ExecStart` menjalankan ulang `bot.py` dari virtualenv setiap kali service dimulai atau direstart. Restart service tidak me-reboot VPS.

`enabled` membuat service otomatis hidup setelah VPS reboot. `Restart=always` menjalankan ulang proses ketika bot crash.

Jika file service diubah:

```bash
sudo systemctl daemon-reload
sudo systemctl restart nexaplay-telegram
```

## 15. Verifikasi Deployment

Cek service:

```bash
systemctl is-enabled nexaplay-telegram
systemctl is-active nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
```

Hasil utama:

```text
enabled
active
```

Cek aplikasi lokal tanpa membuka port 8000:

```bash
curl -I http://127.0.0.1:8000/admin/login
```

Cek panel publik:

```bash
curl -I https://tele.nexaplayid.store/admin/login
```

Buka panel:

```text
https://tele.nexaplayid.store/admin/login
```

Cek endpoint webhook menghasilkan HTTP 200:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  -X POST https://tele.nexaplayid.store/telegram/webhook
```

Request tanpa secret tidak memproses update Telegram, tetapi route yang sehat tetap merespons HTTP 200.

Cek webhook melalui Telegram API dengan token placeholder, bukan token yang ditulis ke dokumentasi:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

Hasil sehat memuat:

```json
{
  "ok": true,
  "result": {
    "url": "https://tele.nexaplayid.store/telegram/webhook"
  }
}
```

Jangan membagikan command yang sudah berisi token asli karena token menjadi bagian URL.

Uji end-to-end:

1. Login panel admin.
2. Buat ticket.
3. Kirim kode ticket ke bot Telegram.
4. Pastikan bot menerima dan memproses ticket.
5. Pastikan ticket berhasil redeemed.
6. Pastikan file `NexaPlay.zip` terkirim.
7. Pastikan email terkirim jika Resend digunakan.

## 16. Verifikasi Setelah Reboot

Reboot hanya untuk uji auto-start setelah setup selesai:

```bash
sudo reboot
```

Setelah VPS kembali online, login ulang dari PowerShell:

```powershell
ssh -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" nexaplay@103.103.20.78
```

Verifikasi:

```bash
systemctl is-enabled nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
systemctl status nginx --no-pager
sudo pg_lsclusters
```

Service Telegram harus tetap `enabled` dan `active (running)`.

# Update Project Setelah Deployment

Update dilakukan dari root project lokal Windows menuju path production yang sama.

## Upload Satu File Python

Contoh update `web_app.py` dari PowerShell:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".\web_app.py" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/web_app.py
```

Restart lalu cek:

```bash
sudo systemctl restart nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
journalctl -u nexaplay-telegram -n 100 --no-pager
```

Perubahan file Python baru aktif setelah proses menjalankan ulang `bot.py`.

## Upload `.env`

Simpan `.env` sebagai LF di VS Code bila memungkinkan, lalu upload:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".env" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/.env
```

Di VPS:

```bash
sed -i 's/\r$//' /home/nexaplay/telegram_bot_nexaplay/.env
chmod 600 /home/nexaplay/telegram_bot_nexaplay/.env
sudo systemctl restart nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
```

Aplikasi membaca `.env` saat `bot.py` mulai. Karena itu perubahan `.env` membutuhkan restart service.

## Update `requirements.txt`

Upload file:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".\requirements.txt" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/requirements.txt
```

Install dependency dan restart:

```bash
cd /home/nexaplay/telegram_bot_nexaplay
sudo -u nexaplay .venv/bin/pip install -r requirements.txt
sudo systemctl restart nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
journalctl -u nexaplay-telegram -n 100 --no-pager
```

## Update File EXE, ZIP, atau `api.json`

Contoh upload file dengan nama yang sama:

```powershell
scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".\tools\_Add_Game (RUN ADMINISTRATOR).exe" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/tools/

scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".\bypass\Bypass.zip" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/bypass/Bypass.zip

scp -i "D:\_NEXAPLAY\VPS\nexaplay-bot-key.pem" ".\api.json" nexaplay@103.103.20.78:/home/nexaplay/telegram_bot_nexaplay/api.json
```

Perilaku project:

- EXE dan ZIP bypass dibuka ketika package ticket dibangun. Jika isi file diganti dengan nama yang sama, restart biasanya tidak diperlukan.
- `api.json` dibaca ulang ketika daftar API dipakai. Update isinya biasanya tidak memerlukan restart.
- Jika nama EXE/ZIP berubah, perbarui `ADD_GAME_FILENAME` atau `BYPASS_TEMPLATE_FILENAME` di `.env`, lalu restart.
- File Python, konfigurasi startup, atau `.env` harus diikuti restart.

Sesudah update aset, lakukan satu test pembuatan ticket. Restart tetap aman bila ingin memastikan proses memakai konfigurasi terbaru:

```bash
sudo systemctl restart nexaplay-telegram
```

## Jika File Service Diubah

```bash
sudo systemctl daemon-reload
sudo systemctl restart nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
```

# Perintah Harian

Restart bot tanpa reboot VPS:

```bash
sudo systemctl restart nexaplay-telegram
```

Status:

```bash
systemctl status nexaplay-telegram --no-pager
```

Log terakhir:

```bash
journalctl -u nexaplay-telegram -n 100 --no-pager
```

Log realtime:

```bash
journalctl -u nexaplay-telegram -f
```

Keluar dari log realtime dengan `Ctrl+C`.

Start dan stop:

```bash
sudo systemctl start nexaplay-telegram
sudo systemctl stop nexaplay-telegram
```

Enable sekaligus start:

```bash
sudo systemctl enable --now nexaplay-telegram
```

# Monitoring

Cek RAM dan swap:

```bash
free -h
swapon --show
```

Cek disk:

```bash
df -h
```

Cek semua service utama:

```bash
systemctl status nexaplay-telegram --no-pager
systemctl status nginx --no-pager
systemctl status postgresql --no-pager
sudo pg_lsclusters
```

Cek port listening:

```bash
sudo ss -lntp
```

Port `8000` harus terikat ke `127.0.0.1`, bukan `0.0.0.0`.

Cek proses dengan penggunaan RAM terbesar:

```bash
ps aux --sort=-%mem | head
```

Log aplikasi juga tersedia di:

```text
/home/nexaplay/telegram_bot_nexaplay/logs/bot.log
```

Lihat log tanpa membuka `.env`:

```bash
tail -n 100 /home/nexaplay/telegram_bot_nexaplay/logs/bot.log
```

# Troubleshooting

## Service Gagal Start

```bash
systemctl status nexaplay-telegram --no-pager
journalctl -u nexaplay-telegram -n 100 --no-pager
```

Periksa path executable tanpa menampilkan `.env`:

```bash
ls -lah /home/nexaplay/telegram_bot_nexaplay/bot.py
ls -lah /home/nexaplay/telegram_bot_nexaplay/.venv/bin/python
```

Setelah perbaikan:

```bash
sudo systemctl restart nexaplay-telegram
systemctl status nexaplay-telegram --no-pager
```

## Setelah Mengubah File Service

```bash
sudo systemctl daemon-reload
sudo systemctl restart nexaplay-telegram
journalctl -u nexaplay-telegram -n 100 --no-pager
```

## HTTP 502 dari Nginx

502 berarti Nginx tidak dapat menjangkau FastAPI di `127.0.0.1:8000`.

```bash
systemctl status nexaplay-telegram --no-pager
curl -I http://127.0.0.1:8000/admin/login
sudo nginx -t
journalctl -u nexaplay-telegram -n 100 --no-pager
journalctl -u nginx -n 100 --no-pager
```

## Webhook Tidak Memproses Update

```bash
systemctl status nexaplay-telegram --no-pager
journalctl -u nexaplay-telegram -n 100 --no-pager
curl -I https://tele.nexaplayid.store/admin/login
```

Periksa `getWebhookInfo` menggunakan token secara lokal dan jangan bagikan output yang memuat informasi sensitif. URL webhook harus tepat:

```text
https://tele.nexaplayid.store/telegram/webhook
```

## PostgreSQL Bermasalah

```bash
systemctl status postgresql --no-pager
sudo pg_lsclusters
sudo journalctl -u postgresql -n 100 --no-pager
```

`DATABASE_URL` harus mengarah ke `127.0.0.1:5432/nexaplay_bot`. Jangan menampilkan nilai lengkap jika berisi password asli.

## Permission `.env`

```bash
stat -c '%a %U:%G %n' /home/nexaplay/telegram_bot_nexaplay/.env
```

Hasil yang benar:

```text
600 nexaplay:nexaplay /home/nexaplay/telegram_bot_nexaplay/.env
```

Perbaiki tanpa menampilkan isi file:

```bash
sudo chown nexaplay:nexaplay /home/nexaplay/telegram_bot_nexaplay/.env
chmod 600 /home/nexaplay/telegram_bot_nexaplay/.env
sudo systemctl restart nexaplay-telegram
```

# Setup Email Resend

1. Tambahkan domain `nexaplayid.store` di dashboard Resend.
2. Salin record SPF dan DKIM dari Resend ke DNS Zone Editor tanpa mengubah nama atau nilainya.
3. Jangan membuat dua record SPF pada hostname yang sama. Gabungkan sesuai petunjuk Resend jika record sudah ada.
4. Tambahkan record DMARC awal:

   ```text
   Type: TXT
   Name: _dmarc
   Value: v=DMARC1; p=none; adkim=r; aspf=r;
   ```

5. Tunggu status domain di Resend menjadi `Verified`.
6. Simpan API key hanya dalam `.env` lokal, lalu upload `.env` memakai prosedur di atas.
7. Kirim email uji ke Gmail dan periksa versi asli. SPF, DKIM, dan DMARC harus `PASS`.

Email otomatis memakai `NexaPlay <order@nexaplayid.store>`. Balasan customer diarahkan ke `nexaplayid@gmail.com` melalui header `Reply-To`.

# Testing Lokal

Untuk testing lokal Windows:

```env
TELEGRAM_MODE=polling
PUBLIC_BASE_URL=
TELEGRAM_WEBHOOK_SECRET=
```

Langkah ringkas:

1. Siapkan Python 3.11 atau 3.12 dan PostgreSQL.
2. Isi `.env` lokal dengan secret development.
3. Pastikan file dalam `tools/`, `bypass/`, `api.json`, dan file panduan tersedia.
4. Install dependency:

   ```powershell
   pip install -r requirements.txt
   ```

5. Jalankan:

   ```powershell
   python bot.py
   ```

6. Buka `http://127.0.0.1:8000/admin/login`.
7. Login, buat ticket, lalu kirim kode ticket ke bot untuk test redeem.

Production tetap memakai `TELEGRAM_MODE=webhook`.

# Endpoint

- `GET /admin/login` — login admin
- `GET /admin` — dashboard admin
- `POST /admin/tickets/create` — membuat ticket
- `POST /telegram/webhook` — endpoint webhook Telegram

# Fitur Utama

- Ticket valid sampai dipakai
- Admin dapat memilih API:
  - `auto`: fallback mengikuti urutan API aktif dalam `api.json`
  - `manual`: memakai satu API yang dipilih
- Bypass mengedit `gamefixer.cfg` dan menambahkan koma terakhir
- Nama file bypass dan Add Game mengikuti nama file sumber
- `BACA INI JIKA GAME GAK BISA MUNCUL.txt` dimasukkan ke `NexaPlay.zip`
- Urutan pesan redeem:
  1. Peringatan penghapusan otomatis 24 jam
  2. Peringatan bypass jika diperlukan
  3. Link tutorial Add Game dan bypass jika diperlukan
  4. File dengan caption `Silahkan download Setup Tersebut`
- Pesan peringatan/tutorial tidak dihapus
- Hanya pesan file yang dihapus otomatis setelah 24 jam

# Checklist Akhir Production

- [ ] Ubuntu 24.04 aktif di `103.103.20.78`
- [ ] Login SSH key sebagai `nexaplay` berhasil
- [ ] Project berada di `/home/nexaplay/telegram_bot_nexaplay`
- [ ] Virtualenv berada di `/home/nexaplay/telegram_bot_nexaplay/.venv`
- [ ] `.env` berasal dari project lokal Windows, memakai LF atau sudah dibersihkan dari CRLF
- [ ] `.env` dimiliki `nexaplay:nexaplay` dengan permission `600`
- [ ] Tidak ada secret yang masuk Git atau dokumentasi
- [ ] File EXE, ZIP bypass, `api.json`, dan file panduan tersedia
- [ ] PostgreSQL 16 cluster berstatus online
- [ ] Database `nexaplay_bot` dan user `nexaplay_user` tersedia
- [ ] Swap `/swapfile` 2 GB aktif dan tercatat dalam `/etc/fstab`
- [ ] DNS `tele.nexaplayid.store` mengarah ke `103.103.20.78`
- [ ] UFW hanya membuka OpenSSH dan Nginx Full
- [ ] Port 8000 hanya mendengarkan di `127.0.0.1`
- [ ] Nginx aktif dan konfigurasi lolos `nginx -t`
- [ ] HTTPS aktif dan `certbot renew --dry-run` berhasil
- [ ] `PUBLIC_BASE_URL=https://tele.nexaplayid.store`
- [ ] `TELEGRAM_MODE=webhook`
- [ ] Service `nexaplay-telegram.service` berstatus `enabled`
- [ ] Service `nexaplay-telegram.service` berstatus `active (running)`
- [ ] Panel admin dapat dibuka di `https://tele.nexaplayid.store/admin/login`
- [ ] Webhook aktif di `https://tele.nexaplayid.store/telegram/webhook`
- [ ] `getWebhookInfo` menghasilkan `ok=true`
- [ ] Ticket berhasil dibuat, diterima Telegram, dan redeemed
- [ ] Service kembali aktif setelah reboot VPS
