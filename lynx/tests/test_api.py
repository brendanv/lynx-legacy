from django.contrib.auth.models import User
from django.test import TestCase, AsyncClient
from unittest.mock import patch
from lynx.models import UserSetting, Link
import json
from django.utils import timezone

add_link_dict = {
    "url": "https://example.com?1234=5678",
    "cleaned_url": "https://example.com",
    "title": "Example",
    "summary": "A summary",
    "raw_text_content": "Some content",
    "author": "John Doe",
}


class CreateLinkEndpointTest(TestCase):

  def setUp(self):
    self.client = AsyncClient()
    self.user = User.objects.create_user(username='testuser')
    self.user_setting = UserSetting.objects.create(user_id=self.user.pk,
                                                   lynx_api_key='test_api_key')

  @patch('lynx.url_parser.parse_url')
  async def test_test_endpoint_with_valid_key_header(self, mock_parse_url):
    mock_parse_url.return_value = Link(
        user=self.user,
        original_url=add_link_dict['url'],
        cleaned_url=add_link_dict['cleaned_url'],
        title=add_link_dict['title'],
        author=add_link_dict['author'],
        article_date=timezone.now(),
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    response = await self.client.generic('POST',
                                         '/api/links/add',
                                         json.dumps(
                                             {'url': add_link_dict['url']}),
                                         X_API_KEY='test_api_key')
    self.assertEqual(response.status_code, 200)
    mock_parse_url.assert_called_once_with(add_link_dict['url'], self.user,
                                           None)
    response_data = json.loads(response.content.decode())
    self.assertEqual(response_data['original_url'], add_link_dict['url'])
    self.assertEqual(response_data['cleaned_url'],
                     add_link_dict['cleaned_url'])
    self.assertEqual(response_data['title'], add_link_dict['title'])
    self.assertEqual(response_data['author'], add_link_dict['author'])
    self.assertEqual(response_data['read_time_seconds'], 12)
    self.assertEqual(response_data['read_time_display'], '12 seconds')

  @patch('lynx.url_parser.parse_url')
  async def test_test_endpoint_with_valid_key_bearer(self, mock_parse_url):
    mock_parse_url.return_value = Link(
        user=self.user,
        original_url=add_link_dict['url'],
        cleaned_url=add_link_dict['cleaned_url'],
        title=add_link_dict['title'],
        author=add_link_dict['author'],
        article_date=timezone.now(),
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    response = await self.client.generic('POST',
                                         '/api/links/add',
                                         json.dumps(
                                             {'url': add_link_dict['url']}),
                                         AUTHORIZATION='Bearer test_api_key')
    self.assertEqual(response.status_code, 200)
    mock_parse_url.assert_called_once_with(add_link_dict['url'], self.user,
                                           None)
    response_data = json.loads(response.content.decode())
    self.assertEqual(response_data['original_url'], add_link_dict['url'])
    self.assertEqual(response_data['cleaned_url'],
                     add_link_dict['cleaned_url'])
    self.assertEqual(response_data['title'], add_link_dict['title'])
    self.assertEqual(response_data['author'], add_link_dict['author'])
    self.assertEqual(response_data['read_time_seconds'], 12)
    self.assertEqual(response_data['read_time_display'], '12 seconds')

  @patch('lynx.url_parser.parse_url')
  async def test_test_endpoint_with_invalid_key_bearer(self, mock_parse_url):
    response = await self.client.generic(
        'POST',
        '/api/links/add',
        json.dumps(add_link_dict),
        HTTP_AUTHORIZATION='Bearer invalid_key')
    self.assertNotEqual(response.status_code, 200)
    mock_parse_url.assert_not_called()

  @patch('lynx.url_parser.parse_url')
  async def test_test_endpoint_with_invalid_key_header(self, mock_parse_url):
    response = await self.client.generic('POST',
                                         '/api/links/add',
                                         json.dumps(add_link_dict),
                                         HTTP_X_API_KEY='invalid_key')
    self.assertNotEqual(response.status_code, 200)
    mock_parse_url.assert_not_called()


class CreateNoteEndpointTest(TestCase):

  def setUp(self):
    self.client = AsyncClient()
    self.user = User.objects.create_user(username='testuser')
    self.user_setting = UserSetting.objects.create(user_id=self.user.pk,
                                                   lynx_api_key='test_api_key')

  @patch('lynx.url_parser.parse_url')
  async def test_create_note_for_unsaved_link(self, mock_parse_url):
    mock_parse_url.return_value = Link(
        user=self.user,
        original_url=add_link_dict['url'],
        cleaned_url=add_link_dict['cleaned_url'],
        title=add_link_dict['title'],
        author=add_link_dict['author'],
        article_date=timezone.now(),
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    response = await self.client.generic('POST',
                                         '/api/notes/add',
                                         json.dumps({
                                             'url': add_link_dict['url'],
                                             'content': 'hello world'
                                         }),
                                         X_API_KEY='test_api_key')
    self.assertEqual(response.status_code, 200)
    mock_parse_url.assert_called_once_with(add_link_dict['url'], self.user,
                                           None)
    response_data = json.loads(response.content.decode())
    self.assertEqual(response_data['content'], 'hello world')
    self.assertEqual(response_data['url'], add_link_dict['cleaned_url'])
    self.assertEqual(response_data['link']['original_url'], add_link_dict['url'])
    self.assertEqual(response_data['link']['cleaned_url'],
                     add_link_dict['cleaned_url'])
    self.assertEqual(response_data['link']['title'], add_link_dict['title'])
    self.assertEqual(response_data['link']['author'], add_link_dict['author'])
    self.assertEqual(response_data['link']['read_time_seconds'], 12)
    self.assertEqual(response_data['link']['read_time_display'], '12 seconds')
    
  async def test_create_note_for_previously_saved_link(self):
    existing_link = await Link.objects.acreate(
        user=self.user,
        original_url=add_link_dict['url'],
        cleaned_url=add_link_dict['cleaned_url'],
        title=add_link_dict['title'],
        author=add_link_dict['author'],
        article_date=timezone.now(),
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    with patch('lynx.commands.get_or_create_link') as mock_get_or_create_link:
      mock_get_or_create_link.return_value = (existing_link, False)
      response = await self.client.generic('POST',
                                         '/api/notes/add',
                                         json.dumps({
                                             'url': add_link_dict['url'],
                                             'content': 'hello world'
                                         }),
                                         X_API_KEY='test_api_key')
      self.assertEqual(response.status_code, 200)
      
      response_data = json.loads(response.content.decode())
      self.assertEqual(response_data['content'], 'hello world')
      self.assertEqual(response_data['link']['id'], existing_link.pk)
