import os, json, time
from .config import settings

def job_dir(job_id: str) -> str:
    return os.path.join(settings.data_root, "jobs", job_id)

def ensure_job_dirs(job_id: str) -> dict:
    jd = job_dir(job_id)
    paths = {
        "root": jd,
        "uploads": os.path.join(jd, "uploads"),
        "work": os.path.join(jd, "work"),
        "outputs": os.path.join(jd, "outputs"),
        "meta": os.path.join(jd, "meta.json"),
        "log": os.path.join(jd, "log.txt"),
    }
    for k, p in paths.items():
        if k in ("meta","log"): 
            continue
        os.makedirs(p, exist_ok=True)
    if not os.path.exists(paths["log"]):
        with open(paths["log"], "w", encoding="utf-8") as f:
            f.write("")
    return paths

def write_meta(job_id: str, meta: dict) -> None:
    paths = ensure_job_dirs(job_id)
    meta = dict(meta)
    meta["updated_at"] = time.time()
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def read_meta(job_id: str) -> dict:
    paths = ensure_job_dirs(job_id)
    if not os.path.exists(paths["meta"]):
        return {}
    with open(paths["meta"], "r", encoding="utf-8") as f:
        return json.load(f)

def append_log(job_id: str, line: str) -> None:
    paths = ensure_job_dirs(job_id)
    with open(paths["log"], "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")
