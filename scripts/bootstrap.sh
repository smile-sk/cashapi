#!/usr/bin/env bash
# Bootstrap ВМ Ubuntu 24.04 для CashAPI
# Запускать: sudo bash bootstrap.sh  (от любого пользователя с sudo)
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

PUBKEY="PASTE_YOUR_PUBLIC_KEY_HERE"

echo "[1/5] apt update + upgrade"
apt-get update -y
apt-get upgrade -y

echo "[2/5] пользователь cody + sudo (без пароля - только ключ)"
if ! id cody >/dev/null 2>&1; then
  useradd -m -s /bin/bash cody
fi
echo "cody ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/cody
chmod 440 /etc/sudoers.d/cody

echo "[3/5] SSH-ключ для cody"
install -d -o cody -g cody -m 700 /home/cody/.ssh
echo "$PUBKEY" > /home/cody/.ssh/authorized_keys
chown cody:cody /home/cody/.ssh/authorized_keys
chmod 600 /home/cody/.ssh/authorized_keys

echo "[4/5] Docker + инструменты"
apt-get install -y docker.io docker-compose-v2 python3-venv python3-pip git ufw
systemctl enable --now docker
usermod -aG docker cody

echo "[5/5] фаервол (наружу только SSH)"
ufw allow OpenSSH
ufw --force enable

echo "ГОТОВО. Проверка с твоей Windows: ssh cody@x.x.x.x"
