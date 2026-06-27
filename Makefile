SHELL          := /bin/bash
.DEFAULT_GOAL  := help

dc             := docker compose
success        := ✔ done

-include .env
export

CARLA_ROOT     ?= /opt/carla-simulator
APP_MODULE     ?= simulation
PYGAME_MODULE  ?= simulation.viewer
CACHE_DIRS     := __pycache__ .mypy_cache .ruff_cache .pytest_cache htmlcov dist

BOLD   := \033[1m
RESET  := \033[0m
GREEN  := \033[32m
CYAN   := \033[36m
YELLOW := \033[33m

.PHONY: help
help:
	@echo ""
	@printf "  $(BOLD)$(CYAN)LeanGuard — Available Targets$(RESET)\n"
	@echo ""
	@printf "  $(GREEN)Infrastructure$(RESET)\n"
	@printf "    $(BOLD)up$(RESET)           Start services, stream logs\n"
	@printf "    $(BOLD)up.d$(RESET)         Start services detached (background)\n"
	@printf "    $(BOLD)down$(RESET)         Stop all services\n"
	@printf "    $(BOLD)logs$(RESET)         Tail service logs\n"
	@printf "    $(BOLD)ps$(RESET)           Show container status\n"
	@echo ""
	@printf "  $(GREEN)Simulation$(RESET)\n"
	@printf "    $(BOLD)carla$(RESET)        Launch CARLA server in background (detached)\n"
	@printf "    $(BOLD)carla.stop$(RESET)   Stop the CARLA background server\n"
	@printf "    $(BOLD)carla.status$(RESET) Show CARLA server status\n"
	@echo ""
	@printf "  $(GREEN)Application$(RESET)\n"
	@printf "    $(BOLD)app$(RESET)          Run LeanGuard (python -m simulation)\n"
	@printf "    $(BOLD)pygame$(RESET)       Run Pygame CARLA client via python -m\n"
	@printf "    $(BOLD)build$(RESET)        Build wheel and sdist into dist/\n"
	@echo ""
	@printf "  $(GREEN)Development$(RESET)\n"
	@printf "    $(BOLD)lint$(RESET)         Run ruff linter\n"
	@printf "    $(BOLD)lint-fix$(RESET)     Run ruff with auto-fix\n"
	@printf "    $(BOLD)format$(RESET)       Run black formatter\n"
	@printf "    $(BOLD)format-check$(RESET) Check formatting without applying\n"
	@printf "    $(BOLD)typecheck$(RESET)    Run mypy\n"
	@printf "    $(BOLD)test$(RESET)         Run pytest\n"
	@printf "    $(BOLD)test-cov$(RESET)     Run pytest with coverage\n"
	@printf "    $(BOLD)ci$(RESET)           lint + format-check + typecheck + test\n"
	@printf "    $(BOLD)clean$(RESET)        Remove cache directories\n"
	@echo ""

.PHONY: up
up:
	@$(dc) up

.PHONY: up.d
up.d:
	@$(dc) up -d
	@printf "  MLflow → $(CYAN)http://localhost:5000$(RESET)\n"
	@echo "$(success)"

.PHONY: down
down:
	@$(dc) down --remove-orphans
	@echo "$(success)"

.PHONY: logs
logs:
	@$(dc) logs -f

.PHONY: ps
ps:
	@$(dc) ps

CARLA_LOG_FILE := /tmp/leanguard_carla.log

carla_pid     = $$(ss -tlnp 2>/dev/null | grep ":$(CARLA_PORT) " | grep -oP 'pid=\K[0-9]+' | head -1)
carla_running = ss -tlnp 2>/dev/null | grep -q ":$(CARLA_PORT) "

.PHONY: carla
carla:
	@if [ ! -f "$(CARLA_ROOT)/CarlaUE4.sh" ]; then \
		printf "$(BOLD)\033[31m✗ CarlaUE4.sh not found at $(CARLA_ROOT)$(RESET)\n"; \
		printf "  Set CARLA_ROOT in .env or environment.\n"; \
		exit 1; \
	fi
	@if $(carla_running); then \
		printf "$(YELLOW)⚠ CARLA already running (pid=$(carla_pid), port=$(CARLA_PORT))$(RESET)\n"; \
		exit 0; \
	fi
	@printf "  Starting CARLA on port $(CARLA_PORT)"
	@DISPLAY=:0 nohup $(CARLA_ROOT)/CarlaUE4.sh \
		-RenderOffScreen -quality-level=Low \
		-fps=20 -nosound -carla-rpc-port=$(CARLA_PORT) \
		> $(CARLA_LOG_FILE) 2>&1 &
	@i=0; while [ $$i -lt 30 ]; do \
		sleep 1; printf "."; \
		if $(carla_running); then break; fi; \
		i=$$((i+1)); \
	done; printf "\n"
	@if $(carla_running); then \
		printf "  $(GREEN)✔ CARLA started$(RESET) (pid=$(carla_pid), port=$(CARLA_PORT)) → log: $(CARLA_LOG_FILE)\n"; \
	else \
		printf "$(BOLD)\033[31m✗ CARLA failed to start — check log: $(CARLA_LOG_FILE)$(RESET)\n"; \
		exit 1; \
	fi

.PHONY: carla.stop
carla.stop:
	@BINARY=$$(ss -tlnp 2>/dev/null | grep ":$(CARLA_PORT) " | grep -oP 'pid=\K[0-9]+'); \
	if [ -z "$$BINARY" ]; then \
		printf "  $(YELLOW)CARLA is not running$(RESET)\n"; \
		exit 0; \
	fi; \
	WRAPPER=$$(ps -o ppid= -p $$BINARY 2>/dev/null | tr -d ' '); \
	ALL=$$(printf '%s\n%s\n' "$$BINARY" "$$WRAPPER" | grep -v '^[[:space:]]*$$' | sort -u | tr '\n' ' '); \
	printf "  Killing PIDs: $$ALL\n"; \
	echo $$ALL | xargs kill -9 2>/dev/null || true; \
	sleep 1; \
	if $(carla_running); then \
		printf "$(YELLOW)⚠ Port $(CARLA_PORT) still active — try again$(RESET)\n"; \
	else \
		printf "  $(GREEN)✔ CARLA fully stopped$(RESET)\n"; \
	fi

.PHONY: carla.status
carla.status:
	@if $(carla_running); then \
		printf "  $(GREEN)✔ CARLA running$(RESET) (pid=$(carla_pid), port=$(CARLA_PORT))\n"; \
	else \
		printf "  $(YELLOW)✗ CARLA not running$(RESET)\n"; \
	fi


.PHONY: app
app:
	uv run python -m $(APP_MODULE)

.PHONY: pygame
pygame:
	uv run python -m $(PYGAME_MODULE)

.PHONY: build
build:
	uv build
	@echo "$(success)"

.PHONY: lint
lint:
	uv run ruff check src tests

.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix src tests

.PHONY: format
format:
	uv run black src tests

.PHONY: format-check
format-check:
	uv run black --check src tests

.PHONY: precommit
precommit:
	uv run pre-commit run --all-files

.PHONY: typecheck
typecheck:
	uv run mypy src

.PHONY: test
test:
	uv run pytest

.PHONY: test-cov
test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=40

.PHONY: audit
audit:
	uvx --python 3.12 pip-audit

.PHONY: ci
ci: precommit typecheck test-cov audit build

.PHONY: clean
clean:
	@$(foreach d,$(CACHE_DIRS),find . -type d -name "$(d)" -exec rm -rf {} + 2>/dev/null;)
	@echo "$(success)"
