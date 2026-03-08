# Nerf Recon Web (Upload video → reconstruct → export marketing outputs)

This repository provides a local web app for:
- uploading a walkthrough video,
- choosing a reconstruction method (e.g. `nerfacto`, `splatfacto`),
- running an end-to-end pipeline (data processing → training → renders/exports),
- downloading multiple output options (videos, point cloud, mesh).

## What this is (and isn't)

- ✅ Intended for **local execution** on a machine with an **NVIDIA GPU**.
- ✅ Runs in containers with `docker compose`.
- ✅ Uses Nerfstudio CLIs:
  - `ns-process-data` supports `video` input via `ns-process-data {video,images,...} --data ... --output-dir ...`. citeturn0search0turn0search3
  - `ns-train` supports methods like `nerfacto` and `splatfacto`. citeturn0search4turn0search5turn3view0
  - `ns-render` has subcommands like `interpolate` and `spiral`. citeturn1search0turn2view0
  - `ns-export` supports exporting geometry; the docs show examples like `ns-export tsdf --load-config CONFIG.yml --output-dir OUTPUT_DIR` and `ns-export poisson ...`. citeturn5view0turn4view0

- ❌ This is not a hosted SaaS template. It’s meant to run on your workstation/server.
- ❌ Output quality depends heavily on capture quality.

## Requirements

1) Docker + docker compose  
2) NVIDIA GPU + drivers  
3) nvidia-container-toolkit (so containers can access the GPU)

Verify GPU-in-docker (Linux example):
```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open:
- Web UI: http://localhost:3000
- API docs: http://localhost:8000/docs

## Outputs

Per job, the worker attempts:
- Render videos:
  - `ns-render interpolate ...` (trajectory derived from the dataset cameras)
  - `ns-render spiral ...` (simple spiral fly-around)
- Geometry exports:
  - point cloud (PLY)
  - TSDF mesh
  - optional Poisson mesh (requires predicted normals per Nerfstudio docs) citeturn5view0

Outputs are stored under:
`./data/jobs/<job_id>/outputs/`

## Tuning

All tuning is via `.env`, using **extra args**:
- `NS_TRAIN_EXTRA_ARGS` → appended to `ns-train <model> --data ...`
- `NS_RENDER_INTERPOLATE_EXTRA_ARGS` → appended to `ns-render interpolate ...`
- `NS_RENDER_SPIRAL_EXTRA_ARGS` → appended to `ns-render spiral ...`

If you want fewer training iterations, you can add the appropriate Nerfstudio flag(s) in `NS_TRAIN_EXTRA_ARGS` after checking `ns-train <model> --help` inside the worker container.

## Security

Local-first. If you expose it to the internet, add auth and harden uploads.

## License

MIT.
