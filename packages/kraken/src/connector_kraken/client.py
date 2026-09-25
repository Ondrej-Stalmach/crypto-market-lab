import asyncio
from typing import Any, Literal

import httpx

Market = Literal["spot", "futures"]
TradingPairs = dict[Market, list[str]]
TickerResult = dict[str, Any] | list[dict[str, Any]]

_SPOT_API_URL = "https://api.kraken.com/0/public"
_FUTURES_TICKERS_URL = "https://futures.kraken.com/derivatives/api/v3/tickers"
_FUTURES_INSTRUMENTS_URL = "https://futures.kraken.com/derivatives/api/v3/instruments"


class KrakenAPIError(RuntimeError):
    """Raised when Kraken returns an API-level error."""


class KrakenClient:
    """Fetch public spot and futures market data from Kraken."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._http_client = http_client

    async def get_tickers(self, market: Market = "spot") -> TickerResult:
        """Return raw Kraken tickers for USD-quoted pairs in the selected market."""
        if market not in {"spot", "futures"}:
            raise ValueError("market must be 'spot' or 'futures'")

        return await self._fetch_tickers(self._http_client, market)

    async def get_usd_trading_pairs(self) -> TradingPairs:
        """Return active spot and futures symbols quoted in USD."""
        return await self._fetch_usd_trading_pairs(self._http_client)

    async def _fetch_tickers(
        self,
        http_client: httpx.AsyncClient,
        market: Market,
    ) -> TickerResult:
        if market == "spot":
            return await self._get_spot_tickers(http_client)
        return await self._get_futures_tickers(http_client)

    async def _fetch_usd_trading_pairs(
        self,
        http_client: httpx.AsyncClient,
    ) -> TradingPairs:
        spot_pairs, futures_pairs = await asyncio.gather(
            self._get_spot_trading_pairs(http_client),
            self._get_futures_trading_pairs(http_client),
        )
        return {"spot": spot_pairs, "futures": futures_pairs}

    async def _get_spot_tickers(
        self,
        http_client: httpx.AsyncClient,
    ) -> dict[str, Any]:
        pairs_response = await http_client.get(f"{_SPOT_API_URL}/AssetPairs")
        pairs = _spot_result(pairs_response)
        selected_pairs = [
            pair_id
            for pair_id, pair in pairs.items()
            if isinstance(pair, dict)
            and _normalize_quote_currency(pair.get("quote")) == "USD"
        ]
        if not selected_pairs:
            return {}

        ticker_response = await http_client.get(
            f"{_SPOT_API_URL}/Ticker",
            params={"pair": ",".join(selected_pairs)},
        )
        tickers = _spot_result(ticker_response)
        selected_pair_ids = set(selected_pairs)
        return {
            pair_id: ticker
            for pair_id, ticker in tickers.items()
            if pair_id in selected_pair_ids
        }

    async def _get_spot_trading_pairs(
        self,
        http_client: httpx.AsyncClient,
    ) -> list[str]:
        response = await http_client.get(
            f"{_SPOT_API_URL}/AssetPairs",
            params={"assetVersion": 1, "aclass_base": "currency"},
        )
        pairs = _spot_result(response)
        return sorted(
            {
                symbol
                for pair in pairs.values()
                if isinstance(pair, dict)
                and _normalize_quote_currency(pair.get("quote")) == "USD"
                and pair.get("status") == "online"
                and isinstance(symbol := pair.get("altname"), str)
            }
        )

    async def _get_futures_tickers(
        self,
        http_client: httpx.AsyncClient,
    ) -> list[dict[str, Any]]:
        response = await http_client.get(_FUTURES_TICKERS_URL)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise KrakenAPIError("Kraken futures response is not a JSON object")
        if payload.get("result") != "success":
            error = payload.get("errors") or payload.get("error") or "unknown error"
            raise KrakenAPIError(f"Kraken futures API error: {error}")

        tickers = payload.get("tickers")
        if not isinstance(tickers, list):
            raise KrakenAPIError("Kraken futures response is missing tickers")
        return [
            ticker
            for ticker in tickers
            if isinstance(ticker, dict) and _futures_quote(ticker.get("pair")) == "USD"
        ]

    async def _get_futures_trading_pairs(
        self,
        http_client: httpx.AsyncClient,
    ) -> list[str]:
        response = await http_client.get(_FUTURES_INSTRUMENTS_URL)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise KrakenAPIError("Kraken futures response is not a JSON object")
        if payload.get("result") != "success":
            error = payload.get("errors") or payload.get("error") or "unknown error"
            raise KrakenAPIError(f"Kraken futures API error: {error}")

        instruments = payload.get("instruments")
        if not isinstance(instruments, list):
            raise KrakenAPIError("Kraken futures response is missing instruments")
        return sorted(
            {
                symbol
                for instrument in instruments
                if isinstance(instrument, dict)
                and instrument.get("tradeable") is True
                and not instrument.get("isExpired", False)
                and _normalize_quote_currency(instrument.get("quote")) == "USD"
                and isinstance(symbol := instrument.get("symbol"), str)
            }
        )


def _spot_result(response: httpx.Response) -> dict[str, Any]:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise KrakenAPIError("Kraken spot response is not a JSON object")

    errors = payload.get("error", [])
    if errors:
        message = ", ".join(str(error) for error in errors)
        raise KrakenAPIError(f"Kraken spot API error: {message}")

    result = payload.get("result")
    if not isinstance(result, dict):
        raise KrakenAPIError("Kraken spot response is missing a result object")
    return result


def _normalize_quote_currency(quote: Any) -> str | None:
    if not isinstance(quote, str):
        return None
    return quote.removeprefix("Z").upper()


def _futures_quote(pair: Any) -> str | None:
    if not isinstance(pair, str) or ":" not in pair:
        return None
    return pair.rsplit(":", maxsplit=1)[1].upper()
