import unittest

import httpx

from connector_kraken import KrakenClient


class KrakenClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_usd_trading_pairs_returns_active_spot_and_futures_symbols(
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
            "/derivatives/api/v3/instruments": {
                "result": "success",
                "instruments": [
                    {
                        "symbol": "PF_XBTUSD",
                        "quote": "USD",
                        "tradeable": True,
                        "isExpired": False,
                    },
                    {
                        "symbol": "PF_ETHUSD",
                        "quote": "USD",
                        "tradeable": False,
                        "isExpired": False,
                    },
                    {
                        "symbol": "PI_OLDUSD",
                        "quote": "USD",
                        "tradeable": True,
                        "isExpired": True,
                    },
                    {
                        "symbol": "PF_XBTEUR",
                        "quote": "EUR",
                        "tradeable": True,
                        "isExpired": False,
                    },
                    {"quote": "USD", "tradeable": True, "isExpired": False},
                ],
            },
        }
        requested_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            return httpx.Response(200, json=responses[request.url.path])

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            pairs = await KrakenClient(http_client).get_usd_trading_pairs()

        self.assertEqual(
            pairs,
            {"spot": ["XBTUSD"], "futures": ["PF_XBTUSD"]},
        )
        self.assertCountEqual(
            requested_paths,
            ["/0/public/AssetPairs", "/derivatives/api/v3/instruments"],
        )


if __name__ == "__main__":
    unittest.main()
