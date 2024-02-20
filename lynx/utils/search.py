from typing import Optional, Tuple
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Manager
from django.http import HttpRequest
from enum import Enum

from lynx.views import breadcrumbs

SEARCH_QUERY_PARAMETER = 'q'
SEARCH_UNREAD_PARAMETER = 'r'
SEARCH_UNREAD_UNREAD_ONLY_VALUE = 'u'
SEARCH_UNREAD_READ_ONLY_VALUE = 'r'
SEARCH_TAG_PARAMETER = 't'

ReadStatusMode = Enum('ReadStatusMode', ['UNREAD', 'READ', 'ALL'])
  
def get_read_status_mode(request: HttpRequest) -> ReadStatusMode:
  param_value = request.GET.get(SEARCH_UNREAD_PARAMETER, None)
  if param_value == SEARCH_UNREAD_UNREAD_ONLY_VALUE:
    return ReadStatusMode.UNREAD
  elif param_value == SEARCH_UNREAD_READ_ONLY_VALUE:
    return ReadStatusMode.READ
  else:
    return ReadStatusMode.ALL


def breadcrumb_for_links(request: HttpRequest) -> Optional[breadcrumbs.Breadcrumb]:
  query_string = request.GET.get(SEARCH_QUERY_PARAMETER, None)
  read_status_mode = get_read_status_mode(request)
  tag_param = request.GET.get(SEARCH_TAG_PARAMETER, None)

  if query_string:
    return (request.get_full_path(), 'Search Results', [])

  if read_status_mode == ReadStatusMode.ALL and tag_param:
    return breadcrumbs.TAGGED_LINKS(tag_param)

  if read_status_mode == ReadStatusMode.READ:
    return (request.get_full_path(), 'Read Links', [])
  elif read_status_mode == ReadStatusMode.UNREAD:
    return (request.get_full_path(), 'Unread Links', [])

  return None


def query_models(objects: Manager,
                 request: HttpRequest) -> Tuple[Manager, dict[str, str | bool]]:
  # Returns a modified version of the provided Manager with additional
  # query terms added depending on the paramters in the Request. 
  # The returned dictionary contains the query terms that were 
  # parsed from the request so they can be easily used in views.

  modified_queryset = objects
  search_config: dict[str, str | bool] = {'should_expand': False}

  query_string = request.GET.get(SEARCH_QUERY_PARAMETER, '')
  if query_string:
    search_config['should_expand'] = True
    search_config["query_string"] = query_string
    search_query = SearchQuery(query_string,
                               search_type="websearch",
                               config='english')
    modified_queryset = objects.annotate(
        rank=SearchRank(F('content_search'), search_query)).filter(
            content_search=search_query, rank__gte=0.3).order_by('-rank')

  read_status_mode = get_read_status_mode(request)
  if read_status_mode == ReadStatusMode.READ:
    search_config['should_expand'] = True
    search_config["unread"] = "read"
    modified_queryset = modified_queryset.filter(last_viewed_at__isnull=False)
  elif read_status_mode == ReadStatusMode.UNREAD:
    search_config['should_expand'] = True
    search_config["unread"] = "unread"
    modified_queryset = modified_queryset.filter(last_viewed_at__isnull=True)
  else:
    search_config["unread"] = "all"

  tag_param = request.GET.get(SEARCH_TAG_PARAMETER, '')
  if tag_param:
    search_config['should_expand'] = True
    search_config["tag"] = tag_param
    modified_queryset = modified_queryset.filter(tags__slug=tag_param)

  return (modified_queryset, search_config)
