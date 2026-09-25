import asyncio
from typing import Any, Literal

import httpx

Market = Literal["spot", "futures"]
TradingPairs = dict[Market, list[str]]

_SPOT_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
_FUTURES_EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"


class BinanceAPIError(RuntimeError):
    """Raised when Binance returns an unexpected exchange-info response."""


class BinanceClient:
    """Fetch public spot and USDT-margined futures data from Binance."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._http_client = http_client

    async def get_usdt_trading_pairs(self) -> TradingPairs:
        """Return active spot and futures symbols quoted in USDT."""
        return await self._fetch_usdt_trading_pairs(self._http_client)

    async def _fetch_usdt_trading_pairs(
        self,
        http_client: httpx.AsyncClient,
    ) -> TradingPairs:
        spot_response, futures_response = await asyncio.gather(
            http_client.get(_SPOT_EXCHANGE_INFO_URL),
            http_client.get(_FUTURES_EXCHANGE_INFO_URL),
        )
        return {
            "spot": _usdt_trading_symbols(spot_response, "spot"),
            "futures": _usdt_trading_symbols(futures_response, "futures"),
        }


def _usdt_trading_symbols(response: httpx.Response, market: Market) -> list[str]:
    response.raise_for_status()
    payload: Any = response.json()
    if not isinstance(payload, dict):
        raise BinanceAPIError(f"Binance {market} exchange info is not a JSON object")

    symbols = payload.get("symbols")
    if not isinstance(symbols, list):
        raise BinanceAPIError(f"Binance {market} exchange info is missing symbols")

    active_symbols: set[str] = set()
    for instrument in symbols:
        if not isinstance(instrument, dict):
            continue
        if (
            instrument.get("quoteAsset") != "USDT"
            or instrument.get("status") != "TRADING"
        ):
            continue
        if market == "spot" and instrument.get("isSpotTradingAllowed") is False:
            continue

        symbol = instrument.get("symbol")
        if isinstance(symbol, str):
            active_symbols.add(symbol)

    return sorted(active_symbols)
