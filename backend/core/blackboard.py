from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import itertools

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARBITRATED = "arbitrated"

@dataclass
class Entry:
    id: int
    role: str
    task: str
    content: str = ""
    status: Status = Status.PENDING
    rounds: int = 0
    reject_reason: Optional[str] = None
    history: list = field(default_factory=list)

class Blackboard:
    MAX_ROUNDS = 3

    def __init__(self):
        self._ids = itertools.count(1)
        self.entries: dict[int, Entry] = {}
        self.transcript: list[dict] = []

    def post_task(self, role: str, task: str) -> Entry:
        entry = Entry(id=next(self._ids), role=role, task=task)
        self.entries[entry.id] = entry
        self._log("orchestrator", f"assigned to {role}", task)
        return entry

    def submit(self, entry_id: int, content: str, author: str):
        entry = self.entries[entry_id]
        entry.content = content
        entry.rounds += 1
        entry.history.append({"round": entry.rounds, "author": author, "content": content})
        self._log(author, "submitted", content)

    def approve(self, entry_id: int, critic: str):
        entry = self.entries[entry_id]
        entry.status = Status.APPROVED
        self._log(critic, "approved", entry.content)

    def reject(self, entry_id: int, reason: str, critic: str):
        entry = self.entries[entry_id]
        entry.status = Status.REJECTED
        entry.reject_reason = reason
        self._log(critic, "rejected", reason)

    def needs_arbitration(self, entry_id: int) -> bool:
        entry = self.entries[entry_id]
        return entry.status == Status.REJECTED and entry.rounds >= 2

    def arbitrate(self, entry_id: int, final_content: str, orchestrator: str):
        entry = self.entries[entry_id]
        entry.content = final_content
        entry.status = Status.ARBITRATED
        self._log(orchestrator, "arbitrated", final_content)

    def approved_or_arbitrated(self) -> list[Entry]:
        return [
            e for e in self.entries.values()
            if e.status in (Status.APPROVED, Status.ARBITRATED)
        ]

    def _log(self, actor: str, action: str, content: str):
        self.transcript.append({"actor": actor, "action": action, "content": content})