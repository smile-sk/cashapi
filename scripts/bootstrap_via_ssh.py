#!/usr/bin/env python3
"""
Bootstrap сервера CashAPI - выполняется Коди САМ через SSH (paramiko).

Использование:
    python bootstrap_via_ssh.py --host x.x.x.x --user <ubuntu_user> --password <пароль>

Что делает:
  1. Подключается к серверу по SSH (первый вход - логин/пароль от установки Ubuntu).
  2. Создаёт пользователя cody (sudo, bash).
  3. Кладёт authorized_keys: ключ Стаса + ключ Коди.
  4. Ставит Docker, docker-compose, python3-venv, git, ufw.
  5. Добавляет cody в группу docker.
  6. Включает фаервол (только SSH).
  7. Проверяет вход под cody по ключу Коди.
"""
import argparse, getpass, sys
import paramiko

HOST = "x.x.x.x"
CODY_USER = "cody"

# Публичные ключи для authorized_keys
KEYS = [
    # Ключ Стаса (сгенерирован на его Windows)
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIImt0vPtEV/kRHJ9fc2IIXc/pN/PKimbb1RgYZsgUw7t cody@cashapi",
    # Ключ Коди (сгенерирован Коди, приватная часть: keys/cody_ed25519)
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOvUhwCH9iiON+eWzmMimu/tMj4TQqRryISbSDpZjjOv cody@cashapi",
]

def run(ssh, cmd, sudo=False, password=None):
    """Выполнить команду, вернуть (exit_code, stdout, stderr)."""
    if sudo:
        cmd = f"echo '{password}' | sudo -S -p '' bash -c \"{cmd}\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--user", required=True, help="пользователь, созданный при установке Ubuntu")
    ap.add_argument("--password", help="его пароль (можно не указывать - спрошу)")
    args = ap.parse_args()

    password = args.password or getpass.getpass("Пароль от %s@%s: " % (args.user, args.host))

    print(f"[1/7] Подключаюсь к {args.user}@{args.host} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(args.host, port=22, username=args.user, password=password, timeout=15)
    except Exception as e:
        print("НЕ УДАЛОСЬ подключиться:", e)
        sys.exit(1)
    print("      OK")

    print("[2/7] Создаю пользователя cody ...")
    code, out, err = run(ssh, f"id {CODY_USER} 2>/dev/null || useradd -m -s /bin/bash {CODY_USER} && echo '{password}' | passwd {CODY_USER} --stdin && usermod -aG sudo {CODY_USER}", sudo=True, password=password)
    print("      ", out.strip() or err.strip() or "OK")

    print("[3/7] Кладу ключи в authorized_keys ...")
    keys_joined = "\n".join(KEYS)
    cmd = (
        f"mkdir -p /home/{CODY_USER}/.ssh && chmod 700 /home/{CODY_USER}/.ssh && "
        f"echo '{keys_joined}' > /home/{CODY_USER}/.ssh/authorized_keys && "
        f"chown -R {CODY_USER}:{CODY_USER} /home/{CODY_USER}/.ssh && chmod 600 /home/{CODY_USER}/.ssh/authorized_keys"
    )
    code, out, err = run(ssh, cmd, sudo=True, password=password)
    print("      ", out.strip() or err.strip() or "OK")

    print("[4/7] Ставлю пакеты (docker, python, git, ufw) ...")
    code, out, err = run(ssh, "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq docker.io docker-compose-v2 python3-venv python3-pip git ufw >/dev/null 2>&1; echo EXIT=$?", sudo=True, password=password)
    print("      ", out.strip()[-200:] or err.strip()[-200:] or "OK")

    print("[5/7] cody в группе docker + docker включён в автозагрузку ...")
    code, out, err = run(ssh, f"usermod -aG docker {CODY_USER} && systemctl enable --now docker", sudo=True, password=password)
    print("      ", out.strip() or err.strip() or "OK")

    print("[6/7] Фаервол: только SSH ...")
    code, out, err = run(ssh, "ufw allow OpenSSH && ufw --force enable", sudo=True, password=password)
    print("      ", out.strip() or err.strip() or "OK")

    ssh.close()
    print("[7/7] Проверяю вход под cody по ключу Коди ...")
    ssh2 = paramiko.SSHClient()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        key = paramiko.Ed25519Key.from_private_key_file(r"D:\Documents\Projects\CashAPI\keys\cody_ed25519")
        ssh2.connect(args.host, port=22, username=CODY_USER, pkey=key, timeout=15)
        _, out, _ = ssh2.exec_command("whoami && hostname && free -h | head -2")
        print("      ВХОД ПО КЛЮЧУ OK:")
        print(out.read().decode())
        ssh2.close()
        print("ГОТОВО. Сервер настроен, Коди заходит сам.")
    except Exception as e:
        print("Вход по ключу не удался:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
