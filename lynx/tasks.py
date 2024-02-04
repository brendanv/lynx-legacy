from asgiref.sync import async_to_sync
from background_task import background
from django.contrib.auth import get_user_model
from lynx.models import FeedItem
from lynx import commands

@background
def add_feed_item_to_library(user_pk: int, feed_item_pk: int):
  User = get_user_model()
  user = User.objects.get(pk=user_pk)
  feed_item = FeedItem.objects.get(pk=feed_item_pk, feed__user=user)
  url = feed_item.saved_as_link
  if url is not None:
    return

  link, is_new = async_to_sync(commands.get_or_create_link)(feed_item.url, user)
  if is_new:
    link.created_from_feed = feed_item.feed
  link.save()
  if is_new:
    feed_item.saved_as_link = link
    feed_item.save()