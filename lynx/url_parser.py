import json
from datetime import datetime

import readtime
from django.utils import timezone
import trafilatura
from trafilatura.settings import use_config

from .models import Link


def parse_url(url):
  # Required to avoid signals not on main thread error
  new_config = use_config()
  new_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

  downloaded = trafilatura.fetch_url(url)
  md = trafilatura.extract(downloaded,
                           include_links=True,
                           include_formatting=True,
                           include_images=True,
                           config=new_config)
  json_result = trafilatura.extract(downloaded,
                                    include_links=True,
                                    include_formatting=True,
                                    include_images=True,
                                    output_format='json',
                                    config=new_config)
  json_obj = json.loads(json_result)

  article_date = datetime.strptime(json_obj['date'], '%Y-%m-%d').date(
  ) if 'date' in json_obj and json_obj['date'] else timezone.now()

  read_time = readtime.of_markdown(md)

  return Link(url=json_obj['source'],
              hostname=json_obj['hostname'],
              article_date=article_date,
              author=json_obj['author'],
              title=json_obj['title'],
              excerpt=json_obj['excerpt'],
              markdown_content=md,
              raw_text_content=json_obj['raw_text'],
              header_image_url=json_obj['image'],
              read_time_seconds=read_time.seconds,
              read_time_display=read_time.text)
