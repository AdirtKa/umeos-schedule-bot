# Telegram Bot Template

Базовый шаблон Telegram-бота на Python 3.12 и aiogram 3.

## Что внутри

- aiogram 3
- uv
- pydantic-settings
- Ruff
- pre-commit
- pytest + pytest-asyncio
- Docker / Docker Compose
- GitHub Actions
- persistent `/app/data` volume
- ротация Docker-логов

## Структура

```text
.
├── src/
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   ├── repositories/
│   ├── services/
│   ├── utils/
│   ├── config.py
│   ├── logger.py
│   └── main.py
├── tests/
├── data/
├── docker/
├── .github/workflows/
├── .env.example
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── ruff.toml
```

## Быстрый старт

```bash
cp .env.example .env
```

Укажи `BOT_TOKEN`.

```bash
make install
make run
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f bot
```

Данные, которые должны переживать пересоздание контейнера, сохраняй в `/app/data`.
В `docker-compose.yml` эта папка привязана к папке на сервере:

```text
./data -> /app/data
```

Путь на сервере можно поменять через `.env`:

```env
BOT_DATA_DIR=./data
```

Например:

```text
/app/data/bot.db
/app/data/schedules
/app/data/access.log
/app/data/error.log
```

Чтобы не потерять данные на сервере:

1. Не удаляй папку из `BOT_DATA_DIR`.
2. Перед `docker compose down -v` сделай бэкап папки `data`.
3. Если раньше использовался Docker volume `bot_data`, сначала скопируй его в папку:

```bash
docker compose down
mkdir -p data
docker volume ls | grep bot_data
docker run --rm -v ИМЯ_VOLUME:/from -v "$PWD/data:/to" alpine sh -c "cp -a /from/. /to/"
docker compose up -d --build
```

`ИМЯ_VOLUME` обычно похоже на `umeos-schedule-bot_bot_data`, но точное имя лучше взять из `docker volume ls`.

## Проверки

```bash
make lint
make format
make test
make check
```

## Создание uv.lock

После первого клонирования шаблона:

```bash
uv lock
```

Затем `uv.lock` рекомендуется закоммитить.
