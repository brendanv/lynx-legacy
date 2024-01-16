from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import patch
from io import StringIO


class CreateLynxAdminCommandTest(TestCase):

  def test_create_lynx_admin_without_env_variables(self):
    User = get_user_model()
    out = StringIO()
    User.objects.all().delete()
    
    call_command('createlynxadmin', stdout=out)
    self.assertIn('Successfully created superuser: lynx', out.getvalue())
    self.assertTrue(User.objects.filter(username='lynx').exists())
    self.assertTrue(User.objects.get(username='lynx').check_password('lynx'))

  def test_idempotent_create_lynx_admin(self):
    User = get_user_model()
    out = StringIO()
    
    User.objects.create_superuser('lynx', '', 'lynx')
    call_command('createlynxadmin', stdout=out)
    self.assertIn('Superuser creation skipped', out.getvalue())

  @patch('os.environ.get')
  def test_create_lynx_admin_with_env_variables(self, mock_env_get):
    User = get_user_model()
    out = StringIO()
    mock_env_get.side_effect = lambda k, default=None: {
        'LYNX_ADMIN_USERNAME': 'env_lynx',
        'LYNX_ADMIN_PASSWORD': 'env_lynx_pass'
    }.get(k, default)

    call_command('createlynxadmin', stdout=out)

    self.assertIn('Successfully created superuser: env_lynx', out.getvalue())
    self.assertTrue(User.objects.filter(username='env_lynx').exists())
    self.assertEqual(
        User.objects.get(username='env_lynx').check_password('env_lynx_pass'),
        True)

  @patch('os.environ.get')
  def test_create_lynx_admin_with_username_only(self, mock_env_get):
    User = get_user_model()
    stdout = StringIO()
    stderr = StringIO()
    mock_env_get.side_effect = lambda k, default=None: {
        'LYNX_ADMIN_USERNAME': 'only_username'
    }.get(k, default)

    call_command('createlynxadmin', stdout=stdout, stderr=stderr)

    self.assertIn(
        'LYNX_ADMIN_PASSWORD must be set if LYNX_ADMIN_USERNAME is set.',
        stderr.getvalue())
    self.assertFalse(User.objects.filter(username='only_username').exists())

  @patch('os.environ.get')
  def test_create_lynx_admin_with_env_variables_after_default(
      self, mock_env_get):
    User = get_user_model()
    out = StringIO()

    User.objects.create_superuser('lynx', '', 'lynx')
    self.assertTrue(User.objects.filter(username='lynx').exists())

    mock_env_get.side_effect = lambda k, default=None: {
        'LYNX_ADMIN_USERNAME': 'new_env_lynx',
        'LYNX_ADMIN_PASSWORD': 'new_env_lynx_pass'
    }.get(k, default)
    out = StringIO()
    call_command('createlynxadmin', stdout=out)

    self.assertIn('Successfully created superuser: new_env_lynx',
                  out.getvalue())
    self.assertTrue(User.objects.filter(username='new_env_lynx').exists())
    self.assertEqual(
        User.objects.get(
            username='new_env_lynx').check_password('new_env_lynx_pass'), True)

  

  @patch('os.environ.get')
  def test_idempotent_create_lynx_admin_with_env_variables(self, mock_env_get):
    User = get_user_model()
    out = StringIO()
    mock_env_get.side_effect = lambda k, default=None: {
        'LYNX_ADMIN_USERNAME': 'env_lynx',
        'LYNX_ADMIN_PASSWORD': 'env_lynx_pass'
    }.get(k, default)

    User.objects.create_superuser('env_lynx', '', 'env_lynx_pass')
    call_command('createlynxadmin', stdout=out)
    self.assertIn('Superuser creation skipped', out.getvalue())
    self.assertTrue(User.objects.filter(username='env_lynx').exists())

  def test_no_create_default_superuser_if_users_exist(self):
    User = get_user_model()
    out = StringIO()

    User.objects.create_user('existing_user', '', 'password')
    call_command('createlynxadmin', stdout=out)

    self.assertIn(
        'Default Superuser creation skipped because other users exist',
        out.getvalue())
    self.assertFalse(User.objects.filter(username='lynx').exists())
