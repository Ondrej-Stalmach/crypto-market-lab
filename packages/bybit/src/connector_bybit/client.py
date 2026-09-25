import asyncio
from typing import Any, Literal

import httpx

Market = Literal["spot", "futures"]
TradingPairs = dict[Market, list[str]]

_INSTRUMENTS_INFO_URL = "https://api.bybit.com/v5/market/instruments-info"
_PAGE_LIMIT = 1000


class BybitAPIError(RuntimeError):
    """Raised when Bybit returns an unexpected instruments-info response."""


class BybitClient:
    """Fetch public spot and USDT-margined futures data from Bybit."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._http_client = http_client

    async def get_usdt_trading_pairs(self) -> TradingPairs:
        """Return active spot and USDT-margined linear symbols."""
        return await self._fetch_usdt_trading_pairs(self._http_client)

    async def _fetch_usdt_trading_pairs(
        self,
        http_client: httpx.AsyncClient,
    ) -> TradingPairs:
        spot_instruments, futures_instruments = await asyncio.gather(
            self._fetch_instruments(http_client, "spot"),
            self._fetch_instruments(http_client, "futures"),
        )
        return {
            "spot": _usdt_trading_symbols(spot_instruments),
            "futures": _usdt_trading_symbols(futures_instruments),
        }

    async def _fetch_instruments(
        self,
        http_client: httpx.AsyncClient,
        market: Market,
    ) -> list[dict[str, Any]]:
        category = "spot" if market == "spot" else "linear"
        instruments: list[dict[str, Any]] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()

        while True:
            params: dict[str, str | int] = {
                "category": category,
                "limit": _PAGE_LIMIT,
            }
            if cursor is not None:
                params["cursor"] = cursor

            response = await http_client.get(_INSTRUMENTS_INFO_URL, params=params)
            response.raise_for_status()
            payload: Any = response.json()
            if not isinstance(payload, dict):
                raise BybitAPIError(
                    f"Bybit {category} instruments info is not a JSON object"
                )
            if payload.get("retCode") != 0:
                message = payload.get("retMsg") or "unknown error"
                raise BybitAPIError(f"Bybit {category} API error: {message}")

            result = payload.get("result")
            if not isinstance(result, dict):
                raise BybitAPIError(
                    f"Bybit {category} response is missing a result object"
                )

            page = result.get("list")
            if not isinstance(page, list):
                raise BybitAPIError(
                    f"Bybit {category} response is missing an instruments list"
                )
            instruments.extend(item for item in page if isinstance(item, dict))

            next_cursor = result.get("nextPageCursor", "")
            if next_cursor in (None, ""):
                break
            if not isinstance(next_cursor, str):
                raise BybitAPIError(
                    f"Bybit {category} response has an invalid page cursor"
                )
            if next_cursor in seen_cursors:
                raise BybitAPIError(f"Bybit {category} response repeated a page cursor")

            seen_cursors.add(next_cursor)
            cursor = next_cursor

        return instruments


def _usdt_trading_symbols(instruments: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            symbol
            for instrument in instruments
            if instrument.get("quoteCoin") == "USDT"
            and instrument.get("status") == "Trading"
            and isinstance(symbol := instrument.get("symbol"), str)
        }
    )
