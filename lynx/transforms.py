from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse

from lynx.errors import UrlParseError
from .url_context import UrlContext


def apply_all_transforms(html_content: str,
                         url_context: UrlContext) -> BeautifulSoup:
  soup = BeautifulSoup(html_content, features="lxml")
  transforms = [
      convert_image_links, readability_summarize, remove_styling,
      relative_to_absolute_links
  ]
  for transform in transforms:
    soup = transform(soup, url_context)
  return soup


def convert_image_links(soup: BeautifulSoup,
                        url_context: UrlContext) -> BeautifulSoup:
  """
  Substack often uses <a class="image-link"> tags to link to images.
  This function replaces those links with <img> tags.
  """
  for image_container in soup.find_all(class_="captioned-image-container"):
    image_container.unwrap()
  for image_container in soup.find_all(class_="image-link-expand"):
    image_container.decompose()

  for link in soup.find_all('a', class_='image-link'):
    link.replace_with(soup.new_tag('img', src=link['href']))

  return soup


def readability_summarize(soup: BeautifulSoup,
                          url_context: UrlContext) -> BeautifulSoup:
  """
  Strip out non-article content using Readability.
  """
  readable_doc = Document(str(soup))
  new_soup = BeautifulSoup(readable_doc.summary(), features="lxml")
  return new_soup


def remove_styling(soup: BeautifulSoup,
                   url_context: UrlContext) -> BeautifulSoup:
  """
  Remove other irrelevant styling from the HTML that may have slipped 
  through Readability.
  """
  for tag in soup.find_all('font'):
    tag.unwrap()
  for tag in soup.find_all(['area', 'map']):
    tag.decompose()

  return soup


def relative_to_absolute_links(soup: BeautifulSoup,
                               url_context: UrlContext) -> BeautifulSoup:
  for tag in soup.find_all('a'):
    # netloc is not set if it's a relative link
    if tag.has_attr('href') and urlparse(tag['href']).netloc == '':
      tag['href'] = urljoin(url_context.url, tag['href'])
  for tag in soup.find_all('img'):
    # netloc is not set if it's a relative link
    if tag.has_attr('src') and urlparse(tag['src']).netloc == '':
      tag['src'] = urljoin(url_context.url, tag['src'])

  # srcset is a list of urls with optional size descriptions, 
  # so we need to handle all of them
  for tag in soup.find_all('img'):
    if tag.has_attr('srcset'):
      output = []
      for srcset_item in tag['srcset'].split(','):
        split_item = srcset_item.strip().split()
        if urlparse(split_item[0]).netloc == '':
          split_item[0] = urljoin(url_context.url, split_item[0])
        output.append(' '.join(split_item))
      tag['srcset'] = ','.join(output)
  return soup
