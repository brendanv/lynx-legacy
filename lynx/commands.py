from asgiref.sync import sync_to_async
from typing import Tuple, Optional
from lynx import url_parser
from lynx.models import Link, Note
from django.db.models import Q


async def get_or_create_link(url: str,
                             user,
                             model_fields: Optional[dict] = None
                             ) -> Tuple[Link, bool]:
  # We could probably make this work with get_or_create but
  # this way we avoid loading the external link altogether in the case
  # where the link already exists.
  existing_link = await Link.objects.filter(Q(cleaned_url__iexact=url)
                                            | Q(original_url__iexact=url),
                                            creator=user).afirst()
  if existing_link is not None:
    return (existing_link, False)

  link = await (
      sync_to_async(lambda: url_parser.parse_url(url, user, model_fields))())
  await link.asave()
  return (link, True)


async def create_note_for_link(user, link: Link, note_content: str) -> Note:
  return await Note.objects.acreate(
      user=user,
      content=note_content,
      link=link,
      hostname=link.hostname,
      url=link.cleaned_url,
      link_title=link.title,
  )


async def create_note(user, url: str, note_content: str) -> Note:
  link, _ = await get_or_create_link(url, user)
  return await create_note_for_link(user, link, note_content)
