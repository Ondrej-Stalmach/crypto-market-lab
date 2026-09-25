import unittest
from decimal import Decimal

import httpx

from connector_kraken import KrakenAPIError, KrakenClient


class KrakenClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_spot_tickers_returns_complete_spot_metrics(self) -> None:
        responses = {
            "/0/public/Ticker": {
                "error": [],
                "result": {
                    "ACU/USD": {
                        "o": "0.12570000",
                        "h": ["0.13680000", "0.13680000"],
                        "l": ["0.12350000", "0.12350000"],
                        "c": ["0.13370000", "74.76031"],
                        "v": ["407542.59580", "446050.95406"],
                        "p": ["0.13065444", "0.13028153"],
                    },
                    "ACU/EUR": {
                        "o": "53000",
                        "h": ["55000", "56000"],
                        "l": ["52000", "51000"],
                        "c": ["54000", "0.001"],
                        "v": ["1", "2"],
                        "p": ["53000", "53000"],
                    },
                    "ACUUSD": {},
                },
            },
        }
        requested_paths: list[str] = []
        ticker_parameters: list[tuple[str | None, str | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            if request.url.path == "/0/public/Ticker":
                ticker_parameters.append(
                    (
                        request.url.params.get("assetVersion"),
                        request.url.params.get("pair"),
                    )
                )
            return httpx.Response(200, json=responses[request.url.path])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            metrics = await KrakenClient(http_client).get_spot_tickers()

        self.assertEqual(
            metrics,
            [
                {
                    "pair": "ACU/USD",
                    "open": Decimal("0.12570000"),
                    "high_price": Decimal("0.13680000"),
                    "low_price": Decimal("0.12350000"),
                    "close_price": Decimal("0.13370000"),
                    "volume_usd_today_thousands": 53,
                    "volume_usd_24h_thousands": 58,
                }
            ],
        )
        self.assertEqual(requested_paths, ["/0/public/Ticker"])
        self.assertEqual(ticker_parameters, [("1", None)])

    async def test_get_kline_returns_candles_for_pair_and_interval(self) -> None:
        responses = {
            "/0/public/OHLC": {
                "error": [],
                "result": {
                    "XXBTZUSD": [
                        [
                            1711929600,
                            "70000.1000",
                            "70100.2000",
                            "69900.3000",
                            "70050.4000",
                            "70025.5000",
                            "1.2500",
                            42,
                        ]
                    ],
                    "last": 1711929600,
                },
            },
        }
        requested_paths: list[str] = []
        requested_parameters: list[tuple[str | None, str | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            requested_parameters.append(
                (
                    request.url.params.get("pair"),
                    request.url.params.get("interval"),
                )
            )
            return httpx.Response(200, json=responses[request.url.path])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            klines = await KrakenClient(http_client).get_kline("XBTUSD", interval=15)

        self.assertEqual(
            klines,
            [
                {
                    "time": 1711929600,
                    "open": Decimal("70000.1000"),
                    "high": Decimal("70100.2000"),
                    "low": Decimal("69900.3000"),
                    "close": Decimal("70050.4000"),
                    "vwap": Decimal("70025.5000"),
                    "volume": Decimal("1.2500"),
                    "count": 42,
                }
            ],
        )
        self.assertEqual(requested_paths, ["/0/public/OHLC"])
        self.assertEqual(requested_parameters, [("XBTUSD", "15")])

    async def test_get_kline_raises_for_kraken_api_error(self) -> None:
        requested_intervals: list[str | None] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_intervals.append(request.url.params.get("interval"))
            return httpx.Response(
                200,
                json={
                    "error": ["EQuery:Unknown asset pair"],
                    "result": {"last": 0},
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            with self.assertRaisesRegex(KrakenAPIError, "Unknown asset pair"):
                await KrakenClient(http_client).get_kline("UNKNOWN")
        self.assertEqual(requested_intervals, ["1"])

    async def test_get_kline_rejects_invalid_candle_data(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"error": [], "result": {"XXBTZUSD": [[1, "70000"]], "last": 1}},
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            with self.assertRaisesRegex(KrakenAPIError, "invalid candle"):
                await KrakenClient(http_client).get_kline("XBTUSD")

    async def test_get_spot_trading_pairs_returns_online_usd_alt_names(
        self,
    ) -> None:
        responses = {
            "/0/public/AssetPairs": {
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "altname": "XBTUSD",
                        "quote": "ZUSD",
                        "status": "online",
                    },
                    "XXBTEUR": {
                        "altname": "XBTEUR",
                        "quote": "ZEUR",
                        "status": "online",
                    },
                    "OLDUSD": {
                        "altname": "OLDUSD",
                        "quote": "ZUSD",
                        "status": "cancel_only",
                    },
                    "NOALTUSD": {"quote": "ZUSD", "status": "online"},
                },
            },
        }
        requested_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            return httpx.Response(200, json=responses[request.url.path])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            pairs = await KrakenClient(http_client).get_spot_trading_pairs()

        self.assertEqual(
            pairs,
            ["XBTUSD"],
        )
        self.assertEqual(requested_paths, ["/0/public/AssetPairs"])


if __name__ == "__main__":
    unittest.main()
