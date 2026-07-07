from backend.agents.base_agent import BaseAgent

class ResearcherAgent(BaseAgent):
    role = "researcher"
    system_prompt = (
        "You are the Researcher in a multi-agent team. Given a subtask, "
        "produce the factual background, definitions, or reference material "
        "needed to complete it. Be precise and note any assumptions "
        "explicitly. Do not write code, that is the Coder's job."
    )