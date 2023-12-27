from asgiref.sync import sync_to_async
from django.http import JsonResponse, HttpResponseNotAllowed, HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.forms.widgets import TextInput
from django.contrib import messages
from extra_views import ModelFormSetView
from lynx import feed_utils, url_parser, url_summarizer, html_cleaner
from lynx.models import FeedItem, Link, UserSetting, UserCookie, Feed
from lynx.errors import NoAPIKeyInSettings
import secrets
import functools
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import aget_object_or_404, redirect


def async_login_required(view_func):

  @functools.wraps(view_func)
  async def wrapper(request: HttpRequest, *args, **kwargs):
    if not await (sync_to_async(lambda: request.user.is_authenticated)()):
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


class APIKeyWidget(TextInput):
  template_name = "widgets/api_key_widget.html"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.attrs['readonly'] = ''


class FancyTextWidget(TextInput):
  template_name = "widgets/fancy_text_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['display_name'] = display_name


class FancyPasswordWidget(forms.PasswordInput):
  template_name = "widgets/fancy_password_widget.html"

  def __init__(self, display_name, **kwargs):
    super().__init__(**kwargs)
    self.attrs['display_name'] = display_name
    self.attrs['autocomplete'] = 'off'


class AddLinkForm(forms.Form):
  url = forms.URLField(label="",
                       max_length=2000,
                       widget=FancyTextWidget('Article URL'))

  def create_link(self, user) -> Link:
    url = url_parser.parse_url(self.cleaned_data['url'], user)
    url.save()
    return url


@async_login_required
async def add_link_view(request: HttpRequest) -> HttpResponse:
  if request.method == 'POST':
    form = AddLinkForm(request.POST)
    if form.is_valid():
      link = await (sync_to_async(lambda: form.create_link(request.user))())
      return redirect('lynx:link_viewer', pk=link.pk)
  else:
    form = AddLinkForm()

  return TemplateResponse(request, 'lynx/add_link.html', {'form': form})


@async_login_required
@lynx_post_only
async def summarize_link_view(request: HttpRequest, pk: int) -> HttpResponse:
  try:
    link = await aget_object_or_404(Link, pk=pk, creator=request.user)
    link = await url_summarizer.generate_and_persist_summary(link)

    return redirect('lynx:link_details', pk=link.pk)
  except NoAPIKeyInSettings:
    return JsonResponse(
        {"error": "You must have an OpenAI API key in your settings."})


@async_login_required
async def readable_view(request: HttpRequest, pk: int) -> HttpResponse:
  link = await Link.objects.aget(pk=pk, creator=request.user)
  context_data = {'link': link}
  cleaner = html_cleaner.HTMLCleaner(link.article_html)
  cleaner.generate_headings().replace_image_links_with_images()
  context_data = {
      'link': link,
      'html_with_sections': cleaner.prettify(),
      'table_of_contents': [h.to_dict() for h in cleaner.get_headings()]
  }

  link.last_viewed_at = timezone.now()
  await link.asave()
  return TemplateResponse(request, "lynx/link_viewer.html", context_data)


@async_login_required
async def details_view(request: HttpRequest, pk: int) -> HttpResponse:
  link = await aget_object_or_404(Link, pk=pk, creator=request.user)
  return TemplateResponse(request, "lynx/link_details.html", {'link': link})


@async_login_required
async def link_feed_view(request: HttpRequest, filter: str = "all") -> HttpResponse:
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
    queryset = Link.objects.raw(sql, [query_string, request.user.id])
  else:
    queryset = Link.objects.filter(creator=request.user)
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

  data['links_list'] = await (sync_to_async(list)(queryset))
  return TemplateResponse(request, "lynx/links_feed.html", context=data)


class UpdateSettingsForm(forms.Form):
  openai_api_key = forms.CharField(label="",
                                   max_length=255,
                                   widget=FancyPasswordWidget(
                                       'OpenAI API Key', render_value=True),
                                   required=False)

  lynx_api_key = forms.CharField(
      label="",
      max_length=255,
      required=False,
      widget=APIKeyWidget(),
  )

  def update_setting(self, user):
    setting, _ = UserSetting.objects.get_or_create(user=user)
    if 'reset_api_key' in self.data:
      setting.lynx_api_key = secrets.token_hex(16)
    elif 'clear_api_key' in self.data:
      setting.lynx_api_key = ""
    setting.save()


@async_login_required
async def update_settings_view(request: HttpRequest) -> HttpResponse:
  setting, _ = await UserSetting.objects.aget_or_create(user=request.user)
  if request.method == 'POST':
    form = UpdateSettingsForm(request.POST)
    if form.is_valid():
      await (sync_to_async(lambda: form.update_setting(request.user))())
      messages.success(request, "Settings updated.")
      return redirect('lynx:user_settings')
  else:
    form = UpdateSettingsForm(
        initial={
            'openai_api_key': setting.openai_api_key,
            'lynx_api_key': setting.lynx_api_key,
        })

  return TemplateResponse(request, "lynx/usersetting_form.html",
                          {'form': form})


