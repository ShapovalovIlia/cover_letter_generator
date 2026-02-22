# Cover Letter Generator

Загрузите резюме (PDF / DOCX) и укажите ссылку на вакансию — сервис сгенерирует сопроводительное письмо с помощью OpenAI LLM.

## Быстрый старт (прода / Docker)

Одна команда — поднимает backend и frontend:

```bash
cp .env.example .env
# Заполните OPENAI_API_KEY в .env

make up
```

Или без Make: `docker compose up --build`.

Приложение будет доступно по адресу **http://localhost:3000**. Остановка: `make down` или Ctrl+C.

## Локальная разработка

### Backend

```bash
cd backend
uv sync
cp ../.env .env          # или создайте .env в корне репозитория
uv run uvicorn src.app:app --reload
```

API будет доступен на `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev-сервер запустится на `http://localhost:5173` с проксированием `/api/*` на backend.

## Тесты

```bash
cd backend
uv run pytest
```

## Линтинг и форматирование

В проекте настроены pre-commit хуки (`ruff`, `mypy`). Для первичной установки:

```bash
cd backend
uv sync --group dev
uv run pre-commit install
```

Ручной запуск:

```bash
uv run ruff check backend/
uv run ruff format backend/
uv run --directory backend mypy
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `OPENAI_API_KEY` | API-ключ OpenAI | — (обязательно) |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## Стек

- **Backend**: Python 3.13, FastAPI, LangChain, uv
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS
- **Инфраструктура**: Docker, docker-compose, Nginx
- **Качество кода**: ruff, mypy, pre-commit, pytest
