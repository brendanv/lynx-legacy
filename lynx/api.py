from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer, APIKeyHeader
from lynx.models import UserSetting, Link
from lynx import url_parser
from typing import Any, Optional

api = NinjaAPI()


class LynxKeyAuthenticator:

  def authenticate(self, request: HttpRequest,
                   key: Optional[str]) -> Optional[UserSetting]:
    if key is None or key == "":
      return None
    try:
      return UserSetting.objects.get(lynx_api_key=key)
    except UserSetting.DoesNotExist:
      return None


class LynxApiKeyHeader(LynxKeyAuthenticator, APIKeyHeader):
  param_name = "X-API-Key"


class LynxApiKeyBearer(LynxKeyAuthenticator, HttpBearer):
  pass


lynx_auth_methods = [LynxApiKeyBearer(), LynxApiKeyHeader()]

class LinkCreate(Schema):
  url: str

class LinkOverview(Schema):
  id: int
  original_url: str
  cleaned_url: str
  title: str = None
  author: str = None
  read_time_seconds: int = None
  read_time_display: str = None

@api.post("/links/add", auth=lynx_auth_methods, response=LinkOverview)
def create_link(request, link_create: LinkCreate):
  assert isinstance(request.auth, UserSetting)
  url = url_parser.parse_url(link_create.url, request.auth.user)
  url.save()
  return url
