import time
import anthropic


class HaikuClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def classify(self, system: str, user: str) -> str:
        for attempt in range(10):
            try:
                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return response.content[0].text
            except anthropic.RateLimitError as e:
                wait = min(2 ** attempt * 5, 120)
                print(f"  Rate limited (attempt {attempt + 1}/10), waiting {wait}s...")
                time.sleep(wait)
                if attempt == 9:
                    raise
