"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function fmtState(s) {
  if (!s) return "—";
  return s;
}

export default function Page() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState("splatfacto");
  const [jobId, setJobId] = useState("");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  const pollRef = useRef(null);

  const canStart = !!file && !uploading;

  async function createJob() {
    setError("");
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("video", file);
      fd.append("model", model);

      const res = await fetch(`${API_BASE}/api/jobs`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setJobId(data.job_id);
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  async function fetchJob(id) {
    const res = await fetch(`${API_BASE}/api/jobs/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  useEffect(() => {
    if (!jobId) return;
    let stopped = false;

    async function tick() {
      try {
        const data = await fetchJob(jobId);
        if (stopped) return;
        setJob(data);
        if (data.state === "SUCCESS" || data.state === "FAILED") return;
      } catch (e) {
        setError(String(e));
      }
      pollRef.current = setTimeout(tick, 2000);
    }

    tick();
    return () => {
      stopped = true;
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [jobId]);

  return (
    <div className="row">
      <div className="card" style={{flex:"1 1 420px"}}>
        <div style={{fontSize:18, fontWeight:800}}>1) Upload video</div>
        <div className="small" style={{marginTop:6}}>
          Best results: slow motion, good lighting, lots of overlap, minimal people moving.
        </div>
        <div style={{height:12}} />
        <input
          className="input"
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <div style={{height:12}} />
        <div style={{fontSize:18, fontWeight:800}}>2) Select model</div>
        <div className="small" style={{marginTop:6}}>
          <b>splatfacto</b> is usually fast and sharp for marketing fly-throughs; <b>nerfacto</b> can be great too.
        </div>
        <div style={{height:12}} />
        <select className="input" value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="splatfacto">splatfacto (Gaussian splats)</option>
          <option value="splatfacto-big">splatfacto-big (higher quality, more VRAM)</option>
          <option value="nerfacto">nerfacto</option>
          <option value="vanilla-nerf">vanilla-nerf (baseline)</option>
        </select>
        <div style={{height:12}} />
        <button className="btn" disabled={!canStart} onClick={createJob}>
          {uploading ? "Uploading..." : "Start reconstruction"}
        </button>
        {error ? (
          <>
            <div style={{height:12}} />
            <div className="small" style={{color:"#ffb4b4"}}>{error}</div>
          </>
        ) : null}
        {jobId ? (
          <>
            <div style={{height:12}} />
            <div className="small">Job ID: <code>{jobId}</code></div>
          </>
        ) : null}
      </div>

      <div className="card" style={{flex:"1 1 420px"}}>
        <div style={{fontSize:18, fontWeight:800}}>3) Status & outputs</div>
        <div className="small" style={{marginTop:6}}>
          This page polls the backend every ~2s. Open the log for details if it fails.
        </div>

        <div style={{height:12}} />
        {!job ? (
          <div className="small">No job yet. Upload a video to start.</div>
        ) : (
          <>
            <div className="row" style={{alignItems:"center"}}>
              <span className="badge">State: {fmtState(job.state)}</span>
              <span className="badge">Progress: {Math.round((job.progress || 0) * 100)}%</span>
              {job.model ? <span className="badge">Model: {job.model}</span> : null}
            </div>
            <div style={{height:12}} />
            <div className="small">{job.message || ""}</div>

            <div style={{height:16}} />
            <div style={{fontWeight:800}}>Downloads</div>
            <div className="small" style={{marginTop:6}}>
              Files are generated under <code>data/jobs/&lt;job_id&gt;/outputs</code>.
            </div>
            <div style={{height:8}} />

            {(job.outputs || []).length === 0 ? (
              <div className="small">No outputs yet.</div>
            ) : (
              <ul>
                {job.outputs.map((p) => (
                  <li key={p} style={{marginBottom:6}}>
                    <a href={`${API_BASE}/api/jobs/${job.job_id}/download?path=${encodeURIComponent(p)}`} target="_blank" rel="noreferrer">
                      {p}
                    </a>
                  </li>
                ))}
              </ul>
            )}

            <div style={{height:12}} />
            <a className="btn" href={`${API_BASE}/api/jobs/${job.job_id}/log`} target="_blank" rel="noreferrer">
              Open log
            </a>
          </>
        )}
      </div>
    </div>
  );
}
