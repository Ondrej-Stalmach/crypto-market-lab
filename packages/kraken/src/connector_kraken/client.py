from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, TypedDict

import httpx

TradingPairs = list[str]


class SpotTickerMetric(TypedDict):
    pair: str
    open: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume_usd_today_thousands: int
    volume_usd_24h_thousands: int


class Kline(TypedDict):
    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    vwap: Decimal
    volume: Decimal
    count: int


_SPOT_API_URL = "https://api.kraken.com/0/public"


class KrakenAPIError(RuntimeError):
    """Raised when Kraken returns an API-level error."""


class KrakenClient:
    """Fetch public USD spot market data from Kraken."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._http_client = http_client

    async def get_spot_tickers(self) -> list[SpotTickerMetric]:
        """Return USD spot prices and today's and 24-hour volumes in thousands."""
        ticker_response = await self._http_client.get(
            f"{_SPOT_API_URL}/Ticker",
            params={"assetVersion": 1},
        )
        tickers = _response_result(ticker_response, "spot")

        spot_metrics: list[SpotTickerMetric] = []
        for pair_id, ticker in tickers.items():
            if not pair_id.upper().endswith("/USD"):
                continue
            if not isinstance(ticker, dict):
                raise KrakenAPIError(
                    f"Kraken spot ticker for {pair_id} is not an object"
                )

            high_prices = ticker.get("h")
            low_prices = ticker.get("l")
            close_prices = ticker.get("c")
            volumes = ticker.get("v")
            average_prices = ticker.get("p")
            if (
                not isinstance(high_prices, list)
                or not high_prices
                or not isinstance(low_prices, list)
                or not low_prices
                or not isinstance(close_prices, list)
                or not close_prices
                or not isinstance(volumes, list)
                or len(volumes) < 2
                or not isinstance(average_prices, list)
                or len(average_prices) < 2
            ):
                raise KrakenAPIError(
                    f"Kraken spot ticker for {pair_id} is missing price or volume data"
                )

            try:
                open_price = Decimal(str(ticker.get("o")))
                high_price = Decimal(str(high_prices[0]))
                low_price = Decimal(str(low_prices[0]))
                close_price = Decimal(str(close_prices[0]))
                volume_today = Decimal(str(volumes[0]))
                vwap_today = Decimal(str(average_prices[0]))
                volume_24h = Decimal(str(volumes[1]))
                vwap_24h = Decimal(str(average_prices[1]))
            except (InvalidOperation, ValueError) as error:
                raise KrakenAPIError(
                    f"Kraken spot ticker for {pair_id} has invalid price or volume data"
                ) from error

            if not all(
                value.is_finite()
                for value in (
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume_today,
                    vwap_today,
                    volume_24h,
                    vwap_24h,
                )
            ):
                raise KrakenAPIError(
                    f"Kraken spot ticker for {pair_id} has invalid price or volume data"
                )

            spot_metrics.append(
                {
                    "pair": pair_id,
                    "open": open_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "close_price": close_price,
                    "volume_usd_today_thousands": int(
                        (volume_today * vwap_today / Decimal("1000")).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "volume_usd_24h_thousands": int(
                        (volume_24h * vwap_24h / Decimal("1000")).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP
                        )
                    ),
                }
            )

        return sorted(spot_metrics, key=lambda metric: metric["pair"])

    async def get_kline(self, pair: str, interval: int = 1) -> list[Kline]:
        """Return OHLC candles for a spot pair at the requested minute interval."""
        response = await self._http_client.get(
            f"{_SPOT_API_URL}/OHLC",
            params={"pair": pair, "interval": interval},
        )
        result = _response_result(response, "OHLC")

        pair_candles = [candles for key, candles in result.items() if key != "last"]
        if len(pair_candles) != 1 or not isinstance(pair_candles[0], list):
            raise KrakenAPIError("Kraken OHLC response is missing a candle array")

        klines: list[Kline] = []
        for candle in pair_candles[0]:
            if not isinstance(candle, list) or len(candle) != 8:
                raise KrakenAPIError("Kraken OHLC response contains an invalid candle")

            try:
                timestamp = int(candle[0])
                open_price, high_price, low_price, close_price, vwap, volume = (
                    Decimal(str(value)) for value in candle[1:7]
                )
                count = int(candle[7])
            except (InvalidOperation, OverflowError, TypeError, ValueError) as error:
                raise KrakenAPIError(
                    "Kraken OHLC response contains invalid candle data"
                ) from error

            if not all(
                value.is_finite()
                for value in (
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    vwap,
                    volume,
                )
            ):
                raise KrakenAPIError(
                    "Kraken OHLC response contains invalid candle data"
                )

            klines.append(
                {
                    "time": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "vwap": vwap,
                    "volume": volume,
                    "count": count,
                }
            )

        return klines

    async def get_spot_trading_pairs(self) -> TradingPairs:
        """Return USD spot pairs available for normal trading.

        Only `online` pairs are included. Restricted statuses are excluded:
        `cancel_only` allows canceling existing orders; `post_only` allows only
        maker orders; `limit_only` allows only limit orders; `reduce_only` allows
        only reducing an existing position.
        """
        response = await self._http_client.get(
            f"{_SPOT_API_URL}/AssetPairs",
            params={"assetVersion": 1, "aclass_base": "currency"},
        )
        pairs = _response_result(response, "spot")

        return sorted(
            {
                symbol
                for pair in pairs.values()
                if isinstance(pair, dict)
                and pair.get("status") == "online"
                and isinstance(symbol := pair.get("altname"), str)
                and symbol.upper().endswith("USD")
            }
        )


def _response_result(response: httpx.Response, endpoint: str) -> dict[str, Any]:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise KrakenAPIError(f"Kraken {endpoint} response is not a JSON object")

    errors = payload.get("error", [])
    if errors:
        message = ", ".join(str(error) for error in errors)
        raise KrakenAPIError(f"Kraken {endpoint} API error: {message}")

    result = payload.get("result")
    if not isinstance(result, dict):
        raise KrakenAPIError(f"Kraken {endpoint} response is missing a result object")
    return result
