from httpx import ReadTimeout
from lynx.commands import create_archive_for_link
from lynx.models import Link, LinkArchive
from lynx.utils.singlefile import is_singlefile_enabled
from .decorators import async_login_required, lynx_post_only
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import aget_object_or_404, redirect

@async_login_required
@lynx_post_only
async def create_archive_view(request: HttpRequest, link_pk: int) -> HttpResponse:
  if not is_singlefile_enabled():
    messages.warning(request, 'SingleFile archives are not enabled')
    return redirect('lynx:link_details', link_pk)
    
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=link_pk, user=user)
  try: 
    archive = await create_archive_for_link(user, link)
  except ReadTimeout:
    messages.error(request, 'Archive creation timed out')
    return redirect('lynx:link_details', link_pk)
    
  if archive is None:
    messages.error(request, 'Failed to create archive')
    return redirect('lynx:link_details', link_pk)
    
  return redirect('lynx:link_archive', link_pk)
  
async def link_archive_view(request: HttpRequest, link_pk: int) -> HttpResponse:
  user = await request.auser()
  archive = await aget_object_or_404(LinkArchive, user=user, link__pk=link_pk)
  return HttpResponse(archive.archive_content)