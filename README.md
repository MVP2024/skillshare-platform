# SkillShare Platform Backend

Краткое и понятное руководство для разработчиков и преподавателя, который будет проверять проект.

Badges: Django, DRF, Python, PostgreSQL, Docker

---

## Что в репозитории

Это бэкенд на Django + Django REST Framework для учебной платформы (курсы, уроки, платежи, пользователи). Основные папки и файлы:

- `skillshare_platform/` — настройки Django, URL, wsgi/asgi, celery.
- `users/` — приложение пользователей и платежей.
- `materials/` — приложения курсов и уроков.
- `docker-compose.yaml` — локальная конфигурация для разработки.
- `docker-compose.prod.yml` — конфигурация для продакшн (VM).
- `.github/workflows/ci-cd.yml` — GitHub Actions: линтеры, тесты, сборка образов и deploy.
- `.env.example` — пример переменных окружения.
- `requirements.txt` — зависимости.
- `deploy/` — вспомогательные файлы для деплоя (nginx конфиг, скрипт deploy.sh).

---

## Кратко о возможностях

- регистрация/авторизация пользователей (JWT)
- CRUD для курсов и уроков
- система ролей: суперпользователь, модератор, владелец курса/урока
- история платежей, интеграция со Stripe (тестовый режим)
- фоновые задачи через Celery + Redis
- миграции и фикстуры для тестовых данных

---

## Быстрый старт (локально, с venv)

1. Клонируйте репозиторий и зайдите в папку:

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd SkillShare
```

2. Создайте и активируйте виртуальное окружение (пример для Windows PowerShell / Linux/macOS):

Windows PowerShell:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Установите зависимости:

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

4. Создайте `.env` в корне проекта, скопировав `.env.example` и подставив значения. В локальной разработке достаточно:

```
SECRET_KEY=dev-secret
DEBUG=True
DB_NAME=skillshare
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

(Если используете Docker — переменные можно хранить в `.env` и Docker Compose подхватит их.)

5. Простейший способ запустить локально — через Docker Compose (рекомендуется):

```bash
# локальный (development) compose в файле docker-compose.yaml
docker compose up -d --build
# либо старый синтаксис (если вы используете docker-compose отдельный бинарник)
# docker-compose up -d --build
```

После запуска сайт будет доступен по: http://localhost:8001/ (порт проброшен на 8001 в `docker-compose.yaml`).
Документация API: http://localhost:8001/api/schema/swagger-ui/

6. Команды внутри контейнера (пример):

```bash
# выполнить миграции
docker compose exec backend python manage.py migrate --noinput
# загрузить тестовые данные (фикстура)
docker compose exec backend python manage.py load_initial_data
# создать суперпользователя
docker compose exec backend python manage.py createsuperuser
```

7. Остановка:

```bash
docker compose down -v
# или
# docker-compose down -v
```

---
 
## Что вводить, чтобы зайти на удалённый сервер/демку (инструкции для преподавателя)

### Для ученика и учителя:

1) Публичный URL (production)

- Публичный адрес сервера (пример): `http://158.160.22.96/` — это внешний IP хоста, на котором проброшены порты 80/443 для продакшн docker compose.

- Swagger (API): `http://158.160.22.96/api/schema/swagger-ui/`

- Админка Django (если есть суперпользователь): `http://158.160.22.96/admin/`

Примечание: в продакшне приложение поднимается из файла docker-compose.prod.yml и пробрасывает порты 80 и 443 на хост — поэтому порт в URL не указывается.

2) Как запускать продакшн на сервере

- Для продакшн используйте явный prod-файл:

```bash
cd /path/to/project
# поднять весь prod-стек
docker compose -f docker-compose.prod.yml up -d --build
# или только nginx (если нужно)
# docker compose -f docker-compose.prod.yml up -d --build nginx
```

- Проверки/диагностика:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs nginx --tail=200
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

3) SSH-доступ — правильный рабочий поток (безопасно)

- Для доступа по SSH преподаватель должен иметь приватный ключ, который соответствует публичному ключу, находящемуся в
  файле `/home/test_machina/.ssh/authorized_keys` на VM. Никогда не пересылайте приватный ключ по почте.

- Попросите преподавателя сгенерировать у себя ключ и прислать вам только публичную часть (~/.ssh/id_ed25519.pub или
  ~/.ssh/id_rsa.pub).

- Команды, чтобы добавить публичный ключ (на сервере):

