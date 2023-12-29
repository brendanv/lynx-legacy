from asgiref.sync import sync_to_async
from django.contrib.auth.views import redirect_to_login
import functools
from django.http import HttpResponseNotAllowed, HttpRequest

def async_login_required(view_func):

  @functools.wraps(view_func)
  async def wrapper(request: HttpRequest, *args, **kwargs):
    user = await request.auser()
    if not await (sync_to_async(lambda: user.is_authenticated)()):
      return redirect_to_login(request.get_full_path())
    return await view_func(request, *args, **kwargs)

  return wrapper


def lynx_post_only(view_func):

  @functools.wraps(view_func)
  async def wrapper(request, *args, **kwargs):
    if request.method != 'POST':
      return HttpResponseNotAllowed(['POST'])
    return await view_func(request, *args, **kwargs)

  return wrapper