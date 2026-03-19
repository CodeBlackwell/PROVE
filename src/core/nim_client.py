from openai import OpenAI

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NimClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(base_url=NIM_BASE_URL, api_key=api_key)

    def chat(self, messages: list[dict], tools=None, model: str = "nvidia/llama-3.1-nemotron-70b-instruct"):
        try:
            kwargs = {"model": model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"NIM chat error ({NIM_BASE_URL}/chat/completions): {e}") from e

    def embed(self, texts: list[str], model: str = "nvidia/nv-embedqa-e5-v5") -> list[list[float]]:
        try:
            response = self.client.embeddings.create(model=model, input=texts, encoding_format="float", extra_body={"input_type": "query"})
            return [item.embedding for item in response.data]
        except Exception as e:
            raise RuntimeError(f"NIM embed error ({NIM_BASE_URL}/embeddings): {e}") from e
