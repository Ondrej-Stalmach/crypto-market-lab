import asyncio

import httpx

from connector_kraken import KrakenClient


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as http_client:
        client = KrakenClient(http_client)
        tickers = await client.get_spot_tickers()
        print(tickers)
        print(f"Retrieved {len(tickers)} tickers.")


if __name__ == "__main__":
    asyncio.run(main())
