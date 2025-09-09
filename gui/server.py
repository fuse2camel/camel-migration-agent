from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import asyncio, json, time, os
app = FastAPI(title="Coordinator Dashboard")
EVENTS = []; SUBS = set(); PROMPTS = {}; DECISIONS = {}
@app.post("/event")
async def event(e: dict):
    e["server_ts"] = time.time(); EVENTS.append(e)
    dead = []
    for q in list(SUBS):
        try: await q.put(e)
        except Exception: dead.append(q)
    for q in dead: SUBS.discard(q)
    return {"ok": True}
@app.get("/events")
async def events(): return JSONResponse(EVENTS[-500:])
@app.get("/sse")
async def sse():
    q = asyncio.Queue(); SUBS.add(q)
    async def gen():
        try:
            for e in EVENTS[-50:]: yield f"data: {json.dumps(e)}\n\n"
            while True:
                e = await q.get(); yield f"data: {json.dumps(e)}\n\n"
        finally: SUBS.discard(q)
    return StreamingResponse(gen(), media_type="text/event-stream")
@app.post("/create_prompt")
async def create_prompt(payload: dict = Body(...)):
    pid = payload.get("id"); PROMPTS[pid] = payload
    evt = {"ts": time.time(), "type": "prompt", "prompt": payload, "phase": "ui", "status": "prompt"}
    EVENTS.append(evt)
    dead = []
    for q in list(SUBS):
        try: await q.put(evt)
        except Exception: dead.append(q)
    for q in dead: SUBS.discard(q)
    return {"ok": True, "id": pid}
@app.post("/decision/{pid}")
async def post_decision(pid: str, payload: dict = Body(...)):
    DECISIONS[pid] = {"status":"resolved", **payload}
    evt = {"ts": time.time(), "type": "decision", "id": pid, **payload}
    EVENTS.append(evt)
    dead = []
    for q in list(SUBS):
        try: await q.put(evt)
        except Exception: dead.append(q)
    for q in dead: SUBS.discard(q)
    return {"ok": True}
@app.get("/decision/{pid}")
async def get_decision(pid: str):
    if pid in DECISIONS: return DECISIONS[pid]
    return {"status":"pending"}
@app.get("/flow")
async def get_flow():
    try:
        with open("config/flow.json") as f:
            data = json.load(f)
        return {"phases": data.get("phases", [])}
    except Exception:
        return {"phases": ["coordinator","git_agent","reporter"]}
@app.get("/settings")
async def get_settings():
    path = "artifacts/gui_settings.json"
    if os.path.exists(path):
        try:
            with open(path) as f: return json.load(f)
        except Exception: pass
    return {"demo_yellow_secs": 0}
@app.post("/settings")
async def post_settings(payload: dict = Body(...)):
    os.makedirs("artifacts", exist_ok=True)
    path = "artifacts/gui_settings.json"
    with open(path, "w") as f:
        json.dump(payload, f)
    evt = {"ts": time.time(), "type": "settings", **payload}
    EVENTS.append(evt)
    dead = []
    for q in list(SUBS):
        try: await q.put(evt)
        except Exception: dead.append(q)
    for q in dead: SUBS.discard(q)
    return {"ok": True}
app.mount("/", StaticFiles(directory="gui/web", html=True), name="web")
