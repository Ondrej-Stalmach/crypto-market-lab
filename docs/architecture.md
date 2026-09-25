# Workspace Architecture

## Current Scope

This repository is a `uv` workspace containing three independently packaged, asynchronous public REST clients for cryptocurrency exchanges: Binance, Bybit, and Kraken. Each connector owns its exchange-specific API client. There is currently no shared `connector_core`, research package, or notebooks directory.

## Relevant Layout

```text
crypto-market-lab/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .python-version
├── AGENTS.md
├── README.md
├── docs/
│   └── architecture.md
├── examples/
│   ├── binance_trading_pairs.py
│   ├── bybit_trading_pairs.py
│   ├── kraken_kline.py
│   ├── kraken_tickers.py
│   └── kraken_trading_pairs.py
├── packages/
│   ├── binance/
│   │   ├── pyproject.toml
│   │   ├── src/connector_binance/
│   │   └── tests/
│   ├── bybit/
│   │   ├── pyproject.toml
│   │   ├── src/connector_bybit/
│   │   └── tests/
│   └── kraken/
│       ├── pyproject.toml
│       ├── src/connector_kraken/
│       └── tests/
├── pyproject.toml
└── uv.lock
```

The root `pyproject.toml` defines the workspace member pattern as `packages/*` and depends on each connector as a workspace package so examples and tests work after a normal `uv sync`. Each connector follows the `src` layout, with its tests kept alongside the package.

## Package Conventions

| Directory | Project name | Import package |
| --- | --- | --- |
| `packages/binance` | `connector-binance` | `connector_binance` |
| `packages/bybit` | `connector-bybit` | `connector_bybit` |
| `packages/kraken` | `connector-kraken` | `connector_kraken` |

Exchange-specific implementation belongs in the matching connector. Add shared abstractions only when there is a demonstrated need across connectors; do not assume a core package already exists.

If one workspace package depends on another, declare the dependency in its project metadata and map it to the workspace in `[tool.uv.sources]`:

```toml
[project]
dependencies = ["connector-core"]

[tool.uv.sources]
connector-core = { workspace = true }
```

The root project and all three connectors declare Python `>=3.12`; `.python-version` pins the workspace interpreter to Python 3.12. The root project depends on the three connectors, `httpx`, and `pandas`. Its development dependency group contains `ipykernel`, `pytest`, and `ruff`; each connector depends on `httpx`.

## Development

Use `uv` to sync the workspace and run examples and checks:

```sh
uv sync --locked
uv run python examples/binance_trading_pairs.py
uv run python examples/bybit_trading_pairs.py
uv run python examples/kraken_trading_pairs.py
uv run python examples/kraken_tickers.py
uv run python examples/kraken_kline.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Connector tests live under each package's `tests/` directory and use mocked HTTP responses. The same checks run in GitHub Actions.