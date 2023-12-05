from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.security import HttpBearer, APIKeyHeader
from lynx.models import UserSetting
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


@api.post("/test", auth=lynx_auth_methods)
def hello(request):
  return "Success"
