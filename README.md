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

Например:

```text
/app/data/schedule.json
```

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
