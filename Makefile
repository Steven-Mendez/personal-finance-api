.PHONY: help sync run test test-unit test-integration test-e2e test-all test-cov \
        docker-build docker-run docker-stop docker-up docker-down docker-restart docker-logs \
        ruff mypy precommit

APP_HOST ?= 127.0.0.1
APP_PORT ?= 8000
APP_ENTRYPOINT ?= app/main.py
UV ?= uv
UV_RUN ?= $(UV) run
SYNC_FLAGS ?= --all-groups
PYTEST_FLAGS ?= -ra --strict-markers --maxfail=1
TEST_ARGS ?= -v
E2E_TEST_ARGS ?= $(TEST_ARGS)
ALL_TEST_ARGS ?= $(TEST_ARGS)

DOCKER_IMAGE ?= personal-finance-api
DOCKER_TAG ?= latest
DOCKER_CONTAINER ?= personal-finance-api
DOCKER_PORT ?= 8000
DOCKER_COMPOSE ?= docker compose

help:
	@BOLD=$$(printf '\033[1m'); \
	BLUE=$$(printf '\033[34m'); \
	CYAN=$$(printf '\033[36m'); \
	GREEN=$$(printf '\033[32m'); \
	YELLOW=$$(printf '\033[33m'); \
	RESET=$$(printf '\033[0m'); \
	if [ -n "$$NO_COLOR" ] || [ ! -t 1 ]; then \
		BOLD=""; BLUE=""; CYAN=""; GREEN=""; YELLOW=""; RESET=""; \
	fi; \
	printf "%s%sPersonal Finance API - Makefile help%s\n\n" "$$BOLD" "$$BLUE" "$$RESET"; \
	printf "%sOverview%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  Use this Makefile for setup, local run, and test workflows.\n"; \
	printf "  E2E tests run in-process via FastAPI TestClient fixtures.\n"; \
	printf "  test-e2e and test-all invoke pytest directly (no wrapper scripts).\n\n"; \
	printf "%sCommands%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  %smake sync%s\n" "$$GREEN" "$$RESET"; \
	printf "      Install or update dependencies (%suv sync %s%s)\n" "$$YELLOW" "$(SYNC_FLAGS)" "$$RESET"; \
	printf "  %smake run%s\n" "$$GREEN" "$$RESET"; \
	printf "      Start FastAPI dev server (%s host=%s port=%s)\n" "$(APP_ENTRYPOINT)" "$(APP_HOST)" "$(APP_PORT)"; \
	printf "  %smake test%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run all tests except e2e\n"; \
	printf "  %smake test-unit%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run unit tests only\n"; \
	printf "  %smake test-integration%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run integration tests only\n"; \
	printf "  %smake test-e2e%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run E2E tests only\n"; \
	printf "  %smake test-all%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run full test suite (unit + integration + E2E)\n"; \
	printf "  %smake test-cov%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run full test suite with coverage report\n\n"; \
	printf "%sDocker commands%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  %smake docker-build%s\n" "$$GREEN" "$$RESET"; \
	printf "      Build the Docker image (%s:%s)\n" "$(DOCKER_IMAGE)" "$(DOCKER_TAG)"; \
	printf "  %smake docker-run%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run a standalone container on port %s\n" "$(DOCKER_PORT)"; \
	printf "  %smake docker-stop%s\n" "$$GREEN" "$$RESET"; \
	printf "      Stop the standalone container\n"; \
	printf "  %smake docker-up%s\n" "$$GREEN" "$$RESET"; \
	printf "      Start services with Docker Compose (detached)\n"; \
	printf "  %smake docker-down%s\n" "$$GREEN" "$$RESET"; \
	printf "      Stop and remove Docker Compose services\n"; \
	printf "  %smake docker-restart%s\n" "$$GREEN" "$$RESET"; \
	printf "      Restart Docker Compose services (down then up)\n"; \
	printf "  %smake docker-logs%s\n" "$$GREEN" "$$RESET"; \
	printf "      Tail logs from Docker Compose api service\n\n"; \
	printf "%sCode quality%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  %smake ruff%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run Ruff linter (--fix) then Ruff formatter on the whole codebase\n"; \
	printf "  %smake mypy%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run Mypy static type-checker against the app package\n"; \
	printf "  %smake precommit%s\n" "$$GREEN" "$$RESET"; \
	printf "      Run all pre-commit hooks against every file in the repo\n\n"; \
	printf "%sVariable overrides%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  APP_ENTRYPOINT='%s'  FastAPI entrypoint used by make run\n" "$(APP_ENTRYPOINT)"; \
	printf "  APP_HOST='%s'        Host used by make run\n" "$(APP_HOST)"; \
	printf "  APP_PORT='%s'        Port used by make run\n" "$(APP_PORT)"; \
	printf "  PYTEST_FLAGS='%s'  Base pytest flags\n" "$(PYTEST_FLAGS)"; \
	printf "  TEST_ARGS='%s'       Extra args for test, test-unit, test-integration\n" "$(TEST_ARGS)"; \
	printf "  E2E_TEST_ARGS='%s'   Extra args for test-e2e\n" "$(E2E_TEST_ARGS)"; \
	printf "  ALL_TEST_ARGS='%s'   Extra args for test-all\n" "$(ALL_TEST_ARGS)"; \
	printf "  DOCKER_IMAGE='%s'  Docker image name\n" "$(DOCKER_IMAGE)"; \
	printf "  DOCKER_TAG='%s'      Docker image tag\n" "$(DOCKER_TAG)"; \
	printf "  DOCKER_PORT='%s'     Host port for docker-run\n\n" "$(DOCKER_PORT)"; \
	printf "%sExamples%s\n" "$$BOLD$$CYAN" "$$RESET"; \
	printf "  %smake run APP_HOST=0.0.0.0 APP_PORT=9000%s\n" "$$GREEN" "$$RESET"; \
	printf "  %smake test TEST_ARGS='-q'%s\n" "$$GREEN" "$$RESET"; \
	printf "  %smake test-e2e E2E_TEST_ARGS='-q -k readiness'%s\n" "$$GREEN" "$$RESET"; \
	printf "  %smake test-all ALL_TEST_ARGS='-q'%s\n" "$$GREEN" "$$RESET"; \
	printf "  %smake docker-build DOCKER_TAG=v1.0.0%s\n" "$$GREEN" "$$RESET"; \
	printf "  %smake docker-run DOCKER_PORT=9000%s\n\n" "$$GREEN" "$$RESET"; \
	printf "Run %smake help%s anytime to print this guide.\n\n" "$$GREEN" "$$RESET"

sync:
	$(UV) sync $(SYNC_FLAGS)

run:
	$(UV_RUN) fastapi dev $(APP_ENTRYPOINT) --host $(APP_HOST) --port $(APP_PORT)

test:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(TEST_ARGS) -m "not e2e"

test-unit:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(TEST_ARGS) tests/unit

test-integration:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(TEST_ARGS) -m integration

test-e2e:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(E2E_TEST_ARGS) -m e2e

test-all:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(ALL_TEST_ARGS)

test-cov:
	$(UV_RUN) pytest $(PYTEST_FLAGS) $(ALL_TEST_ARGS) --cov --cov-fail-under=80

docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run:
	docker run --rm -d \
		--name $(DOCKER_CONTAINER) \
		-p $(DOCKER_PORT):8000 \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-stop:
	docker stop $(DOCKER_CONTAINER)

docker-up:
	$(DOCKER_COMPOSE) up --build -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-restart: docker-down docker-up

docker-logs:
	$(DOCKER_COMPOSE) logs -f api

ruff:
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

mypy:
	$(UV_RUN) mypy app

db-migrate:
	$(UV_RUN) alembic upgrade head

db-check:
	$(UV_RUN) alembic check

precommit:
	$(UV_RUN) pre-commit run --all-files
