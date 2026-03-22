
# Prefer the docker-compose binary, fall back to the Docker Compose V2 plugin
COMPOSE := $(shell (command -v docker-compose >/dev/null 2>&1 && echo docker-compose) || (docker compose version >/dev/null 2>&1 && echo "docker compose") || echo "")

ifeq ($(COMPOSE),)
$(error Docker Compose not found. Install `docker-compose` or the Docker Compose plugin (see README.md))
endif

.PHONY: build up down logs ps stop

build:
	$(COMPOSE) build --parallel

up:
	$(COMPOSE) up -d --remove-orphans --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

stop:
	$(COMPOSE) stop

run:
	# Start services and print common endpoints
	$(MAKE) up
	@echo ""
	@echo "Services started. Endpoints:"
	@echo " - Web UI: http://localhost:5000"
	@echo " - API: http://localhost:3000"
	@echo ""
	$(COMPOSE) ps
