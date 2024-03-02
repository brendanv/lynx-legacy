from django.contrib import admin

# Register your models here.

from .models import Note, Tag, Link, UserSetting, UserCookie, Feed, FeedItem, LinkArchive

admin.site.register(Link)
admin.site.register(UserSetting)
admin.site.register(UserCookie)
admin.site.register(Feed)
admin.site.register(FeedItem)
admin.site.register(Tag)
admin.site.register(Note)
admin.site.register(LinkArchive)
