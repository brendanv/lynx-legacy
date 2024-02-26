from django.db.models.signals import post_save
from django.dispatch import receiver

from lynx.models import FeedItem, Link, UserSetting
from lynx.tasks import add_feed_item_to_library, summarize_link_in_background


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

# When a Link is saved, if the user's settings indicate 
# that the Link should automatically be summarized, 
# then spawn a background task to summarize the Link.
@receiver(post_save, sender=Link, dispatch_uid='summarize_link')
def summarize_link(sender, instance: Link, created, **kwargs):
  if not created:
    return
  setting, _ = UserSetting.objects.get_or_create(user=instance.user)
  if not setting.automatically_summarize_new_links:
    return
  summarize_link_in_background(instance.user.pk, instance.pk)