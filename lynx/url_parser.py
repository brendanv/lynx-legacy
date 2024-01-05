import json
from datetime import datetime
from django.http.request import HttpRequest

import requests
import readtime
from django.utils import timezone
from readability import Document
import trafilatura
from trafilatura.settings import use_config
from urllib.parse import urlparse
from lynx.errors import UrlParseError
from lynx.transforms import apply_all_transforms

from .models import Link, UserCookie


def extract_headers_to_pass_for_parse(request: HttpRequest) -> dict[str, str]:
  # Headers to make the request look less like scraping but while also
  # not really changing the behavior at all.
  supported_headers = [
      'accept', 'accept-language', 'user-agent', 'dnt',
      'sec-fetch-dest', 'sec-fetch-mode'
  ]
  return {
      k.lower(): v
      for k, v in request.headers.items() if k.lower() in supported_headers
  }


def parse_url(url: str, user, headers: dict[str, str] = {}, model_fields={}) -> Link:
  domain = urlparse(url).netloc
  cookies = UserCookie.objects.filter(user=user, cookie_domain=domain)
  cookie_data = {cookie.cookie_name: cookie.cookie_value for cookie in cookies}
  response = requests.get(url, cookies=cookie_data, headers=headers)

  try:
    response.raise_for_status()
  except requests.exceptions.HTTPError as e:
    raise UrlParseError(str(e))

  # Required to avoid signals not on main thread error
  new_config = use_config()
  new_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
  extracted_json_str = trafilatura.extract(response.content,
                                           include_links=True,
                                           include_formatting=True,
                                           include_images=True,
                                           output_format='json',
                                           config=new_config)
  json_meta = json.loads(str(extracted_json_str))

  article_date = datetime.strptime(json_meta['date'], '%Y-%m-%d').date(
  ) if 'date' in json_meta and json_meta['date'] else timezone.now()

  summary_html = apply_all_transforms(response.text).prettify(formatter='html')
  read_time = readtime.of_html(summary_html)

  model_args = {
    'original_url':url,
    'creator':user,
    'cleaned_url':json_meta.get('source') or url,
    'hostname':json_meta.get('hostname') or domain,
    'article_date':article_date,
    'author':json_meta.get('author') or 'Unknown Author',
    'title':json_meta['title'] or Document(response.content).title(),
    'excerpt':json_meta.get('excerpt') or '',
    'article_html':summary_html,
    'raw_text_content':json_meta['raw_text'],
    'full_page_html':response.text,
    'header_image_url':json_meta.get('image') or '',
    'read_time_seconds':read_time.seconds,
    'read_time_display':read_time.text
  }
  
  return Link(**{**model_args, **model_fields})
