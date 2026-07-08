import time

from backend.agents.orchestrator import Orchestrator
from backend.core import qwen_client

TASKS = [
    {
        "goal": "Write a Python function that validates an email address and "
                "include unit tests for it.",
        "must_contain": ["def ", "test", "@"],
    },
    {
        "goal": "Explain what a rate limiter is and provide a simple token "
                "bucket implementation in Python.",
        "must_contain": ["token", "def ", "rate"],
    },
    {
        "goal": "Plan and implement a function that deduplicates a list of "
                "dictionaries by a given key, with a short explanation of "
                "the approach.",
        "must_contain": ["def ", "key", "dedup"],
    },
]

def completion_score(text: str, must_contain: list[str]) -> float:
    text_lower = text.lower()
    hits = sum(1 for kw in must_contain if kw.lower() in text_lower)
    return hits / len(must_contain)


def run_single_agent(goal: str) -> dict:
    qwen_client.reset_call_count()
    start = time.time()
    result = qwen_client.chat(
        "You are a helpful assistant. Answer the request directly and completely.",
        goal,
    )
    return {
        "text": result["text"],
        "time_s": time.time() - start,
        "calls": qwen_client.get_call_count(),
    }


def run_society(goal: str) -> dict:
    qwen_client.reset_call_count()
    start = time.time()
    orchestrator = Orchestrator()
    result = orchestrator.run(goal)
    return {
        "text": result["final_answer"],
        "time_s": time.time() - start,
        "calls": result["model_calls"],
    }

def main():
    rows = []
    for t in TASKS:
        single = run_single_agent(t["goal"])
        society = run_society(t["goal"])

        rows.append({
            "task": t["goal"][:50] + "...",
            "single_time": round(single["time_s"], 2),
            "single_calls": single["calls"],
            "single_score": round(completion_score(single["text"], t["must_contain"]), 2),
            "society_time": round(society["time_s"], 2),
            "society_calls": society["calls"],
            "society_score": round(completion_score(society["text"], t["must_contain"]), 2),
        })

    header = (
        f"{'task':52} | {'1-agent t(s)':12} | {'1-agent calls':13} | {'1-agent score':13} | "
        f"{'society t(s)':12} | {'society calls':13} | {'society score':13}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['task']:52} | {r['single_time']:<12} | {r['single_calls']:<13} | "
            f"{r['single_score']:<13} | {r['society_time']:<12} | {r['society_calls']:<13} | "
            f"{r['society_score']:<13}"
        )

    avg_single_score = sum(r["single_score"] for r in rows) / len(rows)
    avg_society_score = sum(r["society_score"] for r in rows) / len(rows)
    print(f"\nAverage completion score — single agent: {avg_single_score:.2f} | "
          f"society: {avg_society_score:.2f}")


if __name__ == "__main__":
    main()