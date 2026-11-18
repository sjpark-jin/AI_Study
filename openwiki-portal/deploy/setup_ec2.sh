#!/usr/bin/env bash
set -euo pipefail

# AWS EC2 (Ubuntu 22.04 / 24.04) 원클릭 배포 스크립트
# 사용법: sudo ./deploy/setup_ec2.sh

APP_DIR="/opt/openwiki-portal"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 [1/5] 시스템 패키지 설치 (Python3, venv, Nginx)..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx

echo "📦 [2/5] 프로젝트 파일 복사 -> $APP_DIR ..."
mkdir -p "$APP_DIR"
cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
if [ -f "$SCRIPT_DIR/.env" ]; then
  cp "$SCRIPT_DIR/.env" "$APP_DIR/.env"
fi

echo "🐍 [3/5] Python 가상환경 구성 및 의존성 설치..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "⚙️ [4/5] Systemd 서비스 등록 및 실행..."
cp "$APP_DIR/deploy/openwiki-portal.service" /etc/systemd/system/openwiki-portal.service
chown -R ubuntu:ubuntu "$APP_DIR"
systemctl daemon-reload
systemctl enable openwiki-portal
systemctl restart openwiki-portal

echo "🌐 [5/5] Nginx 리버스 프록시 설정 및 재시작..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/openwiki-portal
ln -sf /etc/nginx/sites-available/openwiki-portal /etc/nginx/sites-enabled/openwiki-portal
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "✅ 배포 완료! 브라우저에서 EC2 퍼블릭 IP (http://<EC2_PUBLIC_IP>)로 접속하세요."

