from typing import Optional
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone
from django.urls import resolve, Resolver404
from datetime import timedelta
from lynx.models import UserSetting
from urllib.parse import urlparse

DAYS_TO_KEEP_HEADERS = 3


def extract_headers_to_pass_for_parse(request: HttpRequest) -> dict[str, str]:
  # Headers to make the request look less like scraping but while also
  # not really changing the behavior at all.
  supported_headers = [
      'accept', 'accept-language', 'user-agent', 'dnt', 'sec-fetch-dest',
      'sec-fetch-mode'
  ]
  return {
      k.lower(): v
      for k, v in request.headers.items() if k.lower() in supported_headers
  }


async def maybe_update_usersetting_headers(request: HttpRequest, user: User):
  user_settings, _ = await UserSetting.objects.aget_or_create(user=user)
  should_update = (user_settings.headers_for_scraping is None
                   or user_settings.headers_updated_at is None
                   or user_settings.headers_updated_at <
                   (timezone.now() - timedelta(days=DAYS_TO_KEEP_HEADERS)))
  if should_update:
    user_settings.headers_for_scraping = extract_headers_to_pass_for_parse(
        request)
    user_settings.headers_updated_at = timezone.now()
    await user_settings.asave()


def get_lynx_referrer_or_default(request: HttpRequest,
                                 exclude_route: Optional[str] = None) -> str:
  referrer = request.META.get('HTTP_REFERER', None)
  if referrer:
    parsed_url = urlparse(referrer)
    path = parsed_url.path
    query = parsed_url.query
    try:
      match = resolve(path)
      if match.route == exclude_route:
        return '/'
      return f'{path}?{query}' if query else path
    except Resolver404:
      return '/'
  return '/'