class UpdateCookiesView(LoginRequiredMixin, ModelFormSetView):
  model = UserCookie
  fields = ["user", "cookie_name", "cookie_value", "cookie_domain"]
  template_name = 'lynx/usercookie_form.html'

  def get_factory_kwargs(self):
    args = super().get_factory_kwargs()
    args['can_delete'] = True
    args['can_delete_extra'] = False
    args['labels'] = {
        'cookie_name': '',
        'cookie_value': '',
        'cookie_domain': ''
    }
    args['widgets'] = {
        'user':
        forms.HiddenInput(),
        'cookie_value':
        FancyPasswordWidget('Cookie Value', render_value=True),
        'cookie_name':
        FancyTextWidget('Cookie Name', attrs={'autocomplete': 'off'}),
        'cookie_domain':
        FancyTextWidget('Cookie Domain', attrs={'autocomplete': 'off'}),
    }
    return args

  def get_formset(self):
    formset = super().get_formset()
    formset.deletion_widget = forms.CheckboxInput(
        attrs={'class': 'checkbox checkbox-primary'})
    return formset

  def get_initial(self):
    return [{
        'user': self.request.user,
    }]

  def get_queryset(self):
    return UserCookie.objects.filter(user=self.request.user)


@async_login_required
async def feeds_list_view(request: HttpRequest) -> HttpResponse:
  feeds = await (sync_to_async(list)(Feed.objects.filter(user=request.user,
                                                         is_deleted=False)))
  return TemplateResponse(request, 'lynx/feed_list.html', {
      'feeds_list': feeds,
  })


class AddFeedForm(forms.Form):
  url = forms.URLField(label="",
                       max_length=2000,
                       widget=FancyTextWidget('Feed URL'))

  def create_feed(self, request, user) -> Feed:
    loader = feed_utils.RemoteFeedLoader(
        user, request, feed_url=self.cleaned_data['url']).load_remote_feed(
        ).persist_new_feed_items().persist_feed()
    messages.success(
        request,
        f"Feed (ID {loader.get_feed().pk}) created and {len(loader.get_new_entries())} entries added."
    )
    return loader.get_feed()


@async_login_required
async def add_feed_view(request: HttpRequest) -> HttpResponse:
  if request.method == 'POST':
    form = AddFeedForm(request.POST)
    if form.is_valid():
      await (sync_to_async(lambda: form.create_feed(request, request.user))())
      return redirect('lynx:feeds')
  else:
    form = AddFeedForm()

  return TemplateResponse(request, 'lynx/add_feed.html', {'form': form})


@async_login_required
async def feed_items_list_view(request: HttpRequest,
                               feed_id: int) -> HttpResponse:
  feed = await aget_object_or_404(Feed.objects.select_related('user'),
                                  pk=feed_id,
                                  is_deleted=False)
  if feed.user != request.user:
    raise Feed.DoesNotExist()
  feed_items = await (sync_to_async(list)(
      FeedItem.objects.filter(feed=feed).order_by('-pub_date')))
  return TemplateResponse(request, 'lynx/feed_item_list.html', {
      'feed_items_list': feed_items,
      'feed': feed
  })


@async_login_required
@lynx_post_only
async def add_feed_item_to_library_view(request: HttpRequest, pk):
  feed_item = await aget_object_or_404(
      FeedItem.objects.select_related('feed__user'),
      pk=pk,
      feed__user=request.user)
  feed = feed_item.feed

  url = feed_item.saved_as_link
  if url is None:
    url = await (sync_to_async(
        lambda: url_parser.parse_url(feed_item.url, request.user))())
    url.created_from_feed = feed
    await url.asave()

    feed_item.saved_as_link = url
    await feed_item.asave()

  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def refresh_feed_from_remote_view(request: HttpRequest, pk: int) -> HttpResponse:
  feed = await aget_object_or_404(Feed, pk=pk, user=request.user)
  loader = await (sync_to_async(
      lambda: feed_utils.RemoteFeedLoader(request.user, request, feed=feed).
      load_remote_feed().persist_new_feed_items().persist_feed())())
  if len(loader.get_new_entries()) > 0:
    messages.success(
        request,
        f"Feed (ID {loader.get_feed().pk}) refreshed and {len(loader.get_new_entries())} entries added."
    )
  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def refresh_all_feeds_view(request: HttpRequest) -> HttpResponse:
  feeds = Feed.objects.filter(user=request.user, is_deleted=False)
  async for feed in feeds:
    loader = await (sync_to_async(
        lambda: feed_utils.RemoteFeedLoader(request.user, request, feed=feed).
        load_remote_feed().persist_new_feed_items().persist_feed())())
    if len(loader.get_new_entries()) > 0:
      messages.success(
          request,
          f"Feed (ID {loader.get_feed().pk}) refreshed and {len(loader.get_new_entries())} entries added."
      )
  return redirect('lynx:feeds')
