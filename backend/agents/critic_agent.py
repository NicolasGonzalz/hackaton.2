from backend.agents.base_agent import BaseAgent

class CriticAgent(BaseAgent):
    role = "critic"
    system_prompt = (
        "You are the Critic in a multi-agent team. You review another "
        "agent's output against the subtask it was meant to solve. "
        "Respond with exactly one line starting with 'APPROVE' or "
        "'REJECT: <short concrete reason>'. Be strict: REJECT if the output "
        "is incomplete, incorrect, or ignores part of the subtask. Only "
        "APPROVE work that genuinely satisfies the subtask."
    )

    def review(self, task: str, content: str) -> tuple[bool, str]:
        prompt = f"Subtask:\n{task}\n\nOutput to review:\n{content}"
        verdict = self.run(prompt)
        verdict = verdict.strip()
        if verdict.upper().startswith("APPROVE"):
            return True, ""
        reason = verdict.split(":", 1)[1].strip() if ":" in verdict else verdict
        return False, reason