import os, subprocess, shlex, time, json
from pathlib import Path

DATA_ROOT = os.getenv("DATA_ROOT", "/data")

def job_paths(job_id: str) -> dict:
    root = Path(DATA_ROOT) / "jobs" / job_id
    return {
        "root": root,
        "uploads": root / "uploads",
        "work": root / "work",
        "outputs": root / "outputs",
        "meta": root / "meta.json",
        "log": root / "log.txt",
    }

def read_meta(job_id: str) -> dict:
    p = job_paths(job_id)["meta"]
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def write_meta(job_id: str, meta: dict) -> None:
    p = job_paths(job_id)["meta"]
    p.parent.mkdir(parents=True, exist_ok=True)
    meta = dict(meta)
    meta["updated_at"] = time.time()
    p.write_text(json.dumps(meta, indent=2), encoding="utf-8")

def append_log(job_id: str, line: str) -> None:
    p = job_paths(job_id)["log"]
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")

def run_cmd(job_id: str, cmd: str, cwd: str | None = None) -> None:
    append_log(job_id, f"$ {cmd}")
    proc = subprocess.Popen(
        shlex.split(cmd),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        append_log(job_id, line.rstrip())
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"Command failed with code {rc}: {cmd}")
