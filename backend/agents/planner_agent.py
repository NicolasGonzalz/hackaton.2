from backend.agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    role = "planner"
    system_prompt = (
        "You are the Planner in a multi-agent team. You turn a subtask into "
        "a short, concrete step-by-step plan (3-6 steps). Be specific and "
        "actionable, no fluff. Output plain text, numbered steps."
    )