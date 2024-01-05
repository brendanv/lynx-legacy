from bs4 import BeautifulSoup
from readability import Document


def apply_all_transforms(html_content: str,
                         one_line_return: bool = True) -> BeautifulSoup:
  soup = BeautifulSoup(html_content, features="lxml")
  transforms = [convert_image_links, readability_summarize, remove_styling]
  for transform in transforms:
    soup = transform(soup)
  return soup


def convert_image_links(soup: BeautifulSoup) -> BeautifulSoup:
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


def readability_summarize(soup: BeautifulSoup) -> BeautifulSoup:
  """
  Strip out non-article content using Readability.
  """
  readable_doc = Document(str(soup))
  new_soup = BeautifulSoup(readable_doc.summary(), features="lxml")
  return new_soup


def remove_styling(soup: BeautifulSoup) -> BeautifulSoup:
  """
  Remove other irrelevant styling from the HTML that may have slipped 
  through Readability.
  """
  for tag in soup.find_all('font'):
    tag.unwrap()
  for tag in soup.find_all(['area', 'map']):
    tag.decompose()

  return soup
