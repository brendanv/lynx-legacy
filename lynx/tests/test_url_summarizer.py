from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import AsyncMock, Mock, mock_open, patch, ANY
from lynx.models import Link, UserSetting
from lynx.url_summarizer import generate_and_persist_summary
from lynx.errors import NoAPIKeyInSettings
from django.utils import timezone

async def get_default_test_user() -> User:
  user, _ = await User.objects.aget_or_create(username='default_user')
  return user

async def set_usersettings_value(user: User, **kwargs) -> UserSetting:
  user_setting, _ = await UserSetting.objects.aupdate_or_create(
      user=user, defaults=kwargs)
  return user_setting

async def create_test_link(**kwargs) -> Link:
  """
      Helper method to create a Link with default fields.
      Fields can be overridden by passing them as keyword arguments.
      """
  default_user = await get_default_test_user()
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

class OpenAIUrlSummarizerTest(TestCase):

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_skip_summarization_with_existing_summary(self, mock_openai):
    # Ensure the user has a valid API key so that's not the reason we skip summarization
    user = await get_default_test_user()
    await set_usersettings_value(user, openai_api_key='foo')
    link = await create_test_link(summary='Preexisting summary')
    await generate_and_persist_summary(link)

    await sync_to_async(link.refresh_from_db)()

    self.assertEqual(link.summary, 'Preexisting summary')
    mock_openai.assert_not_called()

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_generate_and_persist_summary_with_api_key(self, mock_openai):
    user = await get_default_test_user()
    await set_usersettings_value(user, openai_api_key='foo')

    link = await create_test_link(summary='', user=user)

    # Configure the mock OpenAI client to return a sample summary
    mock_openai.return_value.chat.completions.create = AsyncMock(
        return_value=AsyncMock(choices=[
            AsyncMock(message=AsyncMock(content='Generated summary'))
        ]))

    summarized_link = await generate_and_persist_summary(link)

    mock_openai.assert_called_once_with(api_key='foo')
    self.assertEqual(summarized_link.summary, 'Generated summary')

  async def test_raise_if_no_api_key_in_settings(self):
    user = await get_default_test_user()
    await set_usersettings_value(user, openai_api_key='')
    link = await create_test_link(summary='', user=user)

    with self.assertRaises(NoAPIKeyInSettings):
      await generate_and_persist_summary(link)

  @patch('lynx.url_summarizer.AsyncOpenAI')
  async def test_pass_summarization_model_to_openai_api(self, mock_openai):
    user = await get_default_test_user()
    summarization_model = 'gpt-4'
    await set_usersettings_value(user,
                                      openai_api_key='foo',
                                      summarization_model=summarization_model)

    link = await create_test_link(summary='', user=user)

    mock_openai.return_value.chat.completions.create = AsyncMock(
        return_value=AsyncMock(choices=[
            AsyncMock(message=AsyncMock(content='Generated summary'))
        ]))

    await generate_and_persist_summary(link)

    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=summarization_model, messages=ANY)


class AnthropicUrlSummarizerTest(TestCase):

  @patch('lynx.url_summarizer.AsyncAnthropic')
  async def test_skip_summarization_with_existing_summary(self, mock_anthropic):
    # Ensure the user has a valid API key so that's not the reason we skip summarization
    user = await get_default_test_user()
    await set_usersettings_value(user, anthropic_api_key='foo', summarization_model='claude-3-haiku-20240307')
    link = await create_test_link(summary='Preexisting summary')
    await generate_and_persist_summary(link)

    await sync_to_async(link.refresh_from_db)()

    self.assertEqual(link.summary, 'Preexisting summary')
    mock_anthropic.assert_not_called()

  @patch('lynx.url_summarizer.AsyncAnthropic')
  async def test_generate_and_persist_summary_with_api_key(self, mock_anthropic):
    user = await get_default_test_user()
    await set_usersettings_value(user, anthropic_api_key='foo', summarization_model='claude-3-haiku-20240307')

    link = await create_test_link(summary='', user=user)

    # Configure the mock Anthropic client to return a sample summary
    mock_anthropic.return_value.messages.create = AsyncMock(
        return_value=AsyncMock(content=[
            AsyncMock(text='Generated summary')
        ]))

    summarized_link = await generate_and_persist_summary(link)

    mock_anthropic.assert_called_once_with(api_key='foo')
    self.assertEqual(summarized_link.summary, 'Generated summary')

  async def test_raise_if_no_api_key_in_settings(self):
    user = await get_default_test_user()
    await set_usersettings_value(user, anthropic_api_key='', summarization_model='claude-3-haiku-20240307')
    link = await create_test_link(summary='', user=user)

    with self.assertRaises(NoAPIKeyInSettings):
      await generate_and_persist_summary(link)

  @patch('lynx.url_summarizer.AsyncAnthropic')
  async def test_pass_summarization_model_to_anthropic(self, mock_anthropic):
    user = await get_default_test_user()
    summarization_model = 'claude-3-haiku-20240307'
    await set_usersettings_value(user, anthropic_api_key='foo', summarization_model=summarization_model)

    link = await create_test_link(summary='', user=user)

    mock_anthropic.return_value.messages.create = AsyncMock(
        return_value=AsyncMock(content=[
            AsyncMock(text='Generated summary')
        ]))

    await generate_and_persist_summary(link)

    mock_anthropic.return_value.messages.create.assert_called_once_with(
        model=summarization_model, messages=ANY, max_tokens=1024, system=ANY)