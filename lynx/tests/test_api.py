from django.contrib.auth.models import User
from django.test import TestCase, Client
from lynx.models import UserSetting


class ApiEndpointTests(TestCase):

  def setUp(self):
    self.client = Client()
    self.user = User.objects.create_user(username='testuser')
    self.user_setting = UserSetting.objects.create(
        user_id=self.user.pk,
        lynx_api_key='test_api_key')

  def test_test_endpoint_with_valid_key_header(self):
    response = self.client.post('/api/test', HTTP_X_API_KEY='test_api_key')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content.decode(), '"Success"')

  def test_test_endpoint_with_invalid_key_header(self):
    response = self.client.post('/api/test', HTTP_X_API_KEY='invalid_key')
    self.assertNotEqual(response.status_code, 200)

  def test_test_endpoint_with_no_key_header(self):
    response = self.client.post('/api/test')
    self.assertNotEqual(response.status_code, 200)

  def test_test_endpoint_with_valid_key_bearer(self):
    response = self.client.post('/api/test',
                                HTTP_AUTHORIZATION='Bearer test_api_key')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content.decode(), '"Success"')

  def test_test_endpoint_with_invalid_key_bearer(self):
    response = self.client.post('/api/test',
                                HTTP_AUTHORIZATION='Bearer invalid_key')
    self.assertNotEqual(response.status_code, 200)

  def test_test_endpoint_with_no_key_bearer(self):
    response = self.client.post('/api/test')
    self.assertNotEqual(response.status_code, 200)
