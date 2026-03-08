import os
from pathlib import Path
from .celery_worker import celery_app
from .util import job_paths, read_meta, write_meta, append_log, run_cmd

def _set(job_id: str, **kwargs):
    meta = read_meta(job_id)
    meta.update(kwargs)
    write_meta(job_id, meta)

def _extra(env_name: str) -> str:
    val = os.getenv(env_name, "")
    return val.strip()

@celery_app.task(name="worker.tasks.run_reconstruction", bind=True)
def run_reconstruction(self, job_id: str):
    paths = job_paths(job_id)
    paths["outputs"].mkdir(parents=True, exist_ok=True)
    paths["work"].mkdir(parents=True, exist_ok=True)

    meta = read_meta(job_id)
    model = meta.get("model", "splatfacto")
    upload_name = meta.get("upload")
    if not upload_name:
        _set(job_id, state="FAILED", message="No upload found", progress=0.0)
        return

    video_path = paths["uploads"] / upload_name
    if not video_path.exists():
        _set(job_id, state="FAILED", message="Uploaded video missing", progress=0.0)
        return

    # Optional steps
    export_pointcloud = os.getenv("EXPORT_POINTCLOUD", "1") == "1"
    export_tsdf = os.getenv("EXPORT_TSDF", "1") == "1"
    export_poisson = os.getenv("EXPORT_POISSON", "0") == "1"
    render_interpolate = os.getenv("RENDER_INTERPOLATE", "1") == "1"
    render_spiral = os.getenv("RENDER_SPIRAL", "1") == "1"

    train_extra = _extra("NS_TRAIN_EXTRA_ARGS")
    interp_extra = _extra("NS_RENDER_INTERPOLATE_EXTRA_ARGS")
    spiral_extra = _extra("NS_RENDER_SPIRAL_EXTRA_ARGS")

    try:
        _set(job_id, state="STARTED", message="Processing data (frames + poses)", progress=0.05)

        processed = paths["work"] / "ns_data"
        processed.mkdir(parents=True, exist_ok=True)

        # 1) Process video into nerfstudio dataset format.
        # Docs show: ns-process-data {video,images,...} --data <path> --output-dir <dir>
        run_cmd(job_id, f"ns-process-data video --data {video_path} --output-dir {processed}")

        _set(job_id, state="STARTED", message=f"Training model: {model}", progress=0.25)

        # 2) Train (minimal command per docs: ns-train <method> --data <data>)
        # Extra args can be provided via NS_TRAIN_EXTRA_ARGS.
        cmd = f"ns-train {model} --data {processed}"
        if train_extra:
            cmd += f" {train_extra}"
        run_cmd(job_id, cmd)

        # Find the latest config.yml produced by nerfstudio
        config = None
        for p in sorted(paths['work'].rglob('config.yml'), key=lambda x: x.stat().st_mtime, reverse=True):
            config = p
            break
        if config is None:
            raise RuntimeError("Could not find config.yml after training")

        _set(job_id, state="STARTED", message="Rendering videos", progress=0.70)

        renders_dir = paths["outputs"] / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)

        if render_interpolate:
            cmd = f"ns-render interpolate --load-config {config} --output-path {renders_dir / 'interpolate.mp4'}"
            if interp_extra:
                cmd += f" {interp_extra}"
            run_cmd(job_id, cmd)

        if render_spiral:
            cmd = f"ns-render spiral --load-config {config} --output-path {renders_dir / 'spiral.mp4'}"
            if spiral_extra:
                cmd += f" {spiral_extra}"
            run_cmd(job_id, cmd)

        _set(job_id, state="STARTED", message="Exporting geometry", progress=0.85)

        exports_dir = paths["outputs"] / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        if export_pointcloud:
            run_cmd(job_id, f"ns-export pointcloud --load-config {config} --output-dir {exports_dir}")

        if export_tsdf:
            # Docs show: ns-export tsdf --load-config CONFIG.yml --output-dir OUTPUT_DIR
            run_cmd(job_id, f"ns-export tsdf --load-config {config} --output-dir {exports_dir}")

        if export_poisson:
            # Docs note poisson requires predicted normals (often via nerfacto with predict-normals).
            run_cmd(job_id, f"ns-export poisson --load-config {config} --output-dir {exports_dir}")

        _set(job_id, state="SUCCESS", message="Done", progress=1.0)

    except Exception as e:
        append_log(job_id, f"ERROR: {e}")
        _set(job_id, state="FAILED", message=str(e), progress=float(read_meta(job_id).get("progress", 0.0)))
        raise
