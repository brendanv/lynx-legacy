from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer, APIKeyHeader
from lynx.models import UserSetting, Link
from lynx import commands
from typing import Any, Optional

api = NinjaAPI()


class LynxKeyAuthenticator:

  async def authenticate(self, request: HttpRequest,
                   key: Optional[str]) -> Optional[UserSetting]:
    if key is None or key == "":
      return None
    try:
      return await UserSetting.objects.aget(lynx_api_key=key)
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
async def create_link(request, link_create: LinkCreate):
  assert isinstance(request.auth, UserSetting)
  user = await (sync_to_async(lambda: request.auth.user)())
  url, _ = await commands.get_or_create_link(link_create.url, user)
  await url.asave()
  return url
