from django.db import migrations
from django.conf import settings


def create_usersettings(apps, schema_editor):
  User = apps.get_model(settings.AUTH_USER_MODEL)
  UserSetting = apps.get_model("lynx", "UserSetting")
  for current_user in User.objects.all():
    UserSetting.objects.get_or_create(user=current_user)

class Migration(migrations.Migration):

    dependencies = [
        ('lynx', '0002_usersetting'),
    ]

    operations = [
      migrations.RunPython(create_usersettings),
    ]
