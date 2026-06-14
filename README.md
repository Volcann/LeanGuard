# LeanGuard

> **Motorcycle Blind Spot Detection — CARLA Simulation Research Platform**

LeanGuard is a research-grade Python system for motorcycle Blind Spot Detection (BSD) built on the CARLA simulator. It implements a layered false-positive suppression architecture, probabilistic alert triggering, and intent-aware threat prioritisation — validated under adversarial simulation scenarios and targeting IEEE publication.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [Development](#development)
  - [Linting & Formatting](#linting--formatting)
  - [Testing](#testing)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## Overview

LeanGuard addresses the core failure modes in published motorcycle ADAS research that commercial systems (e.g. Chigee) cannot resolve — specifically false positives from static infrastructure, alert oscillation near the TTC threshold, and single-point threat prioritisation under bilateral blind-spot scenarios.

The system is implemented in Python against the CARLA simulator, which provides ground-truth kinematics, raw per-point radar returns, and scriptable NPC behaviour — enabling research findings that project analytically to real-hardware deployment.

The research contribution in two sentences: *"This work demonstrates that motorcycle blind spot detection requires a layered false positive suppression architecture: geometric lean-angle filtering, velocity-coherent infrastructure rejection (DEDR), and point-cloud shape discrimination (GRSA) operating in parallel. Alert decisions are upgraded from deterministic thresholds to probabilistic risk-of-collision mass (RoCM) with intent-aware priority scoring (KIATS), with the system's residual failure modes quantified under adversarial lean-phase injection (LPAI)."*

---

## Research Features

| # | Feature | What it solves |
|---|---------|----------------|
| 1 | **DEDR** — Doppler Ego-Motion Decoupling for Velocity-Coherent Infrastructure Rejection | Suppresses static infrastructure FPs (parked vehicles, barriers) at all times using radar radial velocity vs. expected ego-motion velocity |
| 2 | **GRSA** — Geometric Radar Return Signature Analysis for Object Class Discrimination | Distinguishes narrow NPC motorcycles from guardrail segments using DBSCAN clustering + spatial aspect ratio, velocity coherence, and angular subtended metrics |
| 3 | **RoCM** — Probabilistic TTC with Risk-of-Collision Mass Alert Trigger | Replaces deterministic TTC threshold with a Monte Carlo posterior probability, eliminating alert oscillation near the boundary via hysteresis |
| 4 | **KIATS** — Kinematic Intent Estimation via Acceleration-Weighted Threat Score | Prioritises accelerating threats over constant-velocity threats at equal TTC using a first-order Taylor expansion of TTC under observed acceleration |
| 5 | **LPAI** — Lean-Phase Adversarial Injection with Co-Located Threat Concealment | Adversarial scenario design that quantifies the lean filter's worst-case miss rate when a narrow-profile NPC co-locates with the suppression zone at activation |

**Engineering foundation**

- ✅ Modular `src/` layout following PEP 517/518 standards
- ✅ `uv`-managed dependencies with lockfile for reproducible builds
- ✅ Docker & Docker Compose support
- ✅ Pre-commit hooks (Ruff, Black, Mypy)
- ✅ Makefile-driven developer workflow
- ✅ Full type annotations

---

## Tech Stack

| Layer          | Technology                                                         |
|----------------|--------------------------------------------------------------------|
| Language       | Python 3.12+                                                       |
| Simulation     | [CARLA](https://carla.org/) 0.9.15                                 |
| Inference      | ONNX Runtime                                                       |
| Radar Cluster  | DBSCAN (scikit-learn)                                              |
| Messaging      | MQTT (paho-mqtt)                                                   |
| Package Mgr    | [uv](https://github.com/astral-sh/uv)                             |
| Linting        | [Ruff](https://docs.astral.sh/ruff/)                               |
| Formatting     | [Black](https://black.readthedocs.io/)                             |
| Type Checking  | [Mypy](https://mypy-lang.org/)                                     |
| Testing        | [Pytest](https://pytest.org/)                                      |
| Container      | Docker + Docker Compose                                            |

---

## Project Structure

```
LeanGuard/
├── src/
│   └── shared/             # Shared utilities and base modules
├── .editorconfig           # Editor normalisation rules
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hook configuration
├── CHANGELOG.md            # Version history
├── docker-compose.yml      # Local Docker orchestration
├── Makefile                # Developer workflow shortcuts
├── pyproject.toml          # Project metadata & tool configuration
├── README.md               # This file
└── uv.lock                 # Locked dependency graph
```

---

## Getting Started

### Prerequisites

| Tool   | Minimum Version | Install                                  |
|--------|-----------------|------------------------------------------|
| Python | 3.12            | [python.org](https://www.python.org/)    |
| uv     | 0.4+            | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | 24+             | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Make   | any             | Pre-installed on most Linux/macOS        |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/LeanGuard.git
cd LeanGuard

# 2. Create virtual environment and install dependencies
make install
```

### Environment Setup

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env
```

See [Configuration](#configuration) for a full description of each variable.

### Running Locally

```bash
# Start the application
make run

# Or directly
uv run python -m leanguard
```

### Running with Docker

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Tear down
make docker-down
```

---

## Development

### Linting & Formatting

```bash
# Run linter (Ruff)
make lint

# Auto-fix lint issues
make lint-fix

# Run formatter (Black)
make format

# Run type checker (Mypy)
make typecheck
```

### Testing

```bash
# Run full test suite
make test

# Run with coverage report
make test-cov

# Run a specific test file
uv run pytest tests/path/to/test_file.py -v
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To install them:

```bash
make hooks
```

To run hooks manually against all files:

```bash
uv run pre-commit run --all-files
```

---

## Configuration

All runtime configuration is managed through environment variables. Copy `.env.example` to `.env` and fill in the required values.

| Variable        | Required | Default | Description                        |
|-----------------|----------|---------|------------------------------------|
| `APP_ENV`       | Yes      | `dev`   | Environment (`dev`, `staging`, `prod`) |
| `LOG_LEVEL`     | No       | `INFO`  | Logging verbosity                  |
| `SECRET_KEY`    | Yes      | —       | Application secret key             |

> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes with tests
4. Ensure all checks pass: `make ci`
5. Open a Pull Request against `main`

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) (coming soon) for our code of conduct and PR guidelines.

---

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a full version history.

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

<p align="center">Built with ❤️ using Python &amp; <a href="https://github.com/astral-sh/uv">uv</a></p>
