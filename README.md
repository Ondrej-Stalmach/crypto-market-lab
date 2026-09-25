# Crypto Market Lab

An asynchronous Python workspace with read-only public market-data clients for Binance, Bybit, and Kraken. It provides small exchange-specific APIs and runnable examples; it does not place orders or require API credentials.

## Supported Data

| Connector | Market data |
| --- | --- |
| Binance | Active USDT spot pairs and USD-margined futures pairs via `get_usdt_trading_pairs()` |
| Bybit | Active USDT spot pairs and linear futures pairs via `get_usdt_trading_pairs()` |
| Kraken | Active USD-quoted spot and tradeable, non-expired futures pairs via `get_usd_trading_pairs()` |

`KrakenClient.get_tickers(market="spot")` also returns USD-quoted ticker data. It preserves Kraken's raw response shape: spot tickers are a mapping and futures tickers are a list.

Each client receives an `httpx.AsyncClient` from the caller. The caller owns its lifecycle and can configure timeouts, transport, and other HTTP behavior. HTTP status errors are raised by HTTPX; exchange-level response errors use the connector's `*APIError` exception.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

Install the pinned Python version if needed, then sync the workspace:

```sh
uv python install 3.12
uv sync --locked
```

## Usage

```python
import asyncio

import httpx

from connector_binance import BinanceClient


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as http_client:
        pairs = await BinanceClient(http_client).get_usdt_trading_pairs()

    print(f"Spot pairs: {len(pairs['spot'])}")
    print(f"Futures pairs: {len(pairs['futures'])}")


asyncio.run(main())
```

## Examples

```sh
uv run python examples/binance_trading_pairs.py
uv run python examples/bybit_trading_pairs.py
uv run python examples/kraken_usd_ticker_volumes.py
```

The Kraken example builds sorted 24-hour volume tables with pandas. Exchange APIs can change, apply rate limits, or be unavailable in some regions.

## Development

The connector tests use mocked HTTP responses and do not make live exchange requests.

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

See [docs/architecture.md](docs/architecture.md) for package boundaries and workspace conventions.

## License

No open-source license has been selected yet. Public visibility does not grant permission to reuse this code.
