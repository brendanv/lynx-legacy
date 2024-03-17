from typing import Tuple, Optional
from lynx import url_parser
from lynx.models import Link, LinkArchive, Note, UserCookie
from django.db.models import Q
from urllib.parse import urlparse

from lynx.utils.singlefile import get_singlefile_content


async def get_or_create_link(url: str,
                             user,
                             model_fields: Optional[dict] = None
                             ) -> Tuple[Link, bool]:
  # We could probably make this work with get_or_create but
  # this way we avoid loading the external link altogether in the case
  # where the link already exists.
  existing_link = await Link.objects.filter(Q(cleaned_url__iexact=url)
                                            | Q(original_url__iexact=url),
                                            user=user).afirst()
  if existing_link is not None:
    return (existing_link, False)

  link = await url_parser.parse_url(url, user, model_fields)
  await link.asave()
  return (link, True)


async def get_or_create_link_with_content(
    url: str,
    content: str,
    user,
    model_fields: Optional[dict] = None) -> Tuple[Link, bool]:
  existing_link = await Link.objects.filter(Q(cleaned_url__iexact=url)
                                            | Q(original_url__iexact=url),
                                            user=user).afirst()
  if existing_link is not None:
    return (existing_link, False)
  link = url_parser.parse_url_with_content(url, content, user, model_fields)
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


# Potentially raises a ReadTimeout if the archive service has
# an error!
async def create_archive_for_link(user, link: Link) -> Optional[LinkArchive]:
  existing_archive = await LinkArchive.objects.filter(link=link).afirst()
  if existing_archive is not None:
    return existing_archive

  url = link.original_url
  domain = urlparse(url).netloc
  cookies = UserCookie.objects.filter(user=user, cookie_domain=domain)
  cookie_data = [
      # See https://github.com/gildas-lormeau/single-file-cli/blob/5b9d11bc0b1a9dfe08d92207045c9d6d09c24fbf/options.js#L59
      # (name,value,domain,path,expires,httpOnly,secure,sameSite,url)
      ','.join([
          cookie.cookie_name, cookie.cookie_value, cookie.cookie_domain
      ]) async for cookie in cookies
  ]
  print(cookie_data)

  archive_content = await get_singlefile_content(url, cookies=cookie_data)
  if archive_content is None:
    return None
  return await LinkArchive.objects.acreate(
      user=user,
      link=link,
      archive_content=archive_content,
  )
