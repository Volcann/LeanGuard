SHELL          := /bin/bash
.DEFAULT_GOAL  := help

dc             := docker compose
success        := ✔ done

-include .env
export

CARLA_ROOT     ?= /opt/carla-simulator
APP_MODULE     ?= leanguard.main
PYGAME_MODULE  ?= leanguard.viewer
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
	@printf "    $(BOLD)carla$(RESET)        Launch native CARLA server (off-screen, low quality)\n"
	@echo ""
	@printf "  $(GREEN)Application$(RESET)\n"
	@printf "    $(BOLD)app$(RESET)          Run LeanGuard via python -m\n"
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

.PHONY: carla
carla:
	@if [ ! -f "$(CARLA_ROOT)/CarlaUE4.sh" ]; then \
		printf "$(BOLD)\033[31m✗ CarlaUE4.sh not found at $(CARLA_ROOT)$(RESET)\n"; \
		printf "  Set CARLA_ROOT in .env or environment.\n"; \
		exit 1; \
	fi
	SDL_VIDEODRIVER=offscreen $(CARLA_ROOT)/CarlaUE4.sh \
		-RenderOffScreen -quality-level=Low -benchmark \
		-fps=20 -nosound -carla-rpc-port=$(CARLA_PORT)

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

.PHONY: typecheck
typecheck:
	uv run mypy src

.PHONY: test
test:
	uv run pytest

.PHONY: test-cov
test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

.PHONY: ci
ci: lint format-check typecheck test

.PHONY: clean
clean:
	@$(foreach d,$(CACHE_DIRS),find . -type d -name "$(d)" -exec rm -rf {} + 2>/dev/null;)
	@echo "$(success)"
