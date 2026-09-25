import asyncio
from datetime import datetime, timezone

import httpx

from connector_kraken import KrakenClient

PAIR = "XBTUSD"
INTERVAL_MINUTES = 1


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as http_client:
        klines = await KrakenClient(http_client).get_kline(
            PAIR,
            interval=INTERVAL_MINUTES,
        )

    print(f"Downloaded {len(klines)} {INTERVAL_MINUTES}-minute candles for {PAIR}.")
    for kline in klines[-5:]:
        candle_time = datetime.fromtimestamp(kline["time"], tz=timezone.utc)
        print(
            f"{candle_time.isoformat()} "
            f"open={kline['open']} high={kline['high']} "
            f"low={kline['low']} close={kline['close']} "
            f"volume={kline['volume']} count={kline['count']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
