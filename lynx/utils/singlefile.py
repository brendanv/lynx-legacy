import os
from typing import Optional

import httpx


def is_singlefile_enabled() -> bool:
  return len(get_singlefile_url()) > 0


def get_singlefile_url() -> str:
  return os.getenv('SINGLEFILE_URL', '')


async def get_singlefile_content(url) -> Optional[str]:
  if not is_singlefile_enabled():
    return None

  async with httpx.AsyncClient(timeout=30) as client:
    response = await client.post(get_singlefile_url(), data={'url': url})
    response.raise_for_status()
    return response.text
