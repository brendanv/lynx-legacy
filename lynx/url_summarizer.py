from openai import AsyncOpenAI
from lynx.models import Link

async def generate_summary(link: Link) -> str | None:
  # Requires env var OPENAI_API_KEY
  client = AsyncOpenAI()

  prompt_message = f"Summarize the following article:\n\n{link.raw_text_content}"

  response = await client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_message}]
  )

  return response.choices[0].message.content