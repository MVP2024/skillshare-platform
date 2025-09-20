# SkillShare Platform Backend

Краткое и понятное руководство для разработчиков и преподавателя, который будет проверять проект.

Badges: Django, DRF, Python, PostgreSQL, Docker

---

## Что в репозитории

Это бэкенд на Django + Django REST Framework для учебной платформы (курсы, уроки, платежи, пользователи). Основные папки
и файлы:

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
docker-compose up -d --build
```

После запуска сайт будет доступен по: http://localhost:8001/ (порт проброшен на 8001 в `docker-compose.yaml`).
Документация API: http://localhost:8001/api/schema/swagger-ui/

6. Команды внутри контейнера (пример):

```bash
# выполнить миграции
docker-compose exec backend python manage.py migrate --noinput
# загрузить тестовые данные (фикстура)
docker-compose exec backend python manage.py load_initial_data
# создать суперпользователя
docker-compose exec backend python manage.py createsuperuser
```

7. Остановка:

```bash
docker-compose down -v
```

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

Важно для ревьюера (учителя): в CI в job `lint_and_tests` в переменных окружения уже прописан
`SECRET_KEY: test-secret-key` и `DEBUG: 'True'` — это сделано, чтобы тесты и импорт настроек работали в CI. Поэтому CI
тесты не должны падать из-за отсутствия SECRET_KEY.

---

## Деплой на удалённый сервер (VM) — вручную

Предполагается, что сервер — Linux (например Ubuntu). Нужно Docker и Docker Compose v2.

1. Установите Docker и docker compose (пример для Ubuntu):

```bash
# установить Docker (по официальной инструкции)
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
# добавить пользователя в группу docker (по желанию)
sudo usermod -aG docker $USER
```

Перезайдите в сессию, если добавляли пользователя в группу docker.

2. Клонируйте репозиторий и подготовьте `.env` на сервере (в production используйте безопасный SECRET_KEY и реальные
   значения):

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> /opt/skillshare
cd /opt/skillshare
cp .env.example .env
# Отредактируйте .env: укажите SECRET_KEY, DEBUG=False, базу данных, stripe ключи, REDIS и т.д.
```

3. Запустите продакшн compose (пример):

```bash
# из директории проекта
docker compose -f docker-compose.prod.yml up -d --build
# запустить миграции и collectstatic
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
```

4. Проверка состояния:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
# проверить что контейнер backend в статусе healthy (если настроено) и nginx слушает порт 80
```

5. Скрипт deploy

В папке `deploy/` есть `deploy.sh` — можно запускать его вручную на сервере. Скрипт ожидает, что в `DEPLOY_PATH` есть
`.env`.

## Создание VM в Yandex Cloud (UI — пошагово, простой вариант)

Ниже — подробные шаги, которые понятны учителю или любому другому проверяющему. Мы предполагаем Ubuntu 22.04 LTS и что у
вас есть доступ в консоль Yandex Cloud.

1. Войдите в Yandex Cloud Console: https://console.cloud.yandex.ru/
2. Выберите облако (Cloud) и каталог (Folder).
3. Перейдите в Compute Cloud → VM instances → Create instance.
4. Заполните поля:
    - Name: skillshare-backend (или любое другое понятное имя).
    - Zone: выберите доступную зону, например ru-central1-a.
    - Image: Ubuntu 22.04 LTS.
    - Resources: 1 vCPU, 1–2 GB RAM (для теста достаточно), дисковое пространство 20 GB.
    - External IP: включите «Assign public IPv4 address» (или создайте зарезервированный IP — см. пункт ниже).
    - SSH keys: вставьте содержимое вашего публичного SSH-ключа (~/.ssh/id_ed25519.pub). Имя пользователя для SSH будет
      показано в UI (обычно ubuntu/yc-user).
5. Создайте/проверьте правила брандмауэра (Security group / Network security):
    - Откройте порты: TCP 22 (SSH), TCP 80 (HTTP), TCP 443 (HTTPS).
    - При необходимости откройте TCP 8001, если вы хотите, чтобы бэкенд слушал напрямую на этом порту.
6. Нажмите Create. После запуска запомните внешний IP (Public IPv4).

Резервирование (статический) внешнего IP — рекомендовано:

- В Console: Network → External IP addresses → Create external IPv4 address (Reserved). Привяжите адрес к вашей VM или
  оставьте неподвязанным и привяжите позже.
- Преимущество: IP не меняется после перезапуска VM.

Подключение по SSH:

- ssh ubuntu@<PUBLIC_IP>  (пользователь смотрите в UI)

Установка Docker и Docker Compose (на VM, Ubuntu):

```bash
# обновление и необходимые пакеты
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
# установка Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
# (по желанию) добавить пользователя в группу docker
sudo usermod -aG docker $USER
# перезайдите в сессию, если добавляли в группу
```

Далее на сервере:

```bash
# клонируем проект
sudo mkdir -p /opt/skillshare
sudo chown $(whoami) /opt/skillshare
git clone https://github.com/<your-repo> /opt/skillshare
cd /opt/skillshare
cp .env.example .env
# отредактируйте .env — обязательно SECRET_KEY, DEBUG=False, DB и REDIS значения
# запустите prod compose
docker compose -f docker-compose.prod.yml up -d --build
# миграции и сбор статичных файлов
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput || true
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput || true
```

Проверка:

- Откройте http://<PUBLIC_IP>/ — должен быть доступен Swagger UI (если backend успешно поднялся и nginx проксирует
  запросы).
- Просмотрите логи: docker compose -f docker-compose.prod.yml logs -f backend

---

## Создание VM в Yandex Cloud с помощью CLI (yc) — коротко

Если у вас настроен Yandex CLI (yc), можно создать инстанс командой (пример):

```bash
# создаём инстанс с публичным IP (пример)
yc compute instance create \
  --name skillshare-backend \
  --zone ru-central1-a \
  --public-ip \
  --image-family ubuntu-2204-lts \
  --platform standard-v1 \
  --memory 2 \
  --cores 1 \
  --ssh-key ~/.ssh/id_ed25519.pub
