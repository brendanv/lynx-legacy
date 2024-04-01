from asgiref.sync import sync_to_async
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from lynx.models import Link, UserSetting
from lynx.errors import NoAPIKeyInSettings
from typing import Optional


async def generate_and_persist_summary(link: Link) -> Link:
  # Don't summarize if it's already summarized
  if link.summary:
    return link

  link_owner = await (sync_to_async(lambda: link.user)())
  user_settings, _ = await UserSetting.objects.aget_or_create(user=link_owner)

  summary = None

  model = user_settings.summarization_model
  match model:
    case UserSetting.SummarizationModel.GPT35TURBO | \
        UserSetting.SummarizationModel.GPT35TURBO0125 | \
        UserSetting.SummarizationModel.GPT4 | \
        UserSetting.SummarizationModel.GPT4TURBO:
      api_key = user_settings.openai_api_key
      if not api_key:
        raise NoAPIKeyInSettings()
      summary = await summarize_openai(link, api_key, model)

    case UserSetting.SummarizationModel.CLAUDE3HAIKU | \
        UserSetting.SummarizationModel.CLAUDE3SONNET | \
        UserSetting.SummarizationModel.CLAUDE3OPUS:
      api_key = user_settings.anthropic_api_key
      if not api_key:
        raise NoAPIKeyInSettings()
      summary = await summarize_anthropic(link, api_key, model)

    case _:
      raise ValueError(f"Unknown summarization model: {model}")

  if summary:
    link.summary = summary
    await link.asave()

  return link


async def summarize_openai(link: Link, api_key: str,
                           model: str) -> Optional[str]:
  client = AsyncOpenAI(api_key=api_key)

  prompt_message = f"Summarize the following article:\n\n{link.raw_text_content}"

  response = await client.chat.completions.create(
      model=model,
      messages=[{
          "role": "system",
          "content": "You are a helpful assistant."
      }, {
          "role": "user",
          "content": prompt_message
      }])

  return response.choices[0].message.content


async def summarize_anthropic(link: Link, api_key: str,
                              model_name: str) -> Optional[str]:
  client = AsyncAnthropic(api_key=api_key)
  prompt_message = f"Summarize the following article:\n\n{link.raw_text_content}"
  response = await client.messages.create(
      max_tokens=1024,
      system="You are a helpful assistant.",
      messages=[{
          "role": "user",
          "content": prompt_message
      }],
      model=model_name)
  return response.content[0].text
