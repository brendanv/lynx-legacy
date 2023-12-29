from django.core.paginator import Paginator
from django.http import HttpRequest
from asgiref.sync import sync_to_async

async def generate_paginator_context_data(request: HttpRequest, items) -> dict:
  page_number = request.GET.get('page', '1')
  paginator = Paginator(items, 10, orphans=2)
  page_obj = await (sync_to_async(paginator.get_page)(page_number))
  return {
    'paginator_page': page_obj,
    'paginator': paginator,
  }
