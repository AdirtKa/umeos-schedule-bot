.PHONY: install run lint format test check up down logs help


help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

install: ## Установить зависимости и pre-commit
	uv sync
	uv run pre-commit install

run: ## Запустить бота
	uv run python -m src.main

test: ## Запустить тесты
	uv run pytest

lint: ## Проверить Ruff
	uv run ruff check .

format: ## Отформатировать код
	uv run ruff format .

check: ## скан всех файлов по конфигу в пре коммит
	uv run pre-commit run --all-files

up: ## переспобрать контейнеры
	docker compose up -d --build

down: ## выключить контейнеры
	docker compose down

logs: ## посмотреть логи
	docker compose logs -f bot
