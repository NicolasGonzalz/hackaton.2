import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.orchestrator import Orchestrator
from backend.core import qwen_client
from backend.core import alibaba_storage

app = FastAPI(title="Agent Society")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    goal: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
async def run(req: RunRequest):
    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def on_event(event: dict):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        qwen_client.reset_call_count()
        orchestrator = Orchestrator(on_event=on_event)

        async def do_run():
            result = await asyncio.to_thread(orchestrator.run, req.goal)
            await queue.put({"actor": "system", "action": "done", "content": json.dumps(result)})

        task = asyncio.create_task(do_run())

        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("action") == "done":
                break

        await task

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/upload/{run_id}")
def upload(run_id: str, final_answer: str, transcript: list[dict]):
    key = alibaba_storage.upload_run_artifact(run_id, transcript, final_answer)
    return {"oss_key": key}