from unittest.mock import patch
from background_task.tasks import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from lynx.commands import create_archive_for_link, get_or_create_link, get_or_create_link_with_content
from lynx.models import Link, UserCookie


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

  async def test_get_or_create_link_with_content_does_not_create_duplicate(
      self):
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


class TestCreateArchiveForLink(TestCase):

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

  @patch.dict(os.environ, {"SINGLEFILE_URL": ""}, clear=True)
  async def test_create_archive_for_link_returns_none_if_singlefile_disabled(
      self):

    user, _ = await User.objects.aget_or_create(username='user')
    link = await self.create_test_link(user=user)
    archive = await create_archive_for_link(user, link)
    self.assertIsNone(archive, 'Archive should be None if singlefile disabled')

  @patch.dict(os.environ, {"SINGLEFILE_URL": "https://localhost:8000"},
              clear=True)
  @patch('lynx.commands.get_singlefile_content')
  async def test_create_archive_for_link_returns_existing_archive(
      self, mock_get_singlefile_content):
    user, _ = await User.objects.aget_or_create(username='user')
    link = await self.create_test_link(user=user)
    mock_get_singlefile_content.return_value = '<html>Singlefile content</html>'

    archive = await create_archive_for_link(user, link)
    self.assertIsNotNone(archive)
    if archive is None:
      # Shouldn't happen based on the previous check
      return

    self.assertEqual(archive.archive_content,
                     '<html>Singlefile content</html>')
    self.assertEqual(archive.link, link)
    self.assertEqual(archive.user, user)

    # Attempt to create another archive for the same link
    new_archive = await create_archive_for_link(user, link)

    self.assertEqual(archive.pk, new_archive.pk)
    self.assertEqual(archive.archive_content, new_archive.archive_content)

  @patch.dict(os.environ, {"SINGLEFILE_URL": "https://localhost:8000"},
              clear=True)
  @patch('lynx.commands.get_singlefile_content')
  async def test_doesnt_create_archive_if_singlefile_doesnt_work(
      self, mock_get_singlefile_content):
    user, _ = await User.objects.aget_or_create(username='user')
    link = await self.create_test_link(user=user)
    mock_get_singlefile_content.return_value = None

    archive = await create_archive_for_link(user, link)
    self.assertIsNone(archive)

  @patch.dict(os.environ, {"SINGLEFILE_URL": "https://localhost:8000"},
              clear=True)
  @patch('lynx.commands.get_singlefile_content')
  async def test_passes_along_user_cookies(self, mock_get_singlefile_content):
    user, _ = await User.objects.aget_or_create(username='user')
    await UserCookie.objects.acreate(user=user,
                                              cookie_name='my_cookie',
                                              cookie_value='my_value',
                                              cookie_domain='example.com')
    await UserCookie.objects.acreate(user=user,
                                              cookie_name='othercookie',
                                              cookie_value='othervalue',
                                              cookie_domain='example.com')
    # This cookie should be ignored!
    await UserCookie.objects.acreate(user=user,
                                              cookie_name='thirdcookie',
                                              cookie_value='thirdvalue',
                                              cookie_domain='anothersite.com')
    link = await self.create_test_link(user=user,
                                       original_url='https://example.com',
                                       cleaned_url='https://example.com',
                                       hostname='example.com')
    mock_get_singlefile_content.return_value = None

    archive = await create_archive_for_link(user, link)
    self.assertIsNone(archive)
    mock_get_singlefile_content.assert_called_with(
        'https://example.com',
        cookies=[
            'my_cookie,my_value,example.com',
            'othercookie,othervalue,example.com',
        ])
