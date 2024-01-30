from django.db.models.signals import post_save
from django.dispatch import receiver

from lynx.models import FeedItem
from lynx.tasks import add_feed_item_to_library


# When a feed item is created, if the linked Feed has
# auto_add_to_library set to True, then spawn a background task
# to add the feed item to the library.
@receiver(post_save, sender=FeedItem, dispatch_uid='add_feed_item_to_library')
def save_feed_item_to_library(sender, instance: FeedItem, created, **kwargs):
  if not created:
    return
  feed = instance.feed
  if not feed.auto_add_feed_items_to_library:
    return
  add_feed_item_to_library(feed.user.pk, instance.pk)
