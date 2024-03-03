from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .decorators import async_login_required, lynx_post_only
from .widgets import FancyTextWidget
from . import paginator, breadcrumbs
from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import aget_object_or_404, redirect
from django.db.models import Count, OuterRef, Subquery
from lynx.models import FeedItem, Feed, Link
from lynx.utils import headers
from lynx import feed_utils, tasks


@async_login_required
async def feeds_list_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  queryset = Feed.objects.filter(user=user, is_deleted=False).annotate(
      num_items=Count('item')).annotate(last_feed_item_created_at=Subquery(
          FeedItem.objects.filter(feed=OuterRef('pk')).values('created_at').
          order_by('-created_at')[:1])).order_by('-last_feed_item_created_at')
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
    await (sync_to_async(lambda: tasks.add_feed_item_to_library.now(
        feed.user.pk, feed_item.pk))())

  return redirect('lynx:feed_items', feed_id=feed.pk)


@async_login_required
@lynx_post_only
async def add_all_feed_items_to_library_view(request: HttpRequest, pk):
  user = await request.auser()
  await headers.maybe_update_usersetting_headers(request, user)
  feed = await aget_object_or_404(Feed, pk=pk, user=user)
  count = 0
  async for item in feed.items.filter(saved_as_link__isnull=True):
    await (sync_to_async(
        lambda: tasks.add_feed_item_to_library(feed.user.pk, item.pk))())
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
  link = await aget_object_or_404(Link, user=user, created_from_feed_item=pk)
  await link.adelete()
  if 'next' in request.POST:
    return redirect(request.POST['next'])
  return redirect('lynx:feeds')


class AddFeedForm(forms.Form):
  url = forms.URLField(label="",
                       max_length=2000,
                       widget=FancyTextWidget('Feed URL'))
  auto_add = forms.BooleanField(
      required=False,
      label="Auto-add new articles to library",
      widget=forms.CheckboxInput(attrs={
          'class': 'checkbox checkbox-primary',
          'required': False
      }))

  def create_feed(self, request: HttpRequest, user: User) -> Feed:
    loader = feed_utils.RemoteFeedLoader(
        user,
        request,
        feed_url=self.cleaned_data['url'],
        auto_add=self.cleaned_data['auto_add']).load_remote_feed(
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


class EditFeedForm(forms.Form):
  feed_name = forms.CharField(label="",
                              max_length=1000,
                              widget=FancyTextWidget('Feed Name'))
  feed_description = forms.CharField(
      label="", max_length=1000, widget=FancyTextWidget('Feed Description'))
  auto_add = forms.BooleanField(
      label="Auto-add new articles to library",
      required=False,
      widget=forms.CheckboxInput(attrs={
          'class': 'checkbox checkbox-primary',
      }))


@async_login_required
async def edit_feed_view(request: HttpRequest, feed_id: int) -> HttpResponse:
  user = await request.auser()
  feed = await aget_object_or_404(Feed, pk=feed_id, user=user)
  if request.method == 'POST':
    form = EditFeedForm(request.POST)
    if form.is_valid():
      feed.feed_name = form.cleaned_data['feed_name']
      feed.feed_description = form.cleaned_data['feed_description']
      feed.auto_add_feed_items_to_library = form.cleaned_data['auto_add']
      await feed.asave()
      messages.success(request, 'Feed details updated')

  else:
    form = EditFeedForm(
        initial={
            'feed_name': feed.feed_name,
            'feed_description': feed.feed_description,
            'auto_add': feed.auto_add_feed_items_to_library
        })

  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data([
      breadcrumbs.HOME, breadcrumbs.FEEDS,
      breadcrumbs.FEED_ITEMS(feed),
      breadcrumbs.EDIT_FEED(feed)
  ])
  return TemplateResponse(request,
                          "lynx/edit_feed.html",
                          context={
                              'feed': feed,
                              'form': form
                          } | breadcrumb_data)
