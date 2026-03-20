import time
from openai import OpenAI, RateLimitError

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
EMBED_DIMENSIONS = 1024


class NimClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(base_url=NIM_BASE_URL, api_key=api_key)

    def chat(self, messages: list[dict], tools=None, model: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5"):
        try:
            kwargs = {"model": model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"NIM chat error ({NIM_BASE_URL}/chat/completions): {e}") from e

    def embed(self, texts: list[str], input_type: str = "passage", model: str = "nvidia/llama-3.2-nv-embedqa-1b-v2") -> list[list[float]]:
        for attempt in range(10):
            try:
                response = self.client.embeddings.create(
                    model=model, input=texts, encoding_format="float",
                    dimensions=EMBED_DIMENSIONS,
                    extra_body={"input_type": input_type, "truncate": "END"},
                )
                return [item.embedding for item in response.data]
            except RateLimitError:
                wait = min(2 ** attempt * 5, 120)
                print(f"  NIM rate limited (attempt {attempt + 1}/10), waiting {wait}s...")
                time.sleep(wait)
                if attempt == 9:
                    raise
            except Exception as e:
                raise RuntimeError(f"NIM embed error ({NIM_BASE_URL}/embeddings): {e}") from e
