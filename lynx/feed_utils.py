from datetime import datetime, timedelta
from typing import List, Optional
from django.contrib.auth.models import User
import feedparser
from .models import FeedItem, Feed
from django.db import IntegrityError
from django.contrib import messages
from bs4 import BeautifulSoup


class RemoteFeedLoader:

  def __init__(self,
               user: User,
               request,
               feed: Optional[Feed] = None,
               feed_url: Optional[str] = None) -> None:
    if feed is None and feed_url is None:
      raise ValueError("Either feed or feed_url must be provided")
    if feed is not None and feed_url is not None:
      raise ValueError("Only one of feed or feed_url should be provided")

    self.user = user
    self.feed = feed
    self.feed_url = feed_url
    self.remote = None
    self.created_feed_items = []
    self.skipped_count = 0
    self.request = request

  def load_remote_feed(self):
    if self.feed:
      self.remote = feedparser.parse(self.feed.feed_url,
                                     etag=self.feed.etag,
                                     modified=self.feed.modified)

    if self.feed_url:
      self.remote = feedparser.parse(self.feed_url)
      feed_details = self.remote.get('feed', {})
      feed_title = feed_details.get('title', 'Unknown Feed')
      feed_description = BeautifulSoup(feed_details.get('description',
                                                        '')).get_text()
      feed_image = feed_details.get('image', {})
      feed_image_url = feed_image.get('href', '')
      self.feed = Feed.objects.create(user=self.user,
                                      feed_url=self.feed_url,
                                      feed_name=feed_title,
                                      feed_image_url=feed_image_url,
                                      feed_description=feed_description)
    return self

  def persist_new_feed_items(self):
    if self.feed is None or self.remote is None:
      raise ValueError("Call load_remote_feed before persist_new_feed_items!")

    if self.feed.last_fetched_at:
      last_fetched_timestamp = self.feed.last_fetched_at.timestamp(
      ) if self.feed.last_fetched_at else (datetime.now() -
                                           timedelta(days=2)).timestamp()
      latest_entries = [
          entry for entry in self.remote.entries if datetime(
              *entry.published_parsed[:6]).timestamp() > last_fetched_timestamp
      ]
    else:
      sorted_entries = sorted(
          self.remote.entries,
          key=lambda entry: datetime(*entry.published_parsed[:6]))
      latest_entries = sorted_entries[-3:]

    for entry in latest_entries:
      try:
        feed_item = FeedItem.objects.create(
            feed=self.feed,
            title=entry.title,
            url=entry.link,
            description=BeautifulSoup(entry.summary).get_text(),
            pub_date=datetime(*entry.published_parsed[:6]),
            guid=entry.id)
        self.created_feed_items.append(feed_item)
      except IntegrityError:
        self.skipped_count += 1

    return self

  def persist_feed(self):
    if self.feed is None or self.remote is None:
      raise ValueError("Call load_remote_feed before persist_feed!")

    self.feed.last_fetched_at = datetime.now()
    if 'modified' in self.remote:
      self.feed.modified = self.remote['modified']
    if 'etag' in self.remote:
      self.feed.etag = self.remote['etag']

    if self.remote.status == 301:
      self.feed.feed_url = self.remote.href
      messages.warning(
          self.request,
          f"Feed '{self.feed.feed_name}' has been permanently relocated, updated URL to '{self.remote.href}'"
      )
    if self.remote.status == 410:
      self.feed.is_deleted = True
      messages.error(
          self.request,
          f"Feed '{self.feed.feed_name}' has been permanently deleted, please add a new feed."
      )

    self.feed.save()
    return self

  def get_feed(self) -> Feed:
    if self.feed is None:
      raise ValueError("Call load_remote_feed before get_feed!")
    return self.feed

  def get_new_entries(self) -> List[FeedItem]:
    return self.created_feed_items

  def get_skipped_count(self) -> int:
    return self.skipped_count
