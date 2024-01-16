from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
import os


class Command(BaseCommand):
  help = 'Create a default superuser "lynx" if no users exist.'

  def handle(self, *args, **options):
    User = get_user_model()

    env_username = os.environ.get('LYNX_ADMIN_USERNAME', None)
    env_password = os.environ.get('LYNX_ADMIN_PASSWORD', None)
    if env_username and not env_password:
      self.stderr.write(
          self.style.ERROR(
              'LYNX_ADMIN_PASSWORD must be set if LYNX_ADMIN_USERNAME is set.')
      )
      return

    try:
      if env_username and env_password:
        if not User.objects.filter(username=env_username).exists():
          User.objects.create_superuser(env_username, '', env_password)
          self.stdout.write(
              self.style.SUCCESS(
                  f'Successfully created superuser: {env_username}'))
        else:
          self.stdout.write(
              f'Superuser creation skipped, a user "{env_username}" already exists.'
          )

      else: # No env_username or env_password
        if not User.objects.exists():
          User.objects.create_superuser('lynx', '', 'lynx')
          self.stdout.write(
              self.style.SUCCESS('Successfully created superuser: lynx'))
        else: 
          self.stdout.write(
              'Default Superuser creation skipped because other users exist')
          
    except IntegrityError:
      self.stdout.write(
          self.style.ERROR(
              'Error creating superuser. A user may already exist with that username.'
          ))
