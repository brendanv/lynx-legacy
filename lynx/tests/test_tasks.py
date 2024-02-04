from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from lynx.tasks import add_feed_item_to_library
from lynx.models import FeedItem, Feed, Link
from django.contrib.auth.models import User


class TestTasks(TestCase):

  # kwargs are used as values in link model
  def create_test_link(self, **kwargs) -> Link:
    default_user, _= User.objects.get_or_create(username='default_user')
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'creator': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    link.save()
    return link

  def test_add_feed_item_to_library_creates_link_only_if_not_added(self):
    user = User.objects.create(username='testuser')
    feed = Feed.objects.create(user=user, feed_name='Test Feed')
    link = self.create_test_link(creator=user)
    feed_item = FeedItem.objects.create(feed=feed,
                                        title='Test Feed Item',
                                        url='http://example.com')

    with patch('lynx.url_parser.parse_url') as mock_parse_url:
      mock_parse_url.return_value = link
      add_feed_item_to_library.now(user.pk, feed_item.pk)
      mock_parse_url.assert_called_once_with(feed_item.url, user, None)
      feed_item.refresh_from_db()
      self.assertEqual(feed_item.saved_as_link, link)
      link.refresh_from_db()
      self.assertEqual(link.created_from_feed, feed)
      
    with patch('lynx.url_parser.parse_url') as mock_parse_url:
      add_feed_item_to_library.now(user.pk, feed_item.pk)
      mock_parse_url.assert_not_called()

  def test_add_feed_item_to_library_fails_for_wrong_user(self):
    correct_user = User.objects.create(username='correct_user')
    wrong_user = User.objects.create(username='wrong_user')
    feed = Feed.objects.create(user=correct_user, feed_name='Correct User Feed')
    feed_item = FeedItem.objects.create(feed=feed,
                                        title='Feed Item for Correct User',
                                        url='http://example.com')

    with self.assertRaises(FeedItem.DoesNotExist):
      add_feed_item_to_library.now(wrong_user.pk, feed_item.pk)

    feed_item.refresh_from_db()
    self.assertIsNone(feed_item.saved_as_link)
