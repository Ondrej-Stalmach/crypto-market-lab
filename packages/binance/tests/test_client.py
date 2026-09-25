import unittest

import httpx

from connector_binance import BinanceClient


class BinanceClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_usdt_trading_pairs_filters_active_symbols(self) -> None:
        responses = {
            "/api/v3/exchangeInfo": {
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "quoteAsset": "USDT",
                        "status": "TRADING",
                        "isSpotTradingAllowed": True,
                    },
                    {
                        "symbol": "INACTIVEUSDT",
                        "quoteAsset": "USDT",
                        "status": "BREAK",
                        "isSpotTradingAllowed": True,
                    },
                    {
                        "symbol": "DISABLEDUSDT",
                        "quoteAsset": "USDT",
                        "status": "TRADING",
                        "isSpotTradingAllowed": False,
                    },
                    {
                        "symbol": "BTCUSDC",
                        "quoteAsset": "USDC",
                        "status": "TRADING",
                        "isSpotTradingAllowed": True,
                    },
                ]
            },
            "/fapi/v1/exchangeInfo": {
                "symbols": [
                    {"symbol": "ETHUSDT", "quoteAsset": "USDT", "status": "TRADING"},
                    {"symbol": "BTCUSDT", "quoteAsset": "USDT", "status": "TRADING"},
                    {
                        "symbol": "INACTIVEUSDT",
                        "quoteAsset": "USDT",
                        "status": "PENDING_TRADING",
                    },
                    {"symbol": "BTCUSDC", "quoteAsset": "USDC", "status": "TRADING"},
                ]
            },
        }
        requested_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            return httpx.Response(200, json=responses[request.url.path])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            pairs = await BinanceClient(http_client).get_usdt_trading_pairs()

        self.assertEqual(
            pairs, {"spot": ["BTCUSDT"], "futures": ["BTCUSDT", "ETHUSDT"]}
        )
        self.assertCountEqual(
            requested_paths,
            ["/api/v3/exchangeInfo", "/fapi/v1/exchangeInfo"],
        )


if __name__ == "__main__":
    unittest.main()
