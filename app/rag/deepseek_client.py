from openai import OpenAI

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


def ask(prompt: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content
