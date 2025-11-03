import requests
from orchestrator.llm.base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(
        self, model_name: str, api_key: str, base_url: str = "https://api.openai.com/v1"
    ):
        super().__init__(model_name, base_url, api_key)

    def predict(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 1000,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
