from django.http import HttpRequest, HttpResponse
from django.shortcuts import aget_object_or_404, redirect
from lynx.models import Link, Note
from lynx.utils import headers
from .decorators import async_login_required, lynx_post_only


@async_login_required
@lynx_post_only
async def add_note_view(request: HttpRequest, link_pk: int) -> HttpResponse:
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  link = await aget_object_or_404(Link, pk=link_pk, creator=user)
  if 'note' in request.POST:
    print(request.POST)
    await Note.objects.acreate(
        user=user,
        content=request.POST['note'],
        link=link,
        hostname=link.hostname,
        url=link.cleaned_url,
    )
  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:links_feed_all')
