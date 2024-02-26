from django.utils import timezone
from django.contrib.auth.models import User
from django.test import TestCase
from lynx.models import Link, Tag
from lynx.utils.search import (query_models, SEARCH_QUERY_PARAMETER,
                               SEARCH_TAG_PARAMETER, SEARCH_UNREAD_PARAMETER,
                               SEARCH_UNREAD_READ_ONLY_VALUE,
                               SEARCH_UNREAD_UNREAD_ONLY_VALUE)
from django.http import HttpRequest


class SearchTestCase(TestCase):

  def create_test_link(self, **kwargs) -> Link:
    default_user, _ = User.objects.get_or_create(username='default_user')
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'user': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    link.save()
    return link

  def test_search_requires_all_fields_match(self):
    default_user, _ = User.objects.get_or_create(username='default_user')
    other_user, _ = User.objects.get_or_create(username='other_user')
    tag = Tag.objects.create(name="test tag", user=default_user)
    # Create a link with content, tags, and unread status
    link = self.create_test_link(title='Test Title with complicated words',
                                 raw_text_content='Confusing syntax',
                                 last_viewed_at=timezone.now())
    link.tags.set([tag])
    # Create another link without any of these things
    link2 = self.create_test_link()

    # Query should return the link that matches
    request = HttpRequest()
    request.GET[SEARCH_QUERY_PARAMETER] = 'complicated words'
    request.GET[SEARCH_TAG_PARAMETER] = tag.slug
    request.GET[SEARCH_UNREAD_PARAMETER] = SEARCH_UNREAD_READ_ONLY_VALUE
    queryset, _ = query_models(Link.objects.all(), request)
    results = list(queryset)
    self.assertEqual(len(results), 1)
    self.assertEqual(results[0].pk, link.pk)

    # No results expected if the search terms don't match
    # Mismatched text!
    request = HttpRequest()
    request.GET[SEARCH_QUERY_PARAMETER] = 'no results'
    request.GET[SEARCH_TAG_PARAMETER] = tag.slug
    request.GET[SEARCH_UNREAD_PARAMETER] = SEARCH_UNREAD_READ_ONLY_VALUE
    queryset, _ = query_models(Link.objects.all(), request)
    self.assertEqual(queryset.count(), 0)

    # Mismatched tag!
    request = HttpRequest()
    request.GET[SEARCH_QUERY_PARAMETER] = 'complicated words'
    request.GET[SEARCH_TAG_PARAMETER] = 'not-a-tag'
    request.GET[SEARCH_UNREAD_PARAMETER] = SEARCH_UNREAD_READ_ONLY_VALUE
    queryset, _ = query_models(Link.objects.all(), request)
    self.assertEqual(queryset.count(), 0)

    # Mismatched unread status!
    request = HttpRequest()
    request.GET[SEARCH_QUERY_PARAMETER] = 'complicated words'
    request.GET[SEARCH_TAG_PARAMETER] = tag.slug
    request.GET[SEARCH_UNREAD_PARAMETER] = SEARCH_UNREAD_UNREAD_ONLY_VALUE
    queryset, _ = query_models(Link.objects.all(), request)
    self.assertEqual(queryset.count(), 0)

    # We should also be able to get the other link to be returned
    request = HttpRequest()
    request.GET[SEARCH_UNREAD_PARAMETER] = SEARCH_UNREAD_UNREAD_ONLY_VALUE
    queryset, _ = query_models(Link.objects.all(), request)
    results = list(queryset)
    self.assertEqual(len(results), 1)
    self.assertEqual(results[0].pk, link2.pk)

    # It should also respect the passed in manager
    request = HttpRequest()
    queryset, _ = query_models(Link.objects.filter(user=other_user),
                               request)
    self.assertEqual(queryset.count(), 0)
