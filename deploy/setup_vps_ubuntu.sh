#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   sudo bash deploy/setup_vps_ubuntu.sh
#
# This script installs system dependencies only.
# Project-specific steps (upload code, .env, systemd, nginx, ssl)
# are done with separate files in deploy/.

echo "[1/4] apt update"
apt update

echo "[2/4] install base packages"
apt install -y \
  python3 python3-venv python3-pip \
  nginx \
  postgresql postgresql-contrib \
  certbot python3-certbot-nginx \
  unzip curl git

echo "[3/4] enable services"
systemctl enable nginx
systemctl enable postgresql
systemctl restart nginx
systemctl restart postgresql

echo "[4/4] done"
echo "System dependencies installed. Continue with DB, app, systemd, nginx config."
