.PHONY: help test dev up down build migrate

# Variables
VENV_BIN = venv/bin
PYTHON = $(VENV_BIN)/python
PYTEST = $(VENV_BIN)/pytest
UVICORN = $(VENV_BIN)/uvicorn
ALEMBIC = $(VENV_BIN)/alembic

help:
	@echo "Comandos disponibles:"
	@echo "  make dev      - Inicia el servidor de desarrollo local (puerto 8080 por defecto)"
	@echo "  make test     - Ejecuta toda la suite de tests localmente"
	@echo "  make up       - Levanta la infraestructura de Docker (Postgres, Redis) en background"
	@echo "  make down     - Apaga y elimina los contenedores de Docker"
	@echo "  make build    - Construye la imagen de Docker de la aplicación principal"
	@echo "  make migrate  - Aplica las migraciones de base de datos pendientes (Alembic)"

dev:
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8080 --reload

test:
	$(PYTEST) tests/

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker build -t finance_bot_api .

migrate:
	$(ALEMBIC) upgrade head
