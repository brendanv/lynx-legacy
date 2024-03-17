from typing import Any, OrderedDict
from django.contrib import admin, messages
from django.http.request import HttpRequest

from lynx.tasks import create_archive_for_link_in_background
from lynx.utils.singlefile import is_singlefile_enabled

# Register your models here.

from .models import Note, Tag, Link, UserSetting, UserCookie, Feed, FeedItem, LinkArchive

class LinkAdmin(admin.ModelAdmin):
  actions = ['create_archive']
  
  @admin.action(description="Create archives in background")
  def create_archive(self, request, queryset):
    if not is_singlefile_enabled():
      self.message_user(
          request,
          'Unable to create archives because Singlefile is not enabled.',
          messages.ERROR,
      )
      return
  
    for link in queryset.filter(linkarchive__isnull=True):
      create_archive_for_link_in_background(link.user.pk, link.pk)

  def get_actions(self, request: HttpRequest) -> OrderedDict[Any, Any]:
    actions = super().get_actions(request)
    if not is_singlefile_enabled():
      del actions['create_archive']
    return actions

admin.site.register(Link, LinkAdmin)
admin.site.register(UserSetting)
admin.site.register(UserCookie)
admin.site.register(Feed)
admin.site.register(FeedItem)
admin.site.register(Tag)
admin.site.register(Note)
admin.site.register(LinkArchive)

