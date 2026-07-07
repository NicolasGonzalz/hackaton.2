from backend.core import qwen_client

class BaseAgent:
    role: str = "base"
    system_prompt: str = "You are a helpful agent."

    def run(self, task: str, extra_context: str = "") -> str:
        user_prompt = task if not extra_context else f"{task}\n\nContext:\n{extra_context}"
        result = qwen_client.chat(self.system_prompt, user_prompt)
        return result["text"]