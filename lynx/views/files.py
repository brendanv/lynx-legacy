from asgiref.sync import async_to_sync, sync_to_async
from background_task import background
import csv
import codecs
from datetime import datetime as datetime
from dateutil import parser
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.files.base import File
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from lynx import commands
from lynx.models import Tag, BulkUpload
from typing import Optional
from .widgets import DaisySelect
from . import breadcrumbs

class BulkUploadLinksForm(forms.Form):
  file = forms.FileField()
  file_source = forms.ChoiceField(choices=[('readwise', 'Readwise')], widget=DaisySelect())

async def bulk_upload_view(request: HttpRequest) -> HttpResponse:
  user = await request.auser()
  if request.method == 'POST':
    form = BulkUploadLinksForm(request.POST, request.FILES)
    if form.is_valid():
      match form.cleaned_data['file_source']:
        case 'readwise':
          bulk_upload = await BulkUpload.objects.acreate(user = user)
          bulk_tag, _ = await Tag.objects.aget_or_create(name=f'readwise_upload_{bulk_upload.pk}', user=user)
          bulk_upload.tag_slug = bulk_tag.slug
          await bulk_upload.asave()
          await handle_readwise_upload(request, request.FILES['file'], bulk_tag.name)
          return redirect('lynx:links_feed_tagged', slug=bulk_tag.slug)
        case _:
          messages.warning(request, 'Unsupported file source')
  else:
    form = BulkUploadLinksForm()

  breadcrumb_data = breadcrumbs.generate_breadcrumb_context_data([
    breadcrumbs.HOME, breadcrumbs.BULK_UPLOAD
  ])
  return TemplateResponse(request, 'lynx/bulk_upload.html', context={'form': form} | breadcrumb_data)

async def handle_readwise_upload(request: HttpRequest, file: File, bulk_tag: str) -> None:
  user = await request.auser()
  reader = csv.DictReader(codecs.iterdecode(file, 'utf-8'))
  for row in reader:
    url = row['URL']
    if url.startswith('mailto'):
      continue
    tags = []
    if len(row.get('Document tags', '')) > 2:
      tags = [
        tag.strip().removesuffix("'").removeprefix("'") for tag 
        in row['Document tags'][1:-1].split(', ')]
    tags.append(bulk_tag)

    last_viewed_at = None
    if float(row.get('Reading progress', '0')) > 0.75:
      last_viewed_at = str(timezone.now())

    added_at = str(timezone.now())
    if row.get('Saved date'):
      added_at = str(parser.parse(row['Saved date']))
    
    await (sync_to_async(add_new_link_in_background)(user.pk, url, tags, last_viewed_at, added_at))
    print(row)

@background
def add_new_link_in_background(user_pk: int, url: str, tags: list[str],  last_viewed_at_str: Optional[str], added_at_str: Optional[str]):
  user = User.objects.get(pk=user_pk)
  tag_models = [Tag.objects.get_or_create(name=tag, user=user)[0] for tag in tags]
  
  added_at = timezone.now()
  if added_at_str:
    added_at = parser.parse(added_at_str)
    
  last_viewed_at = None
  if last_viewed_at_str:
    last_viewed_at = parser.parse(last_viewed_at_str)

  link, _ = async_to_sync(commands.get_or_create_link)(url, user, model_fields={
    'added_at': added_at,
    'last_viewed_at': last_viewed_at,
  })
  link.save()
  
  if tag_models:
    link.tags.set(tag_models)
    link.save()