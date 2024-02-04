from django.http import HttpRequest, HttpResponse
from django.shortcuts import aget_object_or_404, redirect
from django.template.response import TemplateResponse
from django.contrib import messages
from lynx.models import Link, Note
from lynx.utils import headers
from .decorators import async_login_required, lynx_post_only
from . import paginator, breadcrumbs


@async_login_required
@lynx_post_only
async def add_note_view(request: HttpRequest, link_pk: int) -> HttpResponse:
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  link = await aget_object_or_404(Link, pk=link_pk, creator=user)
  if 'note' in request.POST:
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

@async_login_required
async def link_notes_view(request: HttpRequest, link_pk: int) -> HttpResponse:
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=link_pk, creator=user)
  paginator_data = await paginator.generate_paginator_context_data(
      request, Note.objects.filter(link=link, user=user).order_by('-saved_at'))
  
  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data(
      [breadcrumbs.HOME, breadcrumbs.NOTES])
  return TemplateResponse(request,
                          'lynx/notes_list.html',
                          context={'link': link} | paginator_data
                          | breadcrumb_data)

@async_login_required
async def all_notes_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  paginator_data = await paginator.generate_paginator_context_data(
      request, Note.objects.filter(user=user).order_by('-saved_at'))
  
  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data(
      [breadcrumbs.HOME, breadcrumbs.NOTES])
  return TemplateResponse(request,
                          'lynx/notes_list.html',
                          context=paginator_data | breadcrumb_data)

@async_login_required
@lynx_post_only
async def delete_note_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  note = await aget_object_or_404(Note, pk=pk, user=user)
  await note.adelete()

  messages.success(request, 'Note deleted')
  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:all_notes')