```bash
sudo mkdir -p /home/test_machina/.ssh
# вставьте одну строку публичного ключа, которую прислал преподаватель
echo 'ssh-ed25519 AAAA... teacher@example.com' | sudo tee -a /home/test_machina/.ssh/authorized_keys
sudo chown -R test_machina:test_machina /home/test_machina/.ssh
sudo chmod 700 /home/test_machina/.ssh
sudo chmod 600 /home/test_machina/.ssh/authorized_keys
```

- Преподаватель сможет подключиться со своей машины:

```bash
ssh -i /path/to/their_private_key test_machina@158.160.22.96
# либо просто
ssh test_machina@158.160.22.96
# (если приватный ключ в ~/.ssh/id_ed25519 и ssh-agent настроен)
```

- Важно: после проверки не забудьте удалить ключ преподавателя из `authorized_keys`, если доступ должен быть временным. Пример удаления строки:

```bash
sudo sed -i '\|ssh-ed25519 AAAA... teacher@example.com|d' /home/test_machina/.ssh/authorized_keys
```

4) Быстрый альтернативный вариант (если вы не даёте SSH)

- Вы можете создать временного суперпользователя Django и отправить логин/пароль преподавателю. Пример команды (на сервере):

```bash
# интерактивно
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# или без интерактива (пример):
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('teacher','teacher@example.com','S3cureP@ss')" | docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell
```

- После этого преподаватель сможет зайти в админку: `http://158.160.22.96/admin/`.

5) Если преподаватель хочет запускать docker-compose/команды

- Дайте SSH-доступ (см. пункт 2). После входа в систему можно выполнять команды:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml exec backend bash
# например, выполнить миграции
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput
```

6) Что проверить в Django перед доступом по публичному IP

- ALLOWED_HOSTS: если DEBUG=False, в `.env` должно быть `ALLOWED_HOSTS=158.160.22.96` (порт в ALLOWED_HOSTS не указывается).
- DEBUG: для публичного доступа желательно `DEBUG=False`.
- SECRET_KEY: в продакшне должен быть безопасный ключ и он не должен быть в репозитории.

7) Безопасность, на что обратить внимание перед раздачей доступа

- Не отправляйте приватные ключи.
- Закройте/ограничьте доступ к Postgres (порт 5432) — лучше не публиковать этот порт наружу или ограничить доступ по IP / firewall.
- Redis в вашем примере проброшен на 127.0.0.1:6379 — это нормально для локального использования.
- После ревью удалите публичный ключ преподавателя из `authorized_keys`, если доступ временный.

---

## Запуск тестов и линтеров (локально)

Перед пушем/PR:

- Форматирование/сортировка импортов:

```bash
isort --profile black .
black .
```

- Проверка стиля и линтеры:

```bash
flake8 .
```

- Запуск тестов:

```bash
pytest --maxfail=1 --disable-warnings -q
```

Если `black`/`isort` предлагают автоправки, лучше применить их и закоммитить.

---

## Что делает CI (GitHub Actions)

Workflow: `.github/workflows/ci-cd.yml`.

Триггеры:

- push в ветки `develop` и `main`
- pull_request в `develop` и `main`
- manual (workflow_dispatch)

Jobs:

- lint_and_tests:
    - запускает контейнеры PostgreSQL и Redis как сервисы
    - устанавливает зависимости
    - запускает flake8, isort (check-only) и black (check)
    - запускает pytest
- build_images:
    - зависит от lint_and_tests
    - проверяет сборку docker-образа локально (не пушит)
- deploy:
    - выполняется только при push в ветку `main`
    - использует SSH (appleboy/ssh-action) и выполняет деплой на удалённый сервер через docker compose prod

В CI в job `lint_and_tests` в переменных окружения уже прописан
`SECRET_KEY: test-secret-key` и `DEBUG: 'True'` — это сделано, чтобы тесты и импорт настроек работали в CI.

---

## Чек‑лист для учителя (быстрая проверка)

Публичный IP: 158.160.22.96

- [ ] Открыть публичный URL: `http://158.160.22.96/` и проверить, что приложение работает.
- [ ] Открыть Swagger: `http://158.160.22.96/api/schema/swagger-ui/`.
- [] Админка:  `http://158.160.22.96/admin/`.
- [ ] При необходимости подключиться по SSH (попросить у автора публичный ключ для доступа или прислать свой публичный ключ).
