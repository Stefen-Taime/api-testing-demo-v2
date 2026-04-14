PYTHON ?= python3
NPM ?= npm
PLAYWRIGHT ?= npx playwright
JMETER ?= jmeter
DOCKER_COMPOSE ?= docker compose
HOST ?= 127.0.0.1
PORT ?= 8000
TEST_ARGS ?=
UI_ARGS ?=

.PHONY: help run serve test test-fast test-ui test-all ui-install load stress token docker-up docker-down docker-logs docker-zap clean

help:
	@printf "Targets:\n"
	@printf "  make run        # demarre l'API en mode reload\n"
	@printf "  make serve      # demarre l'API sans reload\n"
	@printf "  make test       # lance pytest contre un vrai serveur HTTP temporaire\n"
	@printf "  make test-fast  # lance pytest sans la suite reliability\n"
	@printf "  make ui-install # installe Playwright et Chromium\n"
	@printf "  make test-ui    # lance les tests Playwright\n"
	@printf "  make test-all   # lance test + test-ui\n"
	@printf "  make load       # lance le plan JMeter de charge\n"
	@printf "  make stress     # lance le plan JMeter de stress\n"
	@printf "  make token      # genere un JWT local de demonstration\n"
	@printf "  make docker-up  # demarre la stack Docker Compose\n"
	@printf "  make docker-down # arrete la stack Docker Compose\n"
	@printf "  make docker-logs # affiche les logs Docker Compose\n"
	@printf "  make docker-zap # lance le profil ZAP\n"
	@printf "  make clean      # supprime les artefacts de test\n"

run:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

serve:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT)

test:
	$(PYTHON) -m pytest $(TEST_ARGS)

test-fast:
	$(PYTHON) -m pytest -m "not reliability" $(TEST_ARGS)

ui-install:
	$(NPM) install
	$(PLAYWRIGHT) install chromium

test-ui:
	$(NPM) run ui:test -- $(UI_ARGS)

test-all: test test-ui

load:
	$(JMETER) -n -t jmeter/load-test-plan.jmx -l jmeter/load-results.jtl

stress:
	$(JMETER) -n -t jmeter/stress-test-plan.jmx -l jmeter/stress-results.jtl

token:
	$(PYTHON) scripts/issue_demo_token.py --user tester

docker-up:
	$(DOCKER_COMPOSE) up -d --build

docker-down:
	$(DOCKER_COMPOSE) down -v

docker-logs:
	$(DOCKER_COMPOSE) logs -f --tail=200

docker-zap:
	$(DOCKER_COMPOSE) --profile security up --build zap

clean:
	rm -rf test-results playwright-report
	rm -f jmeter/*.jtl