```

Получение публичного IP (пример):

```bash
yc compute instance get --name skillshare-backend --format json | jq -r '.network_interfaces[0].primary_v4_address.one_to_one_nat.address'
```

Дальше выполняйте те же шаги по подключению, установке Docker и деплою, что описано выше.


## Чек‑лист для учителя (быстрая проверка)
Публичный IP 158.160.22.96

Ниже — пошаговый список с чекбоксами, чтобы быстро проверить проект во время ревью.
Учитель может пройти пункты по порядку.

- [ ] CI: Открыть GitHub Actions → запустить workflow (или проверить последний прогон) и убедиться, что jobs
  `Lint and Tests` и `Build Docker images (check)` проходят.
- [ ] Локальный запуск: следуя разделу «Быстрый старт», поднять проект локально через Docker Compose и проверить, что
  Swagger UI доступен по http://localhost:8001/api/schema/swagger-ui/.
- [ ] Тесты: выполнить `pytest -q` и убедиться, что все тесты проходят.
- [ ] Линтеры: запустить `flake8 .`, `black --check .`, `isort --check-only --profile black .` — предупреждений быть не
  должно.
- [ ] Демонстрация функционала (по шагам):
    - [ ] Зарегистрироваться (POST /api/users/),
    - [ ] Получить токен (POST /api/token/),
    - [ ] Создать курс / урок (если это предусмотрено для вашей роли),
    - [ ] Инициировать платёж (POST /api/payments/create/) — в тестовом режиме Stripe возвращает ссылку (если
      STRIPE_SECRET_KEY настроен),
    - [ ] Проверить подписки на курс (POST /api/courses/subscribe/).
- [ ] Деплой (опционально): если вы развернули проект на VM с публичным IP, открыть публичный IP или домен и проверить,
  что API и Swagger доступны (http/https).



---

## GitHub Secrets и .env — что настроить (список и примеры)

1) GitHub Secrets (используются в workflow для деплоя и / или доступа по SSH):

- SSH_PRIVATE_KEY — приватный SSH ключ (PEM/OPENSSH) для подключения к серверу при деплое (размещается в secret и
  используется appleboy/ssh-action). Значение: содержимое приватного ключа (id_ed25519 или id_rsa).
- SSH_HOST (или SERVER_HOST) — публичный IP или доменное имя сервера (для удобства можно оставить пустым для локальных
  прогонов, но для deploy должен быть задан).
- SSH_USERNAME (или SERVER_USER) — пользователь на сервере (например ubuntu или deploy).
- SSH_PORT (опционально) — порт SSH (по умолчанию 22).
- DEPLOY_PATH — путь на сервере, например /opt/skillshare (скрипт deploy будет работать с этой папкой).

Рекомендация: добавьте SSH_PRIVATE_KEY как секрет в репозитории: Settings → Secrets and variables → Actions → New
repository secret.

2) Переменные .env на сервере (production) — пример значений (в файле .env, НЕ в репозитории):

```
# Django
SECRET_KEY=very-secret-production-key
DEBUG=False
ALLOWED_HOSTS=your.domain.com,123.45.67.89

# Database
DB_NAME=skillshare
DB_USER=skillshare_user
DB_PASSWORD=very-db-password
DB_HOST=db  # внутри docker-compose это имя сервиса
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Stripe
STRIPE_SECRET_KEY=sk_test_...
BASE_URL=https://your.domain.com

# Email (production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=smtp_user
EMAIL_HOST_PASSWORD=smtp_password
DEFAULT_FROM_EMAIL=webmaster@your.domain.com
```

Примечания:

- Никогда не храните реальные секреты в репозитории. Используйте .env на сервере и GitHub Secrets для pipeline/Actions.
- В docker-compose.prod.yml сервисы читают `.env` (env_file: ./.env). Убедитесь, что файл находится в DEPLOY_PATH на
  сервере и заполнен корректно.

3) CI (локальные значения для прогонов тестов в Actions):

- В workflow уже задана переменная SECRET_KEY=test-secret-key и DEBUG='True' для job `lint_and_tests`. Это безопасно для
  CI, но в продакшне используйте настоящий SECRET_KEY.

---

## Использование скрипта deploy/create_yc_vm.sh

В репозитории добавлен скрипт deploy/create_yc_vm.sh — он упрощает создание VM в Yandex Cloud и подготовку SSH‑ключа для
деплоя.

Пример использования:

```
# создать VM и зарезервировать IP (опционально)
./deploy/create_yc_vm.sh --name skillshare-backend --zone ru-central1-a --reserve-ip
```

Скрипт сохраняет приватный ключ в deploy/yc_deploy_key — не коммитьте его, а вставьте содержимое как GitHub Secret
`SSH_PRIVATE_KEY`.
