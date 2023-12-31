from django.contrib import admin

# Register your models here.

from .models import Tag, Link, UserSetting, UserCookie, Feed, FeedItem

admin.site.register(Link)
admin.site.register(UserSetting)
admin.site.register(UserCookie)
admin.site.register(Feed)
admin.site.register(FeedItem)
admin.site.register(Tag)
