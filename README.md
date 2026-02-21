# Cover Letter Generator

Загрузите резюме (PDF/DOCX) и укажите ссылку на вакансию — сервис сгенерирует сопроводительное письмо с помощью LLM (OpenAI или Anthropic).

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Заполните API-ключи в .env

docker compose up --build
```

Приложение будет доступно по адресу **http://localhost:3000**.

## Локальная разработка

### Backend

```bash
cd backend
uv sync
cp ../.env.example .env
# Заполните API-ключи в .env
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

## Стек

- **Backend**: Python, FastAPI, LangChain, uv
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Инфраструктура**: Docker, docker-compose, nginx
