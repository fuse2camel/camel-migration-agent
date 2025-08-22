from __future__ import annotations
import json, os, time, threading, queue
import requests
from config.settings import EVENT_LOG_PATH, EVENT_HTTP_ENDPOINT
class EventLogger:
    def __init__(self, log_path: str = EVENT_LOG_PATH, http_endpoint: str | None = EVENT_HTTP_ENDPOINT):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.http_endpoint = http_endpoint
        self.q: queue.Queue = queue.Queue()
        self._t = threading.Thread(target=self._drain, daemon=True); self._t.start()
    def _drain(self):
        while True:
            evt = self.q.get()
            if evt is None: return
            try:
                with open(self.log_path, "a") as f: f.write(json.dumps(evt) + "\n")
            except Exception: pass
            if self.http_endpoint:
                try: requests.post(self.http_endpoint, json=evt, timeout=1.0)
                except Exception: pass
    def emit(self, **kwargs):
        evt = {"ts": time.time(), **kwargs}
        self.q.put(evt)
logger = EventLogger()
