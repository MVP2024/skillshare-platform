#!/usr/bin/env bash
set -euo pipefail

# create_yc_vm.sh
# Помогает быстро создать VM в Yandex Cloud с публичным IP и подготовить SSH-ключ для деплоя.
# Скрипт использует yc CLI (https://cloud.yandex.ru/docs/cli/)
# Пример запуска:
#   ./deploy/create_yc_vm.sh --name skillshare-backend --zone ru-central1-a --reserve-ip
# Параметры:
#   --name        - имя VM (по умолчанию skillshare-backend)
#   --zone        - зона (по умолчанию ru-central1-a)
#   --ssh-pub     - путь к публичному SSH ключу (по умолчанию ~/.ssh/id_ed25519.pub)
#   --reserve-ip  - если указан, создаст зарезервированный внешний IPv4 адрес (не автоматически привязывает к инстансу)
# Скрипт:
# 1) проверяет, установлен ли yc
# 2) при необходимости генерирует пару SSH ключей (id_ed25519)
# 3) создаёт VM с публичным IP
# 4) (опционально) создаёт reserved external IP и показывает, как привязать его вручную
# 5) сохраняет приватный ключ в файле deploy/yc_deploy_key (совет: добавить содержимое этого файла как GitHub secret SSH_PRIVATE_KEY)

VM_NAME="skillshare-backend"
ZONE="ru-central1-a"
SSH_PUB_PATH="$HOME/.ssh/id_ed25519.pub"
SSH_KEY_NAME="yc-deploy-key"
RESERVE_IP=false
YC_REGION="ru-central1"

print_usage() {
  cat <<'USAGE'
Usage: create_yc_vm.sh [--name NAME] [--zone ZONE] [--ssh-pub PATH] [--reserve-ip]

Options:
  --name NAME       VM name (default: skillshare-backend)
  --zone ZONE       Zone (default: ru-central1-a)
  --ssh-pub PATH    Path to public SSH key (default: ~/.ssh/id_ed25519.pub)
  --reserve-ip      Create a reserved external IPv4 address (won't auto-attach)

After running, the script prints the VM public IP and path to the private deploy key
(./deploy/yc_deploy_key) which you can store in GitHub Secrets as SSH_PRIVATE_KEY.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      VM_NAME="$2"; shift 2;;
    --zone)
      ZONE="$2"; shift 2;;
    --ssh-pub)
      SSH_PUB_PATH="$2"; shift 2;;
    --reserve-ip)
      RESERVE_IP=true; shift 1;;
    --help|-h)
      print_usage; exit 0;;
    *)
      echo "Unknown option: $1" >&2; print_usage; exit 1;;
  esac
done

if ! command -v yc >/dev/null 2>&1; then
  echo "yc CLI not found. Install and authenticate yc first: https://cloud.yandex.ru/docs/cli/" >&2
  exit 1
fi

# Убедитесь, что открытый ключ SSH существует, или создайте новую пару ключей
if [ ! -f "$SSH_PUB_PATH" ]; then
  echo "Public key $SSH_PUB_PATH not found. Generating new SSH key pair at ~/.ssh/id_ed25519..."
  ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519" -N "" -C "yc-deploy-key" || true
  SSH_PUB_PATH="$HOME/.ssh/id_ed25519.pub"
fi

if [ ! -f "$SSH_PUB_PATH" ]; then
  echo "Public SSH key still not found at $SSH_PUB_PATH" >&2
  exit 1
fi

# Создаём приватную копию ключа, чтобы использовать его в качестве секрета GitHub Actions (не фиксируйте!)
DEPLOY_KEY_PATH="$(pwd)/deploy/yc_deploy_key"
mkdir -p "$(dirname "$DEPLOY_KEY_PATH")"
# Копируем закрытый ключ, если он есть, или создайте его на основе сгенерированного ключа
if [ -f "$HOME/.ssh/id_ed25519" ]; then
  cp "$HOME/.ssh/id_ed25519" "$DEPLOY_KEY_PATH"
  chmod 600 "$DEPLOY_KEY_PATH"
