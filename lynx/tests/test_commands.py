from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from lynx.commands import get_or_create_link, get_or_create_link_with_content
from lynx.models import Link


class TestGetOrCreateLink(TestCase):

  async def create_test_link(self, **kwargs) -> Link:
    default_user, _ = await User.objects.aget_or_create(username='default_user'
                                                        )
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'user': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    await link.asave()
    return link

  @patch('lynx.url_parser.parse_url')
  async def test_get_or_create_link_does_not_create_duplicate(
      self, mock_parse_url):
    user, _ = await User.objects.aget_or_create(username='user')
    url = 'http://example.com'

    mock_parse_url.return_value = Link(user=user,
                                       original_url=url,
                                       cleaned_url=url,
                                       article_date=timezone.now(),
                                       read_time_seconds=12)

    link, created = await get_or_create_link(url, user)
    self.assertTrue(created, 'Link should be created on first call')

    # Call get_or_create_link again with the same URL and user
    link_again, created_again = await get_or_create_link(url, user)
    self.assertFalse(
        created_again,
        'Link should not be created again for the same URL and user')
    self.assertEqual(link.pk, link_again.pk,
                     'The returned link should have the same primary key')


class TestGetOrCreateLinkWithContent(TestCase):

  async def create_test_link(self, **kwargs) -> Link:
    default_user, _ = await User.objects.aget_or_create(username='default_user'
                                                        )
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'user': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    await link.asave()
    return link

  async def test_get_or_create_link_with_content_does_not_create_duplicate(self):
    user, _ = await User.objects.aget_or_create(username='user')
    url = 'http://example.com'

    link, created = await get_or_create_link_with_content(
        url, '<html><body>hello</body></html>', user)
    self.assertTrue(created, 'Link should be created on first call')

    # Call get_or_create_link again with the same URL and user
    link_again, created_again = await get_or_create_link_with_content(
        url, '<html><body>hello again</body></html>', user)
    self.assertFalse(
        created_again,
        'Link should not be created again for the same URL and user')
    self.assertEqual(link.pk, link_again.pk,
                     'The returned link should have the same primary key')
