from django.contrib import admin

# Register your models here.

from .models import Link, UserSetting

admin.site.register(Link)
admin.site.register(UserSetting)