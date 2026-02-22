.PHONY: up down build

# Запуск для прода: backend + frontend в Docker
up:
	docker compose up --build

# Запуск в фоне
up-d:
	docker compose up --build -d

# Остановка
down:
	docker compose down

# Только пересборка образов
build:
	docker compose build
