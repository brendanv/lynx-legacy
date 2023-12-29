from asgiref.sync import sync_to_async
from .decorators import async_login_required, lynx_post_only
from .widgets import FancyTextWidget
from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import aget_object_or_404, redirect
from lynx.models import FeedItem, Feed
from lynx import feed_utils, url_parser


@async_login_required
async def feeds_list_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  feeds = await (sync_to_async(list)(Feed.objects.filter(user=user,
                                                         is_deleted=False)))
  return TemplateResponse(request, 'lynx/feed_list.html', {
      'feeds_list': feeds,
  })


@async_login_required
async def feed_items_list_view(request: HttpRequest,
                               feed_id: int) -> HttpResponse:
  user = await request.auser()
  feed = await aget_object_or_404(Feed,
                                  pk=feed_id,
                                  is_deleted=False,
                                  user=user)
  feed_items = await (sync_to_async(list)(
      FeedItem.objects.filter(feed=feed).order_by('-pub_date')))
  return TemplateResponse(request, 'lynx/feed_item_list.html', {
      'feed_items_list': feed_items,
      'feed': feed
  })


@async_login_required
@lynx_post_only
async def refresh_all_feeds_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  feeds = Feed.objects.filter(user=user, is_deleted=False)
  async for feed in feeds:
    loader = await (sync_to_async(
        lambda: feed_utils.RemoteFeedLoader(user, request, feed=feed).
        load_remote_feed().persist_new_feed_items().persist_feed())())
    if len(loader.get_new_entries()) > 0:
      messages.success(
          request,
          f"Feed (ID {loader.get_feed().pk}) refreshed and {len(loader.get_new_entries())} entries added."
      )
  return redirect('lynx:feeds')


@async_login_required
@lynx_post_only
async def refresh_feed_from_remote_view(request: HttpRequest,
                                        pk: int) -> HttpResponse:
  user = await request.auser()
  feed = await aget_object_or_404(Feed, pk=pk, user=user)
  loader = await (sync_to_async(
      lambda: feed_utils.RemoteFeedLoader(user, request, feed=feed).
      load_remote_feed().persist_new_feed_items().persist_feed())())
  if len(loader.get_new_entries()) > 0:
    messages.success(
        request,
        f"Feed (ID {loader.get_feed().pk}) refreshed and {len(loader.get_new_entries())} entries added."
    )
  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def add_feed_item_to_library_view(request: HttpRequest, pk):
  user = await request.auser()
  feed_item = await aget_object_or_404(
      FeedItem.objects.select_related('feed__user'),
      pk=pk,
      feed__user=user)
  feed = feed_item.feed

  url = feed_item.saved_as_link
  if url is None:
    stripped_headers = url_parser.extract_headers_to_pass_for_parse(request)
    url = await (sync_to_async(lambda: url_parser.parse_url(
        feed_item.url, user, stripped_headers))())
    url.created_from_feed = feed
    await url.asave()

    feed_item.saved_as_link = url
    await feed_item.asave()

  return redirect('lynx:feed_items', feed_id=feed.pk)


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
      user = await request.auser()
      await (sync_to_async(lambda: form.create_feed(request, user))())
      return redirect('lynx:feeds')
  else:
    form = AddFeedForm()

  return TemplateResponse(request, 'lynx/add_feed.html', {'form': form})
