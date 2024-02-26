from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import AsyncMock, Mock, mock_open, patch
from lynx.models import Link, Tag
from lynx.url_summarizer import generate_and_persist_summary
from lynx.errors import TagError
from lynx.tag_manager import delete_tag_for_user, create_tag_for_user, add_tags_to_link, remove_tags_from_link, set_tags_on_link
from django.utils import timezone
from django.http.response import Http404

class TagsTestCase(TestCase):
  
  async def get_default_test_user(self) -> User:
    user, _= await User.objects.aget_or_create(username='default_user')
    return user
    
  async def create_test_link(self, **kwargs) -> Link:
    """
    Helper method to create a Link with default fields.
    Fields can be overridden by passing them as keyword arguments.
    """
    default_user = await self.get_default_test_user()
    defaults = {
        'summary': '',
        'raw_text_content': 'Some content',
        'article_date': timezone.now(),
        'read_time_seconds': 12,
        'user': default_user,
    }
    defaults.update(kwargs)
    link = Link(**defaults)
    await link.asave()
    return link

  async def test_delete_tag_not_allowed_for_other_users(self):
    user, _= await User.objects.aget_or_create(username='user1')
    user2, _= await User.objects.aget_or_create(username='user2')
    self.assertNotEqual(user.pk, user2.pk)

    tag, _ = await Tag.objects.aget_or_create(name='tag1', user=user)
    with self.assertRaises(Http404):
      await delete_tag_for_user(user2, tag.pk)

    # But the original user should be able to delete
    await delete_tag_for_user(user, tag.pk)
    existing_tags = await (sync_to_async(list)(Tag.objects.filter(pk=tag.pk)))
    self.assertEqual(len(existing_tags), 0)

  async def test_create_tag_for_user_deduplicates(self):
    '''
    Test that create_tag_for_user returns existing tags if there's a match
    '''
    user, _= await User.objects.aget_or_create(username='user1')
    tag = await create_tag_for_user(user, 'tag1')
    retry = await create_tag_for_user(user, 'tag1')
    self.assertEqual(tag, retry)
    self.assertEqual(tag.user, user)
    self.assertEqual(tag.name, 'tag1')
    self.assertIsNotNone(tag.slug)

    # But deduplication should not be cross-user
    user2, _= await User.objects.aget_or_create(username='user2')
    self.assertNotEqual(user.pk, user2.pk)
    user2_tag = await create_tag_for_user(user2, 'tag1')
    self.assertNotEqual(tag, user2_tag)
    self.assertEqual(user2_tag.user, user2)
    self.assertEqual(user2_tag.name, 'tag1')
    self.assertIsNotNone(user2_tag.slug)

  async def test_add_tags_to_link_adds_tags(self):
    user, _= await User.objects.aget_or_create(username='user1')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    link = await self.create_test_link(user=user)
    self.assertEqual(tag1.user, link.user)
    self.assertEqual(tag2.user, link.user)
    self.assertEqual(link.user, user)

    link = await add_tags_to_link([tag1, tag2], link)
    link_tags = await (sync_to_async(list)(link.tags.all()))
    self.assertEqual(2, len(link_tags))
    self.assertEqual(tag1, link_tags[0])
    self.assertEqual(tag2, link_tags[1])
   
  async def test_add_tags_to_link_checks_user(self):
    user, _= await User.objects.aget_or_create(username='user1')
    user2, _= await User.objects.aget_or_create(username='user2')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    link = await self.create_test_link(user=user2)
    self.assertEqual(tag1.user, user)
    self.assertEqual(tag2.user, user)
    self.assertEqual(link.user, user2)

    with self.assertRaises(TagError):
      await add_tags_to_link([tag1, tag2], link)
    
  async def test_remove_tags_from_link_removes_tags(self):
    user, _= await User.objects.aget_or_create(username='user1')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    tag3 = await create_tag_for_user(user, 'tag3')
    link = await self.create_test_link(user=user)
    self.assertEqual(tag1.user, link.user)
    self.assertEqual(tag2.user, link.user)
    self.assertEqual(tag3.user, link.user)
    self.assertEqual(link.user, user)
    link = await add_tags_to_link([tag1, tag2, tag3], link)

    link = await remove_tags_from_link([tag1, tag2], link)
    link_tags = await (sync_to_async(list)(link.tags.all()))
    self.assertEqual(1, len(link_tags))
    self.assertEqual(tag3, link_tags[0])
    
  async def test_remove_tags_from_link_checks_user(self):
    user, _= await User.objects.aget_or_create(username='user1')
    user2, _= await User.objects.aget_or_create(username='user2')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    tag3 = await create_tag_for_user(user2, 'tag3')
    link = await self.create_test_link(user=user)
    self.assertEqual(tag1.user, link.user)
    self.assertEqual(tag2.user, link.user)
    self.assertEqual(tag3.user, user2)
    self.assertEqual(link.user, user)
    link = await add_tags_to_link([tag1, tag2], link)

    with self.assertRaises(TagError):
      await remove_tags_from_link([tag3], link)
      
  async def test_set_tags_on_link_sets_tags(self):
    user, _= await User.objects.aget_or_create(username='user1')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    tag3 = await create_tag_for_user(user, 'tag3')
    link = await self.create_test_link(user=user)
    self.assertEqual(tag1.user, link.user)
    self.assertEqual(tag2.user, link.user)
    self.assertEqual(tag3.user, link.user)
    self.assertEqual(link.user, user)
    
    link = await set_tags_on_link([tag1, tag2], link)
    link_tags = await (sync_to_async(list)(link.tags.all()))
    self.assertEqual(2, len(link_tags))
    self.assertEqual(tag1, link_tags[0])
    self.assertEqual(tag2, link_tags[1])
    
    link = await set_tags_on_link([tag3], link)
    link_tags = await (sync_to_async(list)(link.tags.all()))
    self.assertEqual(1, len(link_tags))
    self.assertEqual(tag3, link_tags[0])
    
    link = await set_tags_on_link([], link)
    link_tags = await (sync_to_async(list)(link.tags.all()))
    self.assertEqual(0, len(link_tags))
    
  async def test_set_tags_on_link_checks_user(self):
    user, _= await User.objects.aget_or_create(username='user1')
    user2, _= await User.objects.aget_or_create(username='user2')
    tag1 = await create_tag_for_user(user, 'tag1')
    tag2 = await create_tag_for_user(user, 'tag2')
    tag3 = await create_tag_for_user(user2, 'tag3')
    link = await self.create_test_link(user=user)
    self.assertEqual(tag1.user, link.user)
    self.assertEqual(tag2.user, link.user)
    self.assertEqual(tag3.user, user2)
    self.assertEqual(link.user, user)

    with self.assertRaises(TagError):
      await set_tags_on_link([tag1, tag2, tag3], link)