COMPOSE=docker-compose

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
