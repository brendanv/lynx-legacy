import os
from typing import Optional
import httpx
import json


def is_singlefile_enabled() -> bool:
  return len(get_singlefile_url()) > 0


def get_singlefile_url() -> str:
  return os.getenv('SINGLEFILE_URL', '')


async def get_singlefile_content(url,
                                 cookies: Optional[list[str]] = None
                                 ) -> Optional[str]:
  if not is_singlefile_enabled():
    return None

  async with httpx.AsyncClient(timeout=30) as client:
    data = {'url': url}
    if cookies is not None:
      data['cookies'] = json.dumps(cookies)
    response = await client.post(get_singlefile_url(), data=data)
    response.raise_for_status()
    return response.text
