from django.core.management.base import BaseCommand
from lynx.models import Feed
from django.contrib.auth import get_user_model
from lynx import feed_utils


class Command(BaseCommand):
  help = 'Refresh all feed objects for a user.'

  def add_arguments(self, parser):
    parser.add_argument('username', type=str, help='The username of the user')

  def handle(self, *args, **options):
    username = options['username']
    User = get_user_model()
    try:
      user = User.objects.get(username=username)
    except User.DoesNotExist:
      self.stderr.write(self.style.ERROR(f'User "{username}" does not exist.'))
      return

    feeds = Feed.objects.filter(user=user, is_deleted=False)
    self.stdout.write(f'Refreshing {len(feeds)} feeds for user "{username}"')
    for feed in feeds:
      try:
        loader = feed_utils.RemoteFeedLoader(
            user, None, feed=feed).load_remote_feed().persist_new_feed_items(
            ).persist_feed()
        if len(loader.get_new_entries()) > 0:
          self.stdout.write(
              self.style.SUCCESS(
                  f'Successfully refreshed feed: {feed.feed_name}'))
        else:
          self.stdout.write(f'No new entries found for feed: {feed.feed_name}')
      except Exception as e:
        self.stderr.write(
            self.style.ERROR(
                f'Failed to refresh feed: {feed.feed_name} - {str(e)}'))
