import asyncio

import httpx
import pandas as pd

from connector_bybit import BybitClient


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as http_client:
        trading_pairs = await BybitClient(http_client).get_usdt_trading_pairs()

    for market, symbols in trading_pairs.items():
        print(f"{market.title()} ({len(symbols)} active USDT pairs)")
        pairs_frame = pd.DataFrame({"symbol": symbols})
        print(pairs_frame.head().to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
