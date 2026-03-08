import os, uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional

from .config import settings
from .celery_app import celery
from .models import JobCreateResponse, JobStatus, ModelName
from .storage import ensure_job_dirs, read_meta, write_meta, job_dir

app = FastAPI(title="Nerf Recon API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _list_outputs(job_id: str):
    out_dir = os.path.join(job_dir(job_id), "outputs")
    if not os.path.isdir(out_dir):
        return []
    files = []
    for root, _, names in os.walk(out_dir):
        for n in names:
            rel = os.path.relpath(os.path.join(root, n), out_dir)
            files.append(rel)
    return sorted(files)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/jobs", response_model=JobCreateResponse)
async def create_job(
    video: UploadFile = File(...),
    model: ModelName = Form("splatfacto"),
):
    # basic upload limit (content-length is not always present, so we also enforce after save)
    job_id = uuid.uuid4().hex
    paths = ensure_job_dirs(job_id)

    filename = video.filename or "upload.mp4"
    safe_name = "".join([c for c in filename if c.isalnum() or c in "._-"]).strip(".")
    if not safe_name:
        safe_name = "upload.mp4"

    upload_path = os.path.join(paths["uploads"], safe_name)
    size = 0
    with open(upload_path, "wb") as f:
        while True:
            chunk = await video.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)

    write_meta(job_id, {"model": model, "upload": safe_name})

    task = celery.send_task("worker.tasks.run_reconstruction", args=[job_id])
    return JobCreateResponse(job_id=job_id, celery_task_id=task.id)

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    meta = read_meta(job_id)
    # Celery task id isn't stored reliably without broker introspection; return coarse state from meta.
    state = meta.get("state", "PENDING")
    progress = float(meta.get("progress", 0.0))
    message = meta.get("message", "")
    model = meta.get("model")
    outputs = _list_outputs(job_id)
    return JobStatus(job_id=job_id, state=state, progress=progress, message=message, model=model, outputs=outputs, meta=meta)

@app.get("/api/jobs/{job_id}/download")
def download_output(job_id: str, path: str):
    out_dir = os.path.join(job_dir(job_id), "outputs")
    full = os.path.normpath(os.path.join(out_dir, path))
    if not full.startswith(os.path.abspath(out_dir)):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(full, filename=os.path.basename(full))

@app.get("/api/jobs/{job_id}/log")
def read_log(job_id: str):
    log_path = os.path.join(job_dir(job_id), "log.txt")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(log_path, filename="log.txt")
