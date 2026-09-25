import asyncio

import httpx
import pandas as pd

from connector_kraken import KrakenClient


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as http_client:
        trading_pairs = await KrakenClient(http_client).get_spot_trading_pairs()

    print(f"Spot ({len(trading_pairs)} active USD pairs)")
    pairs_frame = pd.DataFrame({"symbol": trading_pairs})
    print(pairs_frame.head().to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
