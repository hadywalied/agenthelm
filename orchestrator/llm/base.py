class LLMClient(object):
    def __init__(self, model_name: str, base_url: str, api_key: str):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def predict(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")
