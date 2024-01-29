from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .decorators import async_login_required, lynx_post_only
from .widgets import FancyTextWidget
from . import paginator, breadcrumbs
from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import aget_object_or_404, aget_list_or_404, redirect
from django.db.models import Count
from lynx.models import FeedItem, Feed, Link
from lynx.utils import headers
from lynx import feed_utils, url_parser


@async_login_required
async def feeds_list_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  queryset = Feed.objects.filter(user=user, is_deleted=False).annotate(
      num_items=Count('item')).order_by('-created_at')
  paginator_data = await paginator.generate_paginator_context_data(
      request, queryset)
  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data(
      [breadcrumbs.HOME, breadcrumbs.FEEDS])
  return TemplateResponse(request,
                          'lynx/feed_list.html',
                          context=paginator_data | breadcrumb_data)


@async_login_required
async def feed_items_list_view(request: HttpRequest,
                               feed_id: int) -> HttpResponse:
  user = await request.auser()
  feed = await aget_object_or_404(Feed,
                                  pk=feed_id,
                                  is_deleted=False,
                                  user=user)
  queryset = FeedItem.objects.filter(feed=feed).order_by('-pub_date')
  paginator_data = await paginator.generate_paginator_context_data(
      request, queryset)
  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data(
      [breadcrumbs.HOME, breadcrumbs.FEEDS,
       breadcrumbs.FEED_ITEMS(feed)])
  return TemplateResponse(request,
                          'lynx/feed_item_list.html',
                          context={'feed': feed} | paginator_data
                          | breadcrumb_data)


@async_login_required
@lynx_post_only
async def refresh_all_feeds_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
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
  await headers.maybe_update_usersetting_headers(request, user)
  feed = await aget_object_or_404(Feed, pk=pk, user=user)
  loader = await (sync_to_async(
      lambda: feed_utils.RemoteFeedLoader(user, request, feed=feed).
      load_remote_feed().persist_new_feed_items().persist_feed())())
  if len(loader.get_new_entries()) > 0:
    messages.success(
        request,
        f"Feed (ID {loader.get_feed().pk}) refreshed and {len(loader.get_new_entries())} entries added."
    )
  else:
    messages.warning(request,
                     f"Feed (ID {loader.get_feed().pk}) already up to date.")

  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def delete_feed_view(request: HttpRequest, pk: int) -> HttpResponse:
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  feed = await aget_object_or_404(Feed, pk=pk, user=user)
  previous_id = feed.id
  await feed.adelete()
  messages.success(request, f"Feed (ID {previous_id}) has been deleted.")

  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:feeds')


async def convert_feed_item_to_link(request: HttpRequest,
                                    feed_item: FeedItem) -> FeedItem:
  user = await request.auser()
  url = await (sync_to_async(
      lambda: url_parser.parse_url(feed_item.url, user))())
  url.created_from_feed = feed_item.feed
  await url.asave()
  feed_item.saved_as_link = url
  await feed_item.asave()
  return feed_item


@async_login_required
@lynx_post_only
async def add_feed_item_to_library_view(request: HttpRequest, pk):
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  feed_item = await aget_object_or_404(
      FeedItem.objects.select_related('feed__user'), pk=pk, feed__user=user)
  feed = feed_item.feed

  url = feed_item.saved_as_link
  if url is None:
    await convert_feed_item_to_link(request, feed_item)

  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def add_all_feed_items_to_library_view(request: HttpRequest, pk):
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  feed = await aget_object_or_404(Feed, pk=pk, user=user)
  count = 0
  async for item in feed.items.filter(saved_as_link__isnull=True):
    await convert_feed_item_to_link(request, item)
    count += 1
  if count > 0:
    messages.success(request, f"Added {count} new feed items to library.")
  else:
    messages.warning(request, "All feed items are alreay in your library")
  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def remove_feed_item_from_library_view(request: HttpRequest, pk):
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  link = await aget_object_or_404(Link,
                                  creator=user,
                                  created_from_feed_item=pk)
  await link.adelete()
  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:feeds')


class AddFeedForm(forms.Form):
  url = forms.URLField(label="",
                       max_length=2000,
                       widget=FancyTextWidget('Feed URL'))

  def create_feed(self, request: HttpRequest, user: User) -> Feed:
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
      await headers.maybe_update_usersetting_headers(request, user)
      await (sync_to_async(lambda: form.create_feed(request, user))())
      return redirect('lynx:feeds')
  else:
    form = AddFeedForm()

  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data(
      [breadcrumbs.HOME, breadcrumbs.FEEDS, breadcrumbs.ADD_FEED])
  return TemplateResponse(request, 'lynx/add_feed.html',
                          {'form': form} | breadcrumb_data)
