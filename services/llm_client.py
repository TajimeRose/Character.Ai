import requests
from config import Config

def chat_complete(messages, temperature=0.7, max_tokens=600):
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        timeout=30
    )
    data = resp.json()
    return data["choices"][0]["message"]["content"]
