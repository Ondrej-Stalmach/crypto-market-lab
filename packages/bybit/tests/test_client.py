import unittest

import httpx

from connector_bybit import BybitClient


class BybitClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_usdt_trading_pairs_filters_and_paginates(self) -> None:
        responses = {
            ("spot", ""): {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {"symbol": "BTCUSDT", "quoteCoin": "USDT", "status": "Trading"},
                        {"symbol": "OLDUSDT", "quoteCoin": "USDT", "status": "Closed"},
                        {"symbol": "BTCUSDC", "quoteCoin": "USDC", "status": "Trading"},
                    ],
                    "nextPageCursor": "spot-next",
                },
            },
            ("spot", "spot-next"): {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {"symbol": "ETHUSDT", "quoteCoin": "USDT", "status": "Trading"},
                    ],
                    "nextPageCursor": "",
                },
            },
            ("linear", ""): {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {"symbol": "BTCUSDT", "quoteCoin": "USDT", "status": "Trading"},
                        {"symbol": "ETHUSDC", "quoteCoin": "USDC", "status": "Trading"},
                        {
                            "symbol": "NEWUSDT",
                            "quoteCoin": "USDT",
                            "status": "PreLaunch",
                        },
                    ],
                    "nextPageCursor": "linear-next",
                },
            },
            ("linear", "linear-next"): {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {"symbol": "ETHUSDT", "quoteCoin": "USDT", "status": "Trading"},
                    ],
                    "nextPageCursor": "",
                },
            },
        }
        requested_pages: list[tuple[str, str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            category = request.url.params["category"]
            cursor = request.url.params.get("cursor", "")
            requested_pages.append((category, cursor, request.url.params["limit"]))
            return httpx.Response(200, json=responses[(category, cursor)])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            pairs = await BybitClient(http_client).get_usdt_trading_pairs()

        self.assertEqual(
            pairs,
            {"spot": ["BTCUSDT", "ETHUSDT"], "futures": ["BTCUSDT", "ETHUSDT"]},
        )
        self.assertCountEqual(
            requested_pages,
            [
                ("spot", "", "1000"),
                ("spot", "spot-next", "1000"),
                ("linear", "", "1000"),
                ("linear", "linear-next", "1000"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
