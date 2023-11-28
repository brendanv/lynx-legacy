from asgiref.sync import sync_to_async
from openai import AsyncOpenAI
from lynx.models import Link, UserSetting
from lynx.errors import NoAPIKeyInSettings


async def generate_and_persist_summary(link: Link) -> Link:
  # Don't summarize if it's already summarized
  if link.summary:
    return link

  link_owner = await (sync_to_async(lambda: link.creator)())
  user_settings, _ = await UserSetting.objects.aget_or_create(user=link_owner)
  api_key = user_settings.openai_api_key

  if not api_key:
    raise NoAPIKeyInSettings()

  client = AsyncOpenAI(api_key=api_key)

  prompt_message = f"Summarize the following article:\n\n{link.raw_text_content}"

  response = await client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[{
          "role": "system",
          "content": "You are a helpful assistant."
      }, {
          "role": "user",
          "content": prompt_message
      }])

  summary = response.choices[0].message.content
  if summary:
    link.summary = summary
    await link.asave()

  return link
