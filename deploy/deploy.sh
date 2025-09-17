#!/usr/bin/env bash
set -e

DEPLOY_PATH=${DEPLOY_PATH:-/home/deploy/skillshare}
REPO_URL="https://github.com/${GITHUB_REPOSITORY:-your/repo}.git"
BRANCH=${1:-develop}

if [ ! -d "$DEPLOY_PATH" ]; then
  mkdir -p "$DEPLOY_PATH"
  git clone "$REPO_URL" "$DEPLOY_PATH"
fi

cd "$DEPLOY_PATH"

git fetch --all
git checkout "$BRANCH" || git checkout -B "$BRANCH" origin/"$BRANCH"
git reset --hard origin/"$BRANCH"

if [ ! -f .env ]; then
  echo "Пожалуйста, создайте файл .env на основе .env.example с производственными значениями" >&2
  exit 1
fi

# Убедитесь, что Docker Compose v2 доступен
if ! command -v docker >/dev/null 2>&1; then
  echo "На сервере не установлен Docker. Перед запуском этого скрипта установите Docker и Docker Compose V2." >&2
  exit 1
fi

# Запуск служб
docker compose -f docker-compose.prod.yml pull || true
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# Запуск миграций и сбор данных
sleep 5
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput || true
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput || true

echo "Развернули $BRANCH в $DEPLOY_PATH"
