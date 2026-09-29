"""Makes exactly one provider request; never prints credentials."""
import asyncio
import sys

import httpx

from app.config import get_settings
from app.market import MarketError, fetch_quote


async def main():
    async with httpx.AsyncClient() as client:
        try:
            quote = await fetch_quote(get_settings(), client)
            print(quote.model_dump_json())
        except MarketError as error:
            print(error.message, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
