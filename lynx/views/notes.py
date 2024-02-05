from django.http import HttpRequest, HttpResponse
from django.shortcuts import aget_object_or_404, redirect
from django.template.response import TemplateResponse
from django.contrib import messages
from lynx import commands
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
  fragment = ''
  if 'note' in request.POST:
    note = await commands.create_note_for_link(user, link, request.POST['note'])
    fragment = note.fragment()
  if 'next' in request.POST:
    return redirect(request.POST['next'] + fragment)
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