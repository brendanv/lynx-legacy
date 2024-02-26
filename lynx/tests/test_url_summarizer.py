from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import AsyncMock, Mock, mock_open, patch, ANY
from lynx.models import Link, UserSetting
from lynx.url_summarizer import generate_and_persist_summary
from lynx.errors import NoAPIKeyInSettings
from django.utils import timezone


class UrlSummarizerTest(TestCase):

  async def get_default_test_user(self) -> User:
    user, _ = await User.objects.aget_or_create(username='default_user')
    return user

  async def set_usersettings_value(self, user: User, **kwargs) -> UserSetting:
    user_setting, _ = await UserSetting.objects.aupdate_or_create(
        user=user, defaults=kwargs)
    return user_setting

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

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_skip_summarization_with_existing_summary(self, mock_openai):
    # Ensure the user has a valid API key so that's not the reason we skip summarization
    user = await self.get_default_test_user()
    await self.set_usersettings_value(user, openai_api_key='foo')
    link = await self.create_test_link(summary='Preexisting summary')
    await generate_and_persist_summary(link)

    await sync_to_async(link.refresh_from_db)()

    self.assertEqual(link.summary, 'Preexisting summary')
    mock_openai.assert_not_called()

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_generate_and_persist_summary_with_api_key(self, mock_openai):
    user = await self.get_default_test_user()
    await self.set_usersettings_value(user, openai_api_key='foo')

    link = await self.create_test_link(summary='', user=user)

    # Configure the mock OpenAI client to return a sample summary
    mock_openai.return_value.chat.completions.create = AsyncMock(
        return_value=AsyncMock(choices=[
            AsyncMock(message=AsyncMock(content='Generated summary'))
        ]))

    summarized_link = await generate_and_persist_summary(link)

    mock_openai.assert_called_once_with(api_key='foo')
    self.assertEqual(summarized_link.summary, 'Generated summary')

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_raise_if_no_api_key_in_settings(self, mock_openai):
    user = await self.get_default_test_user()
    await self.set_usersettings_value(user, openai_api_key='')
    link = await self.create_test_link(summary='', user=user)

    with self.assertRaises(NoAPIKeyInSettings):
      await generate_and_persist_summary(link)

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_pass_summarization_model_to_openai_api(self, mock_openai):
    user = await self.get_default_test_user()
    summarization_model = 'gpt-4'
    await self.set_usersettings_value(user,
                                      openai_api_key='foo',
                                      summarization_model=summarization_model)

    link = await self.create_test_link(summary='', user=user)

    mock_openai.return_value.chat.completions.create = AsyncMock(
        return_value=AsyncMock(choices=[
            AsyncMock(message=AsyncMock(content='Generated summary'))
        ]))

    await generate_and_persist_summary(link)

    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=summarization_model, messages=ANY)
