from __future__ import annotations

import asyncio
import logging
import os

import httpx

from memesensei.core.config.models import load_config

logger = logging.getLogger(__name__)


async def poll_status():
    config = load_config()
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(f"http://localhost:{config.core_api_port}/status")
                resp.raise_for_status()
                logger.info("core status: %s", resp.json())
            except Exception as exc:  # pragma: no cover
                logger.error("failed to poll status: %s", exc)
            await asyncio.sleep(5)


def main():
    asyncio.run(poll_status())


if __name__ == "__main__":
    main()
