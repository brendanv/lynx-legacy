import json
from datetime import datetime
from typing import Optional
from django.http.request import HttpRequest

from bs4 import BeautifulSoup
import httpx
import readtime
from django.utils import timezone
from readability import Document
import trafilatura
from trafilatura.settings import use_config
from urllib.parse import urlparse
from lynx.errors import UrlParseError
from lynx.transforms import apply_all_transforms

from .models import Link, UserCookie, UserSetting
from .url_context import UrlContext


async def load_content_from_remote_url(url_context: UrlContext) -> str:
  domain = urlparse(url_context.url).netloc
  cookies = UserCookie.objects.filter(user=url_context.user,
                                      cookie_domain=domain)
  cookie_data = {
      cookie.cookie_name: cookie.cookie_value
      async for cookie in cookies
  }
  setting, _ = await UserSetting.objects.aget_or_create(user=url_context.user)

  try:
    async with httpx.AsyncClient(cookies=cookie_data,
                                 headers=setting.headers_for_scraping,
                                 follow_redirects=True) as client:
      response = await client.get(url_context.url)
      response.raise_for_status()
      return response.text
  except httpx.HTTPError as e:
    raise UrlParseError(str(e))


def parse_content(url_context: UrlContext, content: str) -> dict[str, str]:
  # Required to avoid signals not on main thread error
  new_config = use_config()
  new_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
  extracted_json_str = trafilatura.extract(content,
                                           include_links=True,
                                           include_formatting=True,
                                           include_images=True,
                                           output_format='json',
                                           config=new_config)
  if extracted_json_str is not None:
    json_meta = json.loads(str(extracted_json_str))
  else:
    json_meta = {}

  article_date = datetime.strptime(json_meta['date'], '%Y-%m-%d').date(
  ) if 'date' in json_meta and json_meta['date'] else timezone.now()

  summary_html = apply_all_transforms(content,
                                      url_context).prettify(formatter='html')
  read_time = readtime.of_html(summary_html)
  domain = urlparse(url_context.url).netloc
  model_args = {
      'original_url': url_context.url,
      'user': url_context.user,
      'cleaned_url': json_meta.get('source') or url_context.url,
      'hostname': json_meta.get('hostname') or domain,
      'article_date': article_date,
      'author': json_meta.get('author') or 'Unknown Author',
      'title': json_meta.get('title') or Document(content).title(),
      'excerpt': json_meta.get('excerpt') or '',
      'article_html': summary_html,
      'raw_text_content': json_meta.get('raw_text') or BeautifulSoup(content).get_text(),
      'full_page_html': content,
      'header_image_url': json_meta.get('image') or '',
      'read_time_seconds': read_time.seconds,
      'read_time_display': read_time.text
  }
  return model_args


async def parse_url(url: str,
                    user,
                    model_fields: Optional[dict] = None) -> Link:
  url_context = UrlContext(url, user)
  content = await load_content_from_remote_url(url_context)
  parsed_data = parse_content(url_context, content)
  if model_fields is None:
    model_fields = {}

  return Link(**{**parsed_data, **model_fields})


def parse_url_with_content(url: str,
                           content: str,
                           user,
                           model_fields: Optional[dict] = None) -> Link:
  url_context = UrlContext(url, user)
  parsed_data = parse_content(url_context, content)
  if model_fields is None:
    model_fields = {}
  return Link(**{**parsed_data, **model_fields})
