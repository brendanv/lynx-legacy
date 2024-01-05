from unittest import TestCase
from lynx.transforms import apply_all_transforms
from bs4 import BeautifulSoup
from typing import Optional


class TestTextTransforms(TestCase):

  def run_and_assert_transforms(self,
                                html_content: str,
                                *,
                                contains: Optional[str] = None,
                                not_contains: Optional[str] = None,
                                equals: Optional[str] = None,
                                fail_msg: Optional[str] = None) -> None:
    soup = apply_all_transforms(html_content)
    if contains:
      self.assertIn(contains, str(soup), fail_msg)

    if not_contains:
      self.assertNotIn(not_contains, str(soup), fail_msg)

    if equals:
      self.assertEqual(equals, str(soup), fail_msg)

  def test_convert_image_links(self):
    self.run_and_assert_transforms(
        '<html><body><p>Check out this <a class="image-link" href="http://example.com/image.jpg">image</a>!</p></body></html>',
        contains='<img src="http://example.com/image.jpg"/>',
        fail_msg='Image link should be converted to an <img> tag',
    )

  def test_convert_image_links_with_multiple_classes(self):
    self.run_and_assert_transforms(
        '<html><body><p>See this <a class="image-link another-class" href="http://example.com/picture.jpg">picture</a>!</p></body></html>',
        contains='<img src="http://example.com/picture.jpg"/>!',
        fail_msg=
        'Image link with multiple classes should be converted to an <img> tag',
    )

  def test_extraneous_fonts_removed(self):
    self.run_and_assert_transforms(
        '<html><body><p>Check out this <font color="blue">blue</font> text!</p></body></html>',
        contains='<p>Check out this blue text!</p>',
        not_contains='font',
        fail_msg='Extraneous <font> tags should be removed',
    )

  def test_nested_images_within_fonts_kept(self):
    self.run_and_assert_transforms(
        '<html><body><p>Check out this <font color="blue"><a class="image-link" href="http://example.com" target="_blank">image</a></font>!</p></body></html>',
        contains='<p>Check out this <img src="http://example.com"/>!</p>',
        fail_msg='Content of <font> tags should be kept',
    )

  def test_unused_tags_removed(self):
    self.run_and_assert_transforms(
        '<html><body><p>Check out this and this<map><area href="hello world">hello world</map>!</p></body></html>',
        not_contains='area',
        contains='Check out this and this!',
        fail_msg='Unused tags should be removed',
    )
