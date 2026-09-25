# Crypto Market Lab

An asynchronous Python workspace with read-only public market-data clients for Binance, Bybit, and Kraken. It provides small exchange-specific APIs and runnable examples; it does not place orders or require API credentials.

## Supported Data

| Connector | Market data |
| --- | --- |
| Binance | Active USDT spot pairs and USD-margined futures pairs via `get_usdt_trading_pairs()` |
| Bybit | Active USDT spot pairs and linear futures pairs via `get_usdt_trading_pairs()`; daily futures opens and previous-day USDT turnover |
| Kraken | Active USD spot pairs via `get_spot_trading_pairs()`; ticker metrics via `get_spot_tickers()`; OHLC candles via `get_kline()` |

`KrakenClient.get_spot_tickers()` returns each USD spot pair's open, high, low, latest price, and daily and 24-hour USD volume rounded to whole thousands. Spot volumes are estimated using their respective VWAP values.

`KrakenClient.get_kline(pair, interval=1)` returns up to 720 recent OHLC candles. Valid intervals are `1`, `5`, `15`, `30`, `60`, `240`, `1440`, `10080`, and `21600` minutes. Each candle includes a Unix timestamp in seconds, OHLC prices, VWAP, base-asset volume, and trade count. Kraken includes the current, unfinished candle.

The Kraken connector is spot-only. Existing callers of the former combined `get_usd_trading_pairs()` method should migrate to `get_spot_trading_pairs()` for spot symbols; Kraken futures data is no longer provided.

`BybitClient.get_futures_open_prices()` returns today's UTC daily-candle open for each USDT linear futures pair. `get_yesterday_futures_volumes()` returns the previous UTC day's quote turnover in USDT, not the candle's base-asset volume.

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
uv run python examples/kraken_trading_pairs.py
uv run python examples/kraken_tickers.py
uv run python examples/kraken_kline.py
```

The Kraken ticker example prints USD spot ticker metrics and estimated turnover. The kline example prints the latest five candles. Exchange APIs can change, apply rate limits, or be unavailable in some regions.

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
