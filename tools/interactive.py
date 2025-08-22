from __future__ import annotations
import time, requests, uuid
from typing import Optional, Tuple
class InteractiveClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
    def create_prompt(self, title: str, text: str, options: list[str], default: Optional[str]=None, payload: dict | None=None) -> str:
        prompt_id = str(uuid.uuid4())
        body = {"id": prompt_id, "title": title, "text": text, "options": options, "default": default, "payload": payload or {}}
        requests.post(f"{self.base_url}/create_prompt", json=body, timeout=2.0)
        return prompt_id
    def wait_for_decision(self, prompt_id: str, timeout_sec: int = 600, poll_ms: int = 500) -> dict:
        deadline = time.time() + timeout_sec
        url = f"{self.base_url}/decision/{prompt_id}"
        while time.time() < deadline:
            try:
                r = requests.get(url, timeout=2.0)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "resolved":
                        return data
            except Exception: pass
            time.sleep(poll_ms/1000.0)
        raise TimeoutError("Timed out waiting for decision")
    def choose_branch_action(self, repo_path: str, branch_name: str) -> Tuple[str, str | None]:
        prompt_id = self.create_prompt(
            title="Branch already exists",
            text=f"The branch '{branch_name}' already exists for repository: {repo_path}. What would you like to do?",
            options=["create-new", "override", "ignore"],
            default="override",
            payload={"repo_path": repo_path, "branch": branch_name}
        )
        decision = self.wait_for_decision(prompt_id)
        choice = decision.get("choice", "override")
        new_name = decision.get("new_branch_name") if choice == "create-new" else None
        return choice, new_name


    def choose_jdk_install(self, repo_path: str) -> dict:
        prompt_id = self.create_prompt(
            title="JDK 21 Required",
            text=("Java 21 is required. Provide a Red Hat download URL (you may need to sign in at https://developers.redhat.com/products/openjdk/download) "
                  "or a local .tar.gz/.zip path. Optionally, skip if you will configure it yourself."),
            options=["provide-redhat-url","provide-local-archive","skip"],
            default="provide-redhat-url",
            payload={
                "kind": "jdk",
                "text_input_label": "Red Hat URL or local archive path",
                "show_text_input_when": ["provide-redhat-url","provide-local-archive"],
                "repo_path": repo_path
            }
        )
        decision = self.wait_for_decision(prompt_id)
        return decision
