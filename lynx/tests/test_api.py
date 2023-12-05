from django.contrib.auth.models import User
from django.test import TestCase, Client
from unittest.mock import patch
from lynx.models import UserSetting, Link
import json
from django.utils import timezone

add_link_dict = {"url": "https://example.com?1234=5678"}


class CreateLinkEndpointTest(TestCase):

  def setUp(self):
    self.client = Client()
    self.user = User.objects.create_user(username='testuser')
    self.user_setting = UserSetting.objects.create(user_id=self.user.pk,
                                                   lynx_api_key='test_api_key')

  def create_test_link(self, **kwargs) -> Link:
    default_user = self.user
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'creator': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    link.save()
    return link

  @patch('lynx.url_parser.parse_url')
  def test_test_endpoint_with_valid_key_header(self, mock_parse_url):
    link = self.create_test_link(
        original_url=add_link_dict['url'],
        cleaned_url='https://example.com',
        title='Example Title',
        author='Example Author',
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    mock_parse_url.return_value = link
    response = self.client.generic('POST',
                                   '/api/links/add',
                                   json.dumps(add_link_dict),
                                   HTTP_X_API_KEY='test_api_key')
    self.assertEqual(response.status_code, 200)
    mock_parse_url.assert_called_once_with(add_link_dict['url'], self.user)
    response_data = json.loads(response.content.decode())
    self.assertEqual(response_data['original_url'], add_link_dict['url'])
    self.assertEqual(response_data['cleaned_url'], link.cleaned_url)
    self.assertEqual(response_data['title'], link.title)
    self.assertEqual(response_data['author'], link.author)
    self.assertEqual(response_data['read_time_seconds'],
                     link.read_time_seconds)
    self.assertEqual(response_data['read_time_display'],
                     link.read_time_display)
    
  @patch('lynx.url_parser.parse_url')
  def test_test_endpoint_with_valid_key_bearer(self, mock_parse_url):
    link = self.create_test_link(
        original_url=add_link_dict['url'],
        cleaned_url='https://example.com',
        title='Example Title',
        author='Example Author',
        read_time_seconds=12,
        read_time_display='12 seconds',
    )
    mock_parse_url.return_value = link
    response = self.client.generic('POST',
                                   '/api/links/add',
                                   json.dumps(add_link_dict),
                                   HTTP_AUTHORIZATION='Bearer test_api_key')
    self.assertEqual(response.status_code, 200)
    mock_parse_url.assert_called_once_with(add_link_dict['url'], self.user)
    response_data = json.loads(response.content.decode())
    self.assertEqual(response_data['original_url'], add_link_dict['url'])
    self.assertEqual(response_data['cleaned_url'], link.cleaned_url)
    self.assertEqual(response_data['title'], link.title)
    self.assertEqual(response_data['author'], link.author)
    self.assertEqual(response_data['read_time_seconds'],
                     link.read_time_seconds)
    self.assertEqual(response_data['read_time_display'],
                     link.read_time_display)
    
  @patch('lynx.url_parser.parse_url')
  def test_test_endpoint_with_invalid_key_bearer(self, mock_parse_url):
    response = self.client.generic('POST',
                                   '/api/links/add',
                                   json.dumps(add_link_dict),
                                   HTTP_AUTHORIZATION='Bearer invalid_key')
    self.assertNotEqual(response.status_code, 200)
    mock_parse_url.assert_not_called()
    
  @patch('lynx.url_parser.parse_url')
  def test_test_endpoint_with_invalid_key_header(self, mock_parse_url):
    response = self.client.generic('POST',
                                   '/api/links/add',
                                   json.dumps(add_link_dict),
                                   HTTP_X_API_KEY='invalid_key')
    self.assertNotEqual(response.status_code, 200)
    mock_parse_url.assert_not_called()