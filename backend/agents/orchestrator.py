import json
import uuid

from backend.core import qwen_client
from backend.core.blackboard import Blackboard
from backend.agents.planner_agent import PlannerAgent
from backend.agents.researcher_agent import ResearcherAgent
from backend.agents.coder_agent import CoderAgent
from backend.agents.critic_agent import CriticAgent

DECOMPOSE_PROMPT = """You are the Orchestrator of a multi-agent team with three \
specialists available: "planner" (breaks work into steps), "researcher" \
(gathers facts/background), and "coder" (writes code).

Break the user's goal into 2-4 concrete subtasks. Return ONLY valid JSON, a \
list of objects like:
[{{"role": "planner", "task": "..."}}, {{"role": "coder", "task": "..."}}]

User goal: {goal}
"""

ARBITRATE_PROMPT = """Two agents disagree and could not converge after {rounds} \
rounds on this subtask:
{task}

Latest attempt:
{content}

Critic's standing objection:
{reason}

As Orchestrator, make the final call: either fix the attempt yourself or \
decide it is acceptable as-is, and output only the final content to use.
"""

AGENTS = {
    "planner": PlannerAgent(),
    "researcher": ResearcherAgent(),
    "coder": CoderAgent(),
}


class Orchestrator:
    def __init__(self, on_event=None):
        self.bb = Blackboard()
        self.critic = CriticAgent()
        self.on_event = on_event or (lambda event: None)

    def _emit(self, actor: str, action: str, content: str):
        self.on_event({"actor": actor, "action": action, "content": content})

    def decompose(self, goal: str) -> list[dict]:
        raw = qwen_client.chat(
            "You output only valid JSON, nothing else.",
            DECOMPOSE_PROMPT.format(goal=goal),
        )["text"]
        cleaned = raw.strip().strip("`").replace("json\n", "", 1)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return [{"role": "coder", "task": goal}]

    def run_subtask(self, entry_id: int, role: str, task: str):
        agent = AGENTS.get(role, AGENTS["coder"])
        context = ""

        while True:
            entry = self.bb.entries[entry_id]
            if entry.reject_reason:
                context = f"Previous attempt was rejected. Reason: {entry.reject_reason}"

            content = agent.run(task, extra_context=context)
            self.bb.submit(entry_id, content, author=role)
            self._emit(role, "proposed", content)

            approved, reason = self.critic.review(task, content)
            if approved:
                self.bb.approve(entry_id, critic="critic")
                self._emit("critic", "approved", content)
                return

            self.bb.reject(entry_id, reason, critic="critic")
            self._emit("critic", "rejected", reason)

            if self.bb.needs_arbitration(entry_id) or entry.rounds >= Blackboard.MAX_ROUNDS:
                final = qwen_client.chat(
                    "You are a fair, decisive arbitrator.",
                    ARBITRATE_PROMPT.format(
                        rounds=entry.rounds, task=task, content=content, reason=reason
                    ),
                )["text"]
                self.bb.arbitrate(entry_id, final, orchestrator="orchestrator")
                self._emit("orchestrator", "arbitrated", final)
                return

    def run(self, goal: str) -> dict:
        run_id = str(uuid.uuid4())[:8]
        subtasks = self.decompose(goal)
        self._emit("orchestrator", "decomposed", json.dumps(subtasks, ensure_ascii=False))

        for st in subtasks:
            entry = self.bb.post_task(st["role"], st["task"])
            self.run_subtask(entry.id, st["role"], st["task"])

        final_parts = [
            f"### {e.role} — {e.task}\n{e.content}" for e in self.bb.approved_or_arbitrated()
        ]
        final_answer = "\n\n".join(final_parts)

        return {
            "run_id": run_id,
            "final_answer": final_answer,
            "transcript": self.bb.transcript,
            "model_calls": qwen_client.get_call_count(),
        }