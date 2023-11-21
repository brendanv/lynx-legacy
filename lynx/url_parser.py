from datetime import datetime
import json
import trafilatura
from trafilatura.settings import use_config

def parse_url(url):
  # Required to avoid signals not on main thread error
  new_config = use_config()
  new_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
  
  downloaded = trafilatura.fetch_url(url)
  md = trafilatura.extract(downloaded, include_links=True, include_formatting=True, config=new_config)
  json_result = trafilatura.extract(downloaded, include_links=True, include_formatting=True, output_format='json', config=new_config)
  json_obj = json.loads(json_result)

  article_date = datetime.strptime(json_obj['date'], '%Y-%m-%d').date() if 'date' in json_obj and json_obj['date'] else None

  return (ParsedURL()
          .set_url(url)
          .set_formatted_markdown(md)
          .set_raw_text(json_obj['raw_text'])
          .set_json_parse_result(json_result)
          .set_author(json_obj['author'])
          .set_title(json_obj['title'])
          .set_excerpt(json_obj['excerpt'])
          .set_header_image_url(json_obj['image'])
          .set_article_date(article_date)
         )

class ParsedURL:
  def __init__(self):
      self.url = None
      self.title = None
      self.author = None
      self.article_date = None
      self.excerpt = None
      self.header_image_url = None
      self.raw_text = None
      self.formatted_markdown = None
      self.json_parse_result = None

  def set_url(self, url):
      self.url = url
      return self

  def get_url(self):
      return self.url

  def set_title(self, title):
      self.title = title
      return self

  def get_title(self):
      return self.title

  def set_author(self, author):
      self.author = author
      return self

  def get_author(self):
      return self.author

  def set_article_date(self, article_date):
      self.article_date = article_date
      return self

  def get_article_date(self):
      return self.article_date

  def set_excerpt(self, excerpt):
      self.excerpt = excerpt
      return self

  def get_excerpt(self):
      return self.excerpt

  def set_header_image_url(self, header_image_url):
      self.header_image_url = header_image_url
      return self

  def get_header_image_url(self):
      return self.header_image_url

  def set_raw_text(self, raw_text):
      self.raw_text = raw_text
      return self

  def get_raw_text(self):
      return self.raw_text

  def set_formatted_markdown(self, formatted_markdown):
      self.formatted_markdown = formatted_markdown
      return self

  def get_formatted_markdown(self):
      return self.formatted_markdown

  def set_json_parse_result(self, json_parse_result):
      self.json_parse_result = json_parse_result
      return self

  def get_json_parse_result(self):
      return self.json_parse_result