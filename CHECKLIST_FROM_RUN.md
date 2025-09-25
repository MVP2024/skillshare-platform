Проверка для пользователя — быстрые шаги

Демо URL (публичный IP): http://158.160.22.96/
Swagger UI: http://158.160.22.96/api/schema/swagger-ui/

PR для проверки кода: https://github.com/MVP2024/skillshare-platform/pull/13

Короткая инструкция для проверки

1) Откройте в браузере http://158.160.22.96/ или Swagger UI по ссылке выше.
   - В Swagger можно посмотреть все эндпоинты и выполнить запросы прямо из UI.

2) Быстрая проверка через curl

- Проверка корня:
  curl -i http://158.160.22.96/

- Получение схемы OpenAPI:
  curl -i http://158.160.22.96/api/schema/

- Регистрация (пример):
  curl -X POST "http://158.160.22.96/api/users/" -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"pass123"}'

- Получить токен (пример):
  curl -X POST "http://158.160.22.96/api/token/" -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"pass123"}'

Если эндпоинты недоступны

- Вариант 1: контейнеры не запущены или сервисы упали. Попросите студента или подключитесь по SSH и выполните:
  ssh <user>@158.160.22.96
  cd /opt/skillshare  # или путь, где развернут проект
  docker compose -f docker-compose.prod.yml ps
  docker compose -f docker-compose.prod.yml logs -f backend

- Вариант 2: отсутствует .env или неверные настройки — проверьте на сервере наличие .env и корректные значения (SECRET_KEY, DB, REDIS и т.д.).
