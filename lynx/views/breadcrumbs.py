from typing import Optional
from django.urls import NoReverseMatch, reverse

from lynx.models import Feed, Link

# The first element is the name of the page.
# The second element is the URL name of the page.
# The third element is an array of args to pass to reverse.
Breadcrumb = tuple[str, str, list]

# Convenience consts for consistency
HOME: Breadcrumb = ('lynx:links_feed', 'Home', [])
ADD_LINK: Breadcrumb = ('lynx:add_link', 'Add Link', [])
FEEDS: Breadcrumb = ('lynx:feeds', 'Feeds', [])
ADD_FEED: Breadcrumb = ('lynx:add_feed', 'Add Feed', [])
SETTINGS: Breadcrumb = ('lynx:user_settings', 'Settings', [])
COOKIES: Breadcrumb = ('lynx:user_cookies', 'Cookies', [])
BULK_UPLOAD: Breadcrumb = ('lynx:bulk_upload', 'Bulk Upload', [])
MANAGE_TAGS: Breadcrumb = ('lynx:manage_tags', 'Tags', [])
ADD_TAG: Breadcrumb = ('lynx:add_tag', 'Add Tag', [])
NOTES: Breadcrumb = ('lynx:all_notes', 'Notes', [])


# Convencience functions for consistency
def FEED_ITEMS(feed: Feed) -> Breadcrumb:
  return ('lynx:feed_items', feed.feed_name, [feed.pk])


def TAGGED_LINKS(tag_slug: str) -> Breadcrumb:
  return ('lynx:links_feed_tagged', tag_slug, [tag_slug])


def EDIT_LINK(link: Link) -> Breadcrumb:
  return ('lynx:link_details', 'Edit Link', [link.pk])


def EDIT_FEED(feed: Feed) -> Breadcrumb:
  return ('lynx:edit_feed', 'Edit Feed', [feed.pk])


# List of 3-ples.
def generate_breadcrumb_context_data(path_items: list[Breadcrumb], ) -> dict:
  breadcrumb_data = []
  for url_name, name, args in path_items:
    try:
      breadcrumb_data.append({
          'name': name,
          'url': reverse(url_name, args=args)
      })
    except NoReverseMatch:
      # Janky, but for search results we just want to provide
      # the full URL
      breadcrumb_data.append({'name': name, 'url': url_name})
  return {'breadcrumbs': breadcrumb_data}
