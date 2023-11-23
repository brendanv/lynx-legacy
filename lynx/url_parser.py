import json
from datetime import datetime

import requests
import readtime
from django.utils import timezone
from readability import Document
import trafilatura
from trafilatura.settings import use_config

from .models import Link


def parse_url(url, user):
  response = requests.get(url)

  readable_doc = Document(response.content)
  summary_html = readable_doc.summary()

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

  read_time = readtime.of_html(summary_html)

  return Link(original_url=url,
              creator=user,
              cleaned_url=json_meta['source'],
              hostname=json_meta['hostname'],
              article_date=article_date,
              author=json_meta['author'],
              title=json_meta['title'],
              excerpt=json_meta['excerpt'],
              article_html=summary_html,
              raw_text_content=json_meta['raw_text'],
              full_page_html=readable_doc.content(),
              header_image_url=json_meta['image'],
              read_time_seconds=read_time.seconds,
              read_time_display=read_time.text)
