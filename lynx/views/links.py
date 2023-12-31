from .decorators import async_login_required, lynx_post_only
from .widgets import FancyTextWidget
from . import paginator
from asgiref.sync import sync_to_async
from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from lynx import url_parser, url_summarizer, html_cleaner
from lynx.models import Link, Tag
from lynx.errors import NoAPIKeyInSettings, UrlParseError
from django.shortcuts import aget_object_or_404, aget_list_or_404, redirect


class AddLinkForm(forms.Form):
  url = forms.URLField(label="",
                       max_length=2000,
                       widget=FancyTextWidget('Article URL'))

  def create_link(self, user, headers={}) -> Link:
    url = url_parser.parse_url(self.cleaned_data['url'], user, headers)
    url.save()
    return url


@async_login_required
async def add_link_view(request: HttpRequest) -> HttpResponse:
  if request.method == 'POST':
    form = AddLinkForm(request.POST)
    if form.is_valid():
      try:
        stripped_headers = url_parser.extract_headers_to_pass_for_parse(
            request)
        user = await request.auser()
        link = await (
            sync_to_async(lambda: form.create_link(user, stripped_headers))())
        return redirect('lynx:link_viewer', pk=link.pk)
      except UrlParseError as e:
        messages.error(request,
                       f'Unable to parse link. The error was: {e.http_error}')
  else:
    form = AddLinkForm()

  return TemplateResponse(request, 'lynx/add_link.html', {'form': form})


@async_login_required
@lynx_post_only
async def link_actions_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=pk, creator=user)
  if 'action_delete' in request.POST:
    title = link.title
    await link.adelete()
    messages.info(request, f'Link "{title}" deleted.')
  elif 'action_toggle_unread' in request.POST:
    if link.last_viewed_at is None:
      link.last_viewed_at = timezone.now()
    else:
      link.last_viewed_at = None
    await link.asave()
  elif 'action_summarize' in request.POST:
    try:
      await url_summarizer.generate_and_persist_summary(link)
    except NoAPIKeyInSettings:
      messages.error(
          request,
          'You must have an OpenAI API key in your settings to summarize links.'
      )
  else:
    messages.warning(request, 'Unable to perform unknown action')

  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:links_feed')


@async_login_required
async def readable_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=pk, creator=user)
  context_data = {'link': link}
  cleaner = html_cleaner.HTMLCleaner(link.article_html)
  cleaner.generate_headings().replace_image_links_with_images()
  tags_queryset = link.tags.all()
  tags = await (sync_to_async(list)(tags_queryset))
  all_user_tags = await (sync_to_async(list)(Tag.objects.filter(creator=user)))
  context_data = {
      'link': link,
      'tags': tags,
      'all_user_tags': all_user_tags,
      'html_with_sections': cleaner.prettify(),
      'table_of_contents': [h.to_dict() for h in cleaner.get_headings()]
  }

  link.last_viewed_at = timezone.now()
  await link.asave()
  return TemplateResponse(request, "lynx/link_viewer.html", context_data)


@async_login_required
async def details_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=pk, creator=user)
  return TemplateResponse(request, "lynx/link_details.html", {'link': link})


@async_login_required
async def link_feed_view(request: HttpRequest,
                         filter: str = "all") -> HttpResponse:
  user = await request.auser()
  query_string = request.GET.get('q', '')
  if query_string:
    sql = '''
      SELECT lynx_link.*, rank 
      FROM lynx_link 
      INNER JOIN (
        SELECT rowid, rank 
        FROM lynx_link_fts 
        WHERE lynx_link_fts MATCH %s
      ) 
      ON lynx_link.id = rowid 
      WHERE lynx_link.creator_id = %s
      ORDER BY rank;
    '''
    queryset = Link.objects.raw(sql, [query_string, user.id])
  else:
    queryset = Link.objects.filter(creator=user)
    if filter == "read":
      queryset = queryset.filter(last_viewed_at__isnull=False)
    elif filter == "unread":
      queryset = queryset.filter(last_viewed_at__isnull=True)

    queryset = queryset.order_by('-created_at')

  data = {}
  data['selected_filter'] = filter
  data['query'] = query_string

  if filter == "read":
    data['title'] = "Read Links"
  elif filter == "unread":
    data['title'] = "Unread Links"
  elif filter == "search":
    data['title'] = "Search Results"
  else:
    data['title'] = "All Links"

  paginator_data = await paginator.generate_paginator_context_data(
      request, queryset)
  data = data | paginator_data
  return TemplateResponse(request, "lynx/links_feed.html", context=data)


@async_login_required
async def tagged_links_view(request: HttpRequest, slug: str) -> HttpResponse:
  user = await request.auser()
  tag = await aget_object_or_404(Tag, slug=slug, creator=user)
  queryset = Link.objects.filter(creator=user, tags=tag)
  data = {}
  data['title'] = f"Links tagged with '{tag.name}'"
  paginator_data = await paginator.generate_paginator_context_data(
      request, queryset)
  data = data | paginator_data
  return TemplateResponse(request, 'lynx/tagged_links_list.html', context=data)


@async_login_required
@lynx_post_only
async def link_tags_edit_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  link = await aget_object_or_404(Link, pk=pk, creator=user)
  if 'add_tags' in request.POST:
    ids = request.POST['add_tags'].split(',')
    tags = await aget_list_or_404(Tag, pk__in=ids, creator=user)
    for tag in tags:
      await (sync_to_async(lambda: link.tags.add(tag))())
  if 'remove_tags' in request.POST:
    ids = request.POST['remove_tags'].split(',')
    tags = await aget_list_or_404(Tag, pk__in=ids, creator=user)
    for tag in tags:
      await (sync_to_async(lambda: link.tags.remove(tag))())
  if 'clear_tags' in request.POST:
    await (sync_to_async(lambda: link.tags.clear())())
  if 'set_tags' in request.POST:
    tag_ids = [
        key[9:-1] for key, value in request.POST.items()
        if key.startswith('set_tags[')
    ]
    tags = await aget_list_or_404(Tag, pk__in=tag_ids, creator=user)
    await (sync_to_async(lambda: link.tags.set(tags))())
  if 'add_new_tag' in request.POST:
    new_tag_name = request.POST.get('new_tag_name', None)
    if new_tag_name:
      await link.tags.acreate(name=new_tag_name, creator=user)

  await link.asave()
  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:links_feed')
