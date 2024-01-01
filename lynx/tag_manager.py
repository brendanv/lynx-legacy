from asgiref.sync import sync_to_async
from .models import Link, Tag
from django.shortcuts import aget_object_or_404
from lynx.errors import TagError


async def delete_tag_for_user(user, tag_pk: int) -> None:
  tag = await aget_object_or_404(Tag, pk=tag_pk, creator=user)
  await tag.adelete()


async def create_tag_for_user(user, tag_name: str) -> Tag:
  existing_tags = await (sync_to_async(list)(Tag.objects.filter(name=tag_name,
                                                                creator=user)))
  if existing_tags:
    return existing_tags[0]
  return await Tag.objects.acreate(name=tag_name, creator=user)


async def load_all_user_tags(user) -> list[Tag]:
  return await (sync_to_async(list)(Tag.objects.filter(creator=user)))

async def add_tags_to_link(tags: list[Tag], link: Link) -> Link:
  link_creator = await (sync_to_async(lambda: link.creator)())
  for tag in tags: 
    tag_creator = await (sync_to_async(lambda: tag.creator)())
    if tag_creator != link_creator:
      raise TagError()

  await (sync_to_async(lambda: link.tags.add(*tags))())
  return link
  
async def remove_tags_from_link(tags: list[Tag], link: Link) -> Link:
  link_creator = await (sync_to_async(lambda: link.creator)())
  for tag in tags: 
    tag_creator = await (sync_to_async(lambda: tag.creator)())
    if tag_creator != link_creator:
      raise TagError()

  await (sync_to_async(lambda: link.tags.remove(*tags))())
  return link
  
async def set_tags_on_link(tags: list[Tag], link: Link) -> Link:
  link_creator = await (sync_to_async(lambda: link.creator)())
  for tag in tags: 
    tag_creator = await (sync_to_async(lambda: tag.creator)())
    if tag_creator != link_creator:
      raise TagError()

  await (sync_to_async(lambda: link.tags.set(tags))())
  return link