import os
from dotenv import load_dotenv
load_dotenv()
EVENT_LOG_PATH = os.environ.get("EVENT_LOG_PATH", "./artifacts/events.jsonl")
EVENT_HTTP_ENDPOINT = os.environ.get("EVENT_HTTP_ENDPOINT", "http://127.0.0.1:8000/event")
DEFAULT_BRANCH_NAME = os.environ.get("DEFAULT_BRANCH_NAME", "feature/fuse2camel")