else
  echo "WARNING: private key $HOME/.ssh/id_ed25519 not found. You must provide a private key to use as SSH_PRIVATE_KEY secret." >&2
fi

echo "Using public SSH key: $SSH_PUB_PATH"

# Проверка: существует ли уже инстанс с таким именем. Если да — выводим его публичный IP и завершаем работу скрипта.
EXISTING_JSON=$(yc compute instance get --name "$VM_NAME" --format json 2>/dev/null || true)
if [ -n "$EXISTING_JSON" ]; then
  EXISTING_IP=$(echo "$EXISTING_JSON" | python -c 'import sys, json
try:
    obj = json.load(sys.stdin)
    ip = obj["network_interfaces"][0]["primary_v4_address"]["one_to_one_nat"]["address"]
    print(ip)
except Exception:
    pass')
  echo "Instance with name '$VM_NAME' already exists."
  if [ -n "$EXISTING_IP" ]; then
    echo "Public IP: $EXISTING_IP"
  else
    echo "Unable to determine existing instance public IP automatically. Use 'yc compute instance get --name $VM_NAME --format json' to inspect."
  fi
  echo "If you want to create a new instance, run the script with a different --name or delete the existing instance first."
  exit 0
fi

# Создание VM
echo "Creating VM '$VM_NAME' in zone $ZONE..."
# Для демонстрации используйте базовую маломощную машину. При необходимости измените параметры --memory/--cores."

# Получите публичный IP-адрес виртуальной машины (проанализируйте вывод JSON с помощью Python)
VM_JSON=$(yc compute instance get --name "$VM_NAME" --format json || true)
VM_PUBLIC_IP=$(echo "$VM_JSON" | python -c 'import sys, json
try:
    obj = json.load(sys.stdin)
    ip = obj["network_interfaces"][0]["primary_v4_address"]["one_to_one_nat"]["address"]
    print(ip)
except Exception:
    pass')

if [ -n "$VM_PUBLIC_IP" ]; then
  echo "VM public IP: $VM_PUBLIC_IP"
else
  echo "Unable to determine VM public IP automatically. Check yc compute instance get --name $VM_NAME" >&2
fi

if [ "$RESERVE_IP" = true ]; then
  IP_NAME="${VM_NAME}-reserved-ip"
  echo "Creating reserved external IP: $IP_NAME (region: $YC_REGION)"
  yc compute address create --name "$IP_NAME" --region "$YC_REGION" || true
  # Пробуем получить зарезервированный IP-адрес
  ADDR_JSON=$(yc compute address get --name "$IP_NAME" --format json || true)
  RESERVED_IP=$(echo "$ADDR_JSON" | python -c 'import sys, json
try:
    obj = json.load(sys.stdin)
    print(obj.get("address",""))
except Exception:
    pass')
  echo "Reserved IP created: $RESERVED_IP"
  echo "NOTE: to attach reserved IP to your instance, use the Console or the yc CLI. Example (console is easiest):"
  echo " - Console: Compute Cloud → External IP addresses → attach to instance"
  echo " - Or using yc CLI: see https://cloud.yandex.ru/docs/compute/operations/instance-networking for exact commands."
fi

# Показываем инструкции для GitHub secret
if [ -f "$DEPLOY_KEY_PATH" ]; then
  echo
  echo "Private deploy key saved to: $DEPLOY_KEY_PATH"
  echo "IMPORTANT: Do NOT commit this key to Git. Add contents of this file as GitHub secret SSH_PRIVATE_KEY"
  echo "To add secret in GitHub: Settings → Secrets and variables → Actions → New repository secret"
  echo "Name: SSH_PRIVATE_KEY"
  echo "Value: (paste contents of $DEPLOY_KEY_PATH)"
fi

# Заключительные напоминания
echo
echo "Next steps (recommended):"
echo " - SSH to the server: ssh <user>@$VM_PUBLIC_IP  (user is shown in YC console or 'yc compute instance get')"
echo " - On server: create .env from .env.example and configure production values, then run:"
echo "     docker compose -f docker-compose.prod.yml up -d --build"
echo

echo "Script finished."
