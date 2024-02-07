from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.utils import timezone
from autoslug import AutoSlugField
import urllib.parse


class Tag(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
  name = models.CharField(max_length=50)
  slug = AutoSlugField(populate_from='name', max_length=50)

  def __str__(self):
    return f'Tag({self.name})'

  class Meta:
    ordering = ['name']


class BulkUpload(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
  tag_slug = models.CharField(max_length=50, blank=True, null=True)


class Link(models.Model):
  # The date this model was created
  created_at = models.DateTimeField(auto_now_add=True)
  # The last time this model was updated
  updated_at = models.DateTimeField(auto_now=True)
  # When this link was added to the library. Note that this may be
  # different from created_at in the case of bulk importing links!
  added_at = models.DateTimeField(default=timezone.now)
  creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
  last_viewed_at = models.DateTimeField(null=True, blank=True)

  original_url = models.URLField(max_length=2000)

  # Extracted metadata
  cleaned_url = models.URLField(max_length=2000)
  hostname = models.CharField(max_length=500, blank=True)
  article_date = models.DateField(blank=True,
                                  null=False)  # Published date of the article
  author = models.CharField(max_length=255, blank=True)
  title = models.CharField(max_length=500, blank=True)
  excerpt = models.TextField(blank=True)
  header_image_url = models.URLField(max_length=2000, blank=True)

  # Variations of the content
  article_html = models.TextField(blank=True)
  raw_text_content = models.TextField(blank=True)
  full_page_html = models.TextField(blank=True)
  content_search = models.GeneratedField(
      db_persist=True,
      expression=SearchVector('title', 'excerpt', weight='A', config='english')
      + SearchVector('raw_text_content', weight='B', config='english'),
      output_field=SearchVectorField(blank=True))

  # Extras
  summary = models.TextField(blank=True)  # AI summary if generated
  read_time_seconds = models.IntegerField(blank=True)
  read_time_display = models.CharField(max_length=100, blank=True)

  # Other metadata
  created_from_feed = models.ForeignKey('Feed',
                                        on_delete=models.SET_NULL,
                                        null=True,
                                        blank=True)
  created_from_bulk_upload = models.ForeignKey('BulkUpload',
                                               on_delete=models.SET_NULL,
                                               null=True,
                                               blank=True)
  tags = models.ManyToManyField(Tag, blank=True)

  def __str__(self):
    return f'Link({self.title})'

  class Meta:
    ordering = ['-added_at']


class UserSetting(models.Model):
  user = models.OneToOneField(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
  openai_api_key = models.CharField(max_length=255, blank=True)

  lynx_api_key = models.CharField(max_length=255, blank=True)

  headers_for_scraping = models.JSONField(default=dict)
  headers_updated_at = models.DateTimeField(null=True,
                                            blank=True,
                                            default=None)

  def __str__(self):
    return f"UserSetting({self.user.username})"


class UserCookie(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  cookie_name = models.CharField(max_length=1000)
  cookie_value = models.CharField(max_length=2000)
  cookie_domain = models.CharField(max_length=1000)

  def __str__(self) -> str:
    return f"UserCookie({self.user.username}, {self.cookie_name})"


class Feed(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  last_fetched_at = models.DateTimeField(null=True, blank=True)

  # Server-side params to prevent re-downloads
  etag = models.CharField(max_length=1000, blank=True)
  modified = models.CharField(max_length=1000, blank=True)

  # Lynx-specific info
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  feed_url = models.URLField(max_length=2000)
  feed_name = models.CharField(max_length=1000)
  feed_description = models.TextField(blank=True)
  feed_image_url = models.URLField(max_length=2000, blank=True)
  is_deleted = models.BooleanField(default=False)
  auto_add_feed_items_to_library = models.BooleanField(default=False)

  def __str__(self):
    return f"Feed({self.feed_name})"


class FeedItem(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  feed = models.ForeignKey(Feed,
                           on_delete=models.CASCADE,
                           related_name="items",
                           related_query_name="item")
  title = models.CharField(max_length=1000)
  pub_date = models.DateTimeField(null=True, blank=True)
  guid = models.CharField(max_length=1000, blank=True)
  description = models.TextField(blank=True)
  url = models.URLField(max_length=2000)

  saved_as_link = models.OneToOneField(
      Link,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="created_from_feed_item",
      related_query_name="created_from_feed_item")

  def __str__(self):
    return f"FeedItem({self.title})"

  class Meta:
    ordering = ['-created_at']
    unique_together = ['feed', 'guid']


class Note(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  saved_at = models.DateTimeField(auto_now_add=True)
  content = models.TextField()
  link = models.ForeignKey('Link',
                           on_delete=models.SET_NULL,
                           null=True,
                           blank=True)
  # Store some fields here in case the link is deleted. This way we can
  # reasonably render the note even if the link no longer exists.
  hostname = models.CharField(max_length=500, blank=True)
  url = models.URLField(max_length=2000, blank=True)
  tags = models.ManyToManyField(Tag, blank=True)
  link_title = models.TextField(blank=True)

  def fragment(self, exclude_directive=False):
    words = self.content.split()
    directive = '' if exclude_directive else '#:~:'
    # This seems to be what Chrome does with it's "Copy link to text"
    # feature, so it's probably good enough...
    if len(words) > 8:
      return f'{directive}text={urllib.parse.quote(" ".join(words[:4]))},{urllib.parse.quote(" ".join(words[-4:]))}'
    else:
      return f'{directive}text={urllib.parse.quote(self.content)}'

  def __str__(self):
    return f"Note({self.user.username}, {self.content[:20]})"

  class Meta:
    ordering = ['-saved_at']
