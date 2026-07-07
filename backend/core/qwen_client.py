import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
QWEN_BASE_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")

_client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL, timeout=60.0, max_retries=1)

call_count = 0

def chat(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> dict:
    global call_count
    if not QWEN_API_KEY:
        raise RuntimeError(
            "QWEN_API_KEY is empty. Check that .env exists (cp .env.example .env), "
            "that it's in the directory you run python from, and that QWEN_API_KEY "
            "is filled in with your real Qwen Cloud key."
        )
    call_count += 1
    start = time.time()
    print(f"  [qwen call #{call_count}] sending request (model={QWEN_MODEL})...", flush=True)

    response = _client.chat.completions.create(
        model=QWEN_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    latency = time.time() - start
    print(f"  [qwen call #{call_count}] done in {latency:.1f}s", flush=True)
    text = response.choices[0].message.content
    return {"text": text, "latency_s": latency}


def reset_call_count():
    global call_count
    call_count = 0


def get_call_count() -> int:
    return call_count