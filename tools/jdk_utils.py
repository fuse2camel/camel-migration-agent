from __future__ import annotations
import os, platform, subprocess, tarfile, zipfile, tempfile, shutil, requests
from typing import Tuple, Optional

def _run(cmd: list[str]) -> Tuple[int,str,str]:
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=20)
        return p.returncode, out or "", err or ""
    except Exception as e:
        return 1, "", str(e)

def detect_java_version() -> Tuple[bool, Optional[int], str]:
    # returns (found, major, raw_output)
    rc, out, err = _run(["java", "-version"])
    txt = (out + "\n" + err).strip()
    if rc != 0: return False, None, txt
    # parse 'version "21.0.2"' or openjdk version "21.0.1"
    import re
    m = re.search(r'version\s+\"(\d+)', txt)
    major = int(m.group(1)) if m else None
    return True, major, txt

def _extract_archive(archive_path: str, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    if archive_path.endswith((".tar.gz",".tgz",".tar")):
        with tarfile.open(archive_path, "r:*") as t:
            t.extractall(dest_dir)
    elif archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(dest_dir)
    else:
        raise ValueError("Unsupported archive type (expect .tar.gz or .zip)")
    # pick first top-level dir as JAVA_HOME
    names = [n for n in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir,n))]
    if not names:
        raise RuntimeError("Archive extracted but no directory found")
    # Prefer dirs that look like jdk-21*
    preferred = [n for n in names if n.lower().startswith("jdk-21") or "21" in n]
    use = preferred[0] if preferred else names[0]
    return os.path.join(dest_dir, use)

def install_jdk_from_url(url: str, install_root: str = "./artifacts/jdk21") -> str:
    os.makedirs(install_root, exist_ok=True)
    # stream download
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1] or ".tar.gz")
    tmp.close()
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(tmp.name, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
    java_home = _extract_archive(tmp.name, install_root)
    try: os.remove(tmp.name)
    except Exception: pass
    return java_home

def install_jdk_from_local(archive_path: str, install_root: str = "./artifacts/jdk21") -> str:
    os.makedirs(install_root, exist_ok=True)
    return _extract_archive(archive_path, install_root)

def write_env_activation(java_home: str, dest_script: str = "./artifacts/activate_java.sh") -> str:
    os.makedirs(os.path.dirname(dest_script), exist_ok=True)
    with open(dest_script, "w") as f:
        f.write(f"export JAVA_HOME=\"{os.path.abspath(java_home)}\"\n")
        f.write(f"export PATH=\"$JAVA_HOME/bin:$PATH\"\n")
        f.write("echo \"JAVA_HOME set to $JAVA_HOME\"\n")
    os.chmod(dest_script, 0o755)
    return dest_script

def java_bin_version(java_home: str) -> str:
    exe = os.path.join(java_home, "bin", "java")
    rc, out, err = _run([exe, "-version"])
    return (out + "\n" + err).strip()
