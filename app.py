import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import base64
import os
import uuid
import threading
import time

# ── Write CSS to assets/ so Dash auto-serves it ───────────────────────────────
os.makedirs("assets", exist_ok=True)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

body { font-family: 'DM Sans', sans-serif; background: #0d1117; color: #e6edf3; margin: 0; }

.hero {
    background: linear-gradient(135deg, #1D9E75 0%, #085041 100%);
    padding: 2rem 2.5rem 1.5rem;
    position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; right: -60px; top: -60px;
    width: 280px; height: 280px; border-radius: 50%;
    background: rgba(255,255,255,0.05);
}
.hero-label { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 2px;
              color: rgba(255,255,255,0.6); text-transform: uppercase; margin-bottom: 4px; }
.hero-title { font-family: 'Bebas Neue', sans-serif; font-size: 52px;
              color: #fff; letter-spacing: 3px; line-height: 1; margin: 0; }
.hero-sub   { font-size: 13px; color: rgba(255,255,255,0.65); margin-top: 6px; }
.hero-dot   { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
              background: #9FE1CB; margin-right: 6px; vertical-align: middle; }

.upload-zone {
    border: 2px dashed #5DCAA5; border-radius: 16px;
    background: rgba(29,158,117,0.06); padding: 3rem 2rem;
    text-align: center; cursor: pointer;
    transition: background .2s, border-color .2s;
}
.upload-zone:hover { background: rgba(29,158,117,0.12); border-color: #1D9E75; }
.upload-icon {
    width: 64px; height: 64px; border-radius: 50%; background: #1D9E75;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 1rem;
}
.upload-title { font-size: 20px; font-weight: 500; color: #9FE1CB; margin-bottom: 4px; }
.upload-sub   { font-size: 13px; color: #5DCAA5; }

.file-preview {
    display: flex; align-items: center; gap: 14px;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 12px 16px; margin-top: 12px;
}
.file-thumb {
    width: 48px; height: 36px; border-radius: 8px; background: #1D9E75;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.file-name { font-size: 14px; font-weight: 500; color: #e6edf3; }
.file-meta { font-size: 12px; color: #8b949e; margin-top: 2px; }

.btn-analyze {
    background: #1D9E75; color: #fff; border: none; border-radius: 10px;
    padding: .85rem; font-family: 'DM Sans', sans-serif;
    font-size: 15px; font-weight: 500; width: 100%; margin-top: 14px;
    cursor: pointer; transition: opacity .2s, transform .1s;
}
.btn-analyze:hover   { opacity: .9; }
.btn-analyze:active  { transform: scale(.98); }
.btn-analyze:disabled{ opacity: .4; cursor: not-allowed; }

.proc-card { background: #161b22; border: 1px solid #30363d; border-radius: 14px; overflow: hidden; }
.proc-header {
    background: #0d1117; padding: 10px 16px;
    display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #30363d;
}
.proc-dot { width: 11px; height: 11px; border-radius: 50%; }
.proc-title-bar { font-family: 'DM Mono', monospace; font-size: 12px; color: #6e7681; margin: 0 auto; }
.proc-body { padding: 1.25rem; }

.step-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #21262d; }
.step-row:last-child { border-bottom: none; }
.step-icon {
    width: 34px; height: 34px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
}
.step-icon.pending { background: #21262d; }
.step-icon.running { background: #2d2016; animation: pulse 1s ease-in-out infinite; }
.step-icon.done    { background: #122d22; }
.step-name { font-size: 14px; font-weight: 500; color: #e6edf3; }
.step-desc { font-size: 12px; color: #8b949e; margin-top: 2px; }
.step-badge {
    font-family: 'DM Mono', monospace; font-size: 11px;
    padding: 3px 8px; border-radius: 6px; white-space: nowrap;
}
.step-badge.pending { background: #21262d; color: #6e7681; }
.step-badge.running { background: #2d2016; color: #d29922; }
.step-badge.done    { background: #122d22; color: #3fb950; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.45} }

.prog-track { height: 6px; background: #21262d; border-radius: 99px; overflow: hidden; margin-top: 14px; }
.prog-fill  { height: 100%; background: #1D9E75; border-radius: 99px; transition: width .5s ease; }
.prog-label { display: flex; justify-content: space-between; font-size: 12px; color: #8b949e; margin-top: 6px; }
.prog-pct   { font-family: 'DM Mono', monospace; color: #3fb950; font-weight: 500; }

.log-box {
    background: #0d1117; border-radius: 10px; padding: 12px 14px;
    font-family: 'DM Mono', monospace; font-size: 11px; color: #3fb950;
    height: 110px; overflow-y: auto; margin-top: 12px; line-height: 1.85;
    border: 1px solid #21262d;
}

.video-player-wrap {
    background: #000; border-radius: 14px; overflow: hidden;
    aspect-ratio: 16/9; position: relative;
}
.video-player-wrap video { width: 100%; height: 100%; object-fit: contain; display: block; }

.stat-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 1rem; text-align: center;
}
.stat-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
.stat-val   { font-family: 'Bebas Neue', sans-serif; font-size: 32px; color: #e6edf3; line-height: 1; }
.stat-unit  { font-size: 12px; color: #8b949e; margin-left: 2px; }
.stat-sub   { font-size: 11px; color: #3fb950; margin-top: 3px; }

.player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1rem; }
.player-avatar {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 500; font-size: 13px;
}
.p1-avatar { background: rgba(29,158,117,.2); color: #5DCAA5; }
.p2-avatar { background: rgba(186,117,23,.2);  color: #d29922; }
.bar-label-row { display: flex; justify-content: space-between; font-size: 12px; color: #8b949e; margin-bottom: 3px; }
.bar-track { height: 5px; background: #21262d; border-radius: 99px; overflow: hidden; margin-bottom: 8px; }
.bar-p1    { height: 100%; background: #1D9E75; border-radius: 99px; }
.bar-p2    { height: 100%; background: #d29922; border-radius: 99px; }

.tab-btn {
    background: none; border: none; border-bottom: 2px solid transparent;
    color: #8b949e; font-family: 'DM Sans', sans-serif;
    font-size: 13px; padding: 8px 16px; cursor: pointer;
    transition: color .15s; margin-bottom: -1px;
}
.tab-btn.active { color: #3fb950; border-bottom-color: #3fb950; font-weight: 500; }
.tab-border { border-bottom: 1px solid #30363d; margin-bottom: 1rem; }

.section-title {
    font-family: 'DM Mono', monospace; font-size: 11px;
    text-transform: uppercase; letter-spacing: 1px; color: #8b949e; margin-bottom: 10px;
}
.info-box {
    background: rgba(88,166,255,.08); border: 1px solid rgba(88,166,255,.3);
    border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #8b949e;
}
.success-box {
    background: rgba(29,158,117,.1); border: 1px solid rgba(29,158,117,.35);
    border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #3fb950;
}

/* ── Dual video layout ── */
.dual-video-grid {
    display: grid;
    grid-template-columns: 1fr 2px 1fr;
    align-items: start;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 16px;
    overflow: hidden;
    padding: 16px;
    gap: 16px;
}
.video-col { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.video-divider { width: 1px; background: #30363d; align-self: stretch; }
.video-label { display: flex; align-items: center; gap: 7px; padding: 0 2px 2px; }
.vid-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-amber { background: #d29922; }
.dot-green { background: #3fb950; }
.vid-label-text {
    font-family: 'DM Mono', monospace; font-size: 11px;
    color: #8b949e; text-transform: uppercase; letter-spacing: 1px;
}
.video-player-wrap {
    background: #000; border-radius: 10px; overflow: hidden;
    aspect-ratio: 16/9; position: relative;
}
.video-player-wrap video { width: 100%; height: 100%; object-fit: contain; display: block; }
"""

with open("assets/styles.css", "w") as f:
    f.write(CUSTOM_CSS)

# ── App init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server

UPLOAD_DIR  = "uploads"
OUTPUT_DIR  = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── In-memory job store (replace with Redis/DB for production) ────────────────
jobs: dict[str, dict] = {}   # job_id → {status, step, pct, log, output_path}

PIPELINE_STEPS = [
    ("Reading video frames",    "Decoding input into frame buffer",          12),
    ("Player detection",        "YOLOv8x bounding-box inference",            25),
    ("Ball tracking",           "YOLOv5 + trajectory interpolation",         38),
    ("Court line detection",    "CNN keypoint model — 14 points",            50),
    ("Mini court mapping",      "Pixel-to-metre coordinate conversion",      62),
    ("Shot detection & speed",  "Ball shot frames + km/h computation",       74),
    ("Player stats assembly",   "Aggregating DataFrame per frame",           86),
    ("Rendering output video",  "Drawing overlays, boxes & stats",          100),
]

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    # Hidden state stores
    dcc.Store(id="job-id-store"),
    dcc.Store(id="stage-store", data="upload"),   # upload | processing | result
    dcc.Store(id="tab-store",   data="players"),
    dcc.Store(id="stats-store", data={}),

    # Poll timer (only active during processing)
    dcc.Interval(id="poll-interval", interval=600, n_intervals=0, disabled=True),

    # ── Hero ──────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([html.Span(className="hero-dot"), "AI-Powered Analysis"],
                 className="hero-label"),
        html.H1("Tennis Vision", className="hero-title"),
        html.P("Player tracking · Ball detection · Court mapping · Speed analytics",
               className="hero-sub"),
    ], className="hero"),

    # ── Main content ──────────────────────────────────────────────────────────
    html.Div([

        # Stage: UPLOAD ───────────────────────────────────────────────────────
        html.Div(id="stage-upload", children=[
            html.P("Upload a match recording to begin computer-vision analysis.",
                   style={"fontSize": "13px", "color": "#8b949e", "marginBottom": "14px"}),

            dcc.Upload(
                id="video-upload",
                children=html.Div([
                    html.Div("▲", className="upload-icon",
                             style={"fontSize": "28px", "color": "#fff", "lineHeight": "64px"}),
                    html.Div("Drop your video here", className="upload-title"),
                    html.Div("MP4 · AVI · MOV — up to 2 GB", className="upload-sub"),
                ]),
                className="upload-zone",
                accept="video/*",
                max_size=2 * 1024 * 1024 * 1024,
            ),

            html.Div(id="file-preview-area"),
            html.Button("Analyze Video", id="start-btn", className="btn-analyze",
                        disabled=True, n_clicks=0),
            html.Div(id="upload-error", style={"color": "#f85149", "fontSize": "12px",
                                               "marginTop": "8px"}),
        ]),

        # Stage: PROCESSING ───────────────────────────────────────────────────
        html.Div(id="stage-processing", style={"display": "none"}, children=[
            html.Div([
                html.Div([
                    html.Span(className="proc-dot", style={"background": "#f85149"}),
                    html.Span(className="proc-dot", style={"background": "#d29922"}),
                    html.Span(className="proc-dot", style={"background": "#3fb950"}),
                    html.Span("tennis_vision_pipeline.py", className="proc-title-bar"),
                ], className="proc-header"),
                html.Div([
                    html.Div(id="step-list"),
                    html.Div(html.Div(id="prog-fill", className="prog-fill",
                                     style={"width": "0%"}),
                             className="prog-track"),
                    html.Div([
                        html.Span("Pipeline progress"),
                        html.Span("0%", id="pct-label", className="prog-pct"),
                    ], className="prog-label"),
                ], className="proc-body"),
            ], className="proc-card"),
            html.Div(id="log-box", className="log-box"),
        ]),

        # Stage: RESULT ───────────────────────────────────────────────────────
        html.Div(id="stage-result", style={"display": "none"}, children=[
            # Side-by-side video players
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(className="vid-dot dot-amber"),
                        html.Span("Original", className="vid-label-text"),
                    ], className="video-label"),
                    html.Div(
                        html.Video(id="original-video", controls=True,
                                   style={"width": "100%", "height": "100%", "objectFit": "contain"}),
                        className="video-player-wrap",
                    ),
                ], className="video-col"),
                html.Div(className="video-divider"),
                html.Div([
                    html.Div([
                        html.Span(className="vid-dot dot-green"),
                        html.Span("Processed", className="vid-label-text"),
                    ], className="video-label"),
                    html.Div(
                        html.Video(id="result-video", controls=True,
                                   style={"width": "100%", "height": "100%", "objectFit": "contain"}),
                        className="video-player-wrap",
                    ),
                ], className="video-col"),
            ], className="dual-video-grid"),

            # Stat cards
            html.Div([
                html.Div([html.Div("Ball shots", className="stat-label"),
                          html.Div([html.Span("0", id="stat-ball-shots", className="stat-val"),
                                    html.Span(" hits", className="stat-unit")]),
                          html.Div("detected", className="stat-sub")],
                         className="stat-card"),
                html.Div([html.Div("Max ball speed", className="stat-label"),
                          html.Div([html.Span("0", id="stat-max-speed", className="stat-val"),
                                    html.Span(" km/h", className="stat-unit")]),
                          html.Div("overall", className="stat-sub")],
                         className="stat-card"),
                html.Div([html.Div("Court keypoints", className="stat-label"),
                          html.Div([html.Span("0", id="stat-keypoints", className="stat-val"),
                                    html.Span(" pts", className="stat-unit")]),
                          html.Div("mapped", className="stat-sub")],
                         className="stat-card"),
                html.Div([html.Div("Frames", className="stat-label"),
                          html.Div(html.Span("0", id="stat-frames", className="stat-val")),
                          html.Div("processed", className="stat-sub")],
                         className="stat-card"),
            ], style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)",
                      "gap": "10px", "marginTop": "1.25rem"}),

            # Tabs
            html.Div([
                html.Button("Players", id="tab-players", className="tab-btn active", n_clicks=0),
                html.Button("Ball",    id="tab-ball",    className="tab-btn",        n_clicks=0),
                html.Button("Court",   id="tab-court",   className="tab-btn",        n_clicks=0),
            ], className="tab-border", style={"display": "flex", "marginTop": "1.25rem"}),

            html.Div(id="tab-content"),

            html.Button("↺ Analyze another video", id="reset-btn",
                        style={"marginTop": "1.5rem", "background": "none",
                               "border": "1px solid #30363d", "color": "#8b949e",
                               "borderRadius": "8px", "padding": "8px 16px",
                               "cursor": "pointer", "fontFamily": "'DM Sans', sans-serif",
                               "fontSize": "13px"},
                        n_clicks=0),
        ]),

    ], style={"padding": "1.5rem"}),
], style={"minHeight": "100vh"})


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_bytes(b):
    if b < 1024 * 1024:
        return f"{b/1024:.1f} KB"
    return f"{b/1024/1024:.1f} MB"


def run_pipeline(job_id: str, input_path: str, output_path: str):
    """Simulates (or calls real) pipeline in a background thread."""
    log_lines = [
        ("info",  "[init] Loading models from /models/"),
        ("",      f"[read] Decoding video → {input_path}"),
        ("",      "[yolo] yolov8x.pt — player detection started"),
        ("warn",  "[yolo] Using stub cache: tracker_stubs/player_detections.pkl"),
        ("",      "[yolo] yolo5_last.pt — ball detection started"),
        ("warn",  "[yolo] Using stub cache: tracker_stubs/ball_detections.pkl"),
        ("",      "[ball] Interpolating missing positions…"),
        ("info",  "[court] Running keypoints_model.pth on frame 0"),
        ("",      "[court] 14 keypoints detected successfully"),
        ("",      "[filter] Choosing 2 players closest to court"),
        ("",      "[mini] Initialising MiniCourt from frame dimensions"),
        ("",      "[shot] Ball shot frames detected: 47 events"),
        ("",      "[speed] Avg ball speed: 136.2 km/h"),
        ("warn",  "[stats] NaN in early frames — forward-filling"),
        ("info",  "[render] Drawing bounding boxes, keypoints, mini court…"),
        ("",      f"[save] Writing output → {output_path}"),
        ("info",  "[done] Pipeline complete ✓"),
    ]
    log_per_step = max(1, len(log_lines) // len(PIPELINE_STEPS))

    for idx, (step_name, step_desc, pct) in enumerate(PIPELINE_STEPS):
        jobs[job_id]["step"] = idx
        jobs[job_id]["status"] = "running"
        jobs[job_id]["pct"] = pct - 12   # start of this step

        # Drip logs for this step
        start = idx * log_per_step
        for li in range(start, min(start + log_per_step, len(log_lines))):
            time.sleep(0.35)
            cls, txt = log_lines[li]
            jobs[job_id]["log"].append((cls, txt))

        time.sleep(0.6)
        jobs[job_id]["pct"] = pct

        # ── Real pipeline call would go here ──────────────────────────────
        # (This is a mock progress bar loop)

    # Actually process the video
    from process_tennis_video import process_tennis_video
    stats = process_tennis_video(input_path, output_path)

    jobs[job_id]["status"] = "done"
    jobs[job_id]["output_path"] = output_path
    jobs[job_id]["stats"] = stats


# ── Callback: handle upload ───────────────────────────────────────────────────
@app.callback(
    Output("file-preview-area", "children"),
    Output("start-btn", "disabled"),
    Output("job-id-store", "data"),
    Input("video-upload", "contents"),
    State("video-upload", "filename"),
    State("video-upload", "file_size"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename, file_size):
    if not contents:
        return "", True, None

    job_id = str(uuid.uuid4())
    # Save file
    content_type, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    ext = os.path.splitext(filename)[1] if filename else ".mp4"
    input_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    with open(input_path, "wb") as f:
        f.write(decoded)

    size_str = format_bytes(len(decoded))
    preview = html.Div([
        html.Div("🎬", className="file-thumb", style={"fontSize": "22px", "lineHeight": "36px"}),
        html.Div([
            html.Div(filename or "video", className="file-name"),
            html.Div(f"{size_str} — ready to process", className="file-meta"),
        ]),
    ], className="file-preview")

    return preview, False, job_id


# ── Callback: start processing ────────────────────────────────────────────────
@app.callback(
    Output("stage-store", "data"),
    Output("poll-interval", "disabled"),
    Input("start-btn", "n_clicks"),
    State("job-id-store", "data"),
    State("video-upload", "filename"),
    prevent_initial_call=True,
)
def start_processing(n_clicks, job_id, filename):
    if not n_clicks or not job_id:
        return dash.no_update, True

    ext = os.path.splitext(filename)[1] if filename else ".mp4"
    input_path  = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_output.webm")

    jobs[job_id] = {
        "status": "running", "step": 0, "pct": 0,
        "log": [], "output_path": None, "input_path": input_path,
    }

    thread = threading.Thread(target=run_pipeline,
                              args=(job_id, input_path, output_path),
                              daemon=True)
    thread.start()
    return "processing", False


# ── Callback: poll pipeline state ─────────────────────────────────────────────
@app.callback(
    Output("stage-upload",     "style"),
    Output("stage-processing", "style"),
    Output("stage-result",     "style"),
    Output("step-list",        "children"),
    Output("prog-fill",        "style"),
    Output("pct-label",        "children"),
    Output("log-box",          "children"),
    Output("poll-interval",    "disabled", allow_duplicate=True),
    Output("stage-store",      "data",     allow_duplicate=True),
    Output("result-video",     "src"),
    Output("original-video",   "src"),
    Output("stats-store",      "data"),
    Output("stat-ball-shots",  "children"),
    Output("stat-max-speed",   "children"),
    Output("stat-keypoints",   "children"),
    Output("stat-frames",      "children"),
    Input("poll-interval",     "n_intervals"),
    State("stage-store",       "data"),
    State("job-id-store",      "data"),
    prevent_initial_call=True,
)
def poll_state(n, stage, job_id):
    show  = {"display": "block"}
    hide  = {"display": "none"}
    blank = dash.no_update

    if stage == "upload":
        return show, hide, hide, [], {"width": "0%"}, "0%", [], True, blank, "", "", {}, "0", "0", "0", "0"

    if stage == "processing" and job_id and job_id in jobs:
        job = jobs[job_id]
        pct = job["pct"]

        # Build step rows
        step_rows = []
        for si, (sname, sdesc, _) in enumerate(PIPELINE_STEPS):
            if si < job["step"]:
                cls, badge_cls, badge_txt = "done", "done", "done"
            elif si == job["step"] and job["status"] == "running":
                cls, badge_cls, badge_txt = "running", "running", "running"
            else:
                cls, badge_cls, badge_txt = "pending", "pending", "waiting"

            icons = ["📹","🧍","🎾","🏟️","🗺️","⚡","📊","🎬"]
            step_rows.append(html.Div([
                html.Div(icons[si], className=f"step-icon {cls}"),
                html.Div([
                    html.Div(sname, className="step-name"),
                    html.Div(sdesc, className="step-desc"),
                ], style={"flex": "1"}),
                html.Span(badge_txt, className=f"step-badge {badge_cls}"),
            ], className="step-row"))

        # Build log
        log_children = []
        for cls, txt in job["log"][-30:]:
            style = {}
            if cls == "warn": style = {"color": "#d29922"}
            elif cls == "info": style = {"color": "#58a6ff"}
            log_children.append(html.Div(txt, style=style))

        if job["status"] == "done":
            # Encode output video as data URI for the player
            output_path = job["output_path"]
            video_src = ""
            if output_path and os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(output_path)[1].lstrip(".")
                mime = {"mp4": "video/mp4", "avi": "video/avi",
                        "mov": "video/quicktime", "webm": "video/webm"}.get(ext, "video/mp4")
                video_src = f"data:{mime};base64,{data}"

            orig_src = ""
            input_path = job.get("input_path", "")
            if input_path and os.path.exists(input_path):
                with open(input_path, "rb") as f:
                    orig_data = base64.b64encode(f.read()).decode()
                orig_ext = os.path.splitext(input_path)[1].lstrip(".")
                orig_mime = {"mp4": "video/mp4", "avi": "video/avi",
                             "mov": "video/quicktime"}.get(orig_ext, "video/mp4")
                orig_src = f"data:{orig_mime};base64,{orig_data}"

            stats = job.get("stats", {})
            return (hide, hide, show,
                    step_rows, {"width": "100%"}, "100%",
                    log_children, True, "result", video_src, orig_src,
                    stats, str(stats.get("ball_shots", 0)),
                    f"{stats.get('max_ball_speed', 0):.0f}",
                    str(stats.get("court_keypoints", 0)),
                    str(stats.get("frames", 0)))

        return (hide, show, hide,
                step_rows, {"width": f"{pct}%"}, f"{pct}%",
                log_children, False, blank, "", "", blank, blank, blank, blank, blank)

    if stage == "result":
        return hide, hide, show, [], {"width": "100%"}, "100%", [], True, blank, blank, blank, blank, blank, blank, blank, blank

    return show, hide, hide, [], {"width": "0%"}, "0%", [], True, blank, "", "", blank, blank, blank, blank, blank


# ── Callback: tab switching ───────────────────────────────────────────────────
@app.callback(
    Output("tab-content",  "children"),
    Output("tab-players",  "className"),
    Output("tab-ball",     "className"),
    Output("tab-court",    "className"),
    Input("tab-players",   "n_clicks"),
    Input("tab-ball",      "n_clicks"),
    Input("tab-court",     "n_clicks"),
    Input("stats-store",   "data")
)
def switch_tab(p, b, c, stats):
    stats = stats or {}
    ctx = callback_context
    if not ctx.triggered:
        active = "players"
    else:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "stats-store":
            active = "players"
        else:
            active = prop_id.replace("tab-", "")

    def cls(t): return "tab-btn active" if t == active else "tab-btn"

    if active == "players":
        p1_shot_spd = f"{stats.get('player_1_avg_shot_speed', 0):.0f}"
        p1_mov_spd  = f"{stats.get('player_1_avg_player_speed', 0):.1f}"
        p1_shots    = str(stats.get('player_1_shots', 0))
        
        p2_shot_spd = f"{stats.get('player_2_avg_shot_speed', 0):.0f}"
        p2_mov_spd  = f"{stats.get('player_2_avg_player_speed', 0):.1f}"
        p2_shots    = str(stats.get('player_2_shots', 0))

        content = html.Div([
            html.Div([
                # Player 1
                html.Div([
                    html.Div([
                        html.Div("P1", className="player-avatar p1-avatar"),
                        html.Div([html.Div("Player 1", style={"fontSize":"14px","fontWeight":"500"}),
                                  html.Div("Near baseline", style={"fontSize":"11px","color":"#8b949e"})]),
                    ], style={"display":"flex","alignItems":"center","gap":"10px","marginBottom":"12px"}),
                    html.Div([html.Div(["Avg shot speed", html.Span(f"{p1_shot_spd} km/h")], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p1", style={"width":"75%"}), className="bar-track")]),
                    html.Div([html.Div(["Avg move speed", html.Span(f"{p1_mov_spd} km/h")], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p1", style={"width":"46%"}), className="bar-track")]),
                    html.Div([html.Div(["Shots taken", html.Span(p1_shots)], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p1", style={"width":"51%"}), className="bar-track")]),
                ], className="player-card"),
                # Player 2
                html.Div([
                    html.Div([
                        html.Div("P2", className="player-avatar p2-avatar"),
                        html.Div([html.Div("Player 2", style={"fontSize":"14px","fontWeight":"500"}),
                                  html.Div("Far baseline", style={"fontSize":"11px","color":"#8b949e"})]),
                    ], style={"display":"flex","alignItems":"center","gap":"10px","marginBottom":"12px"}),
                    html.Div([html.Div(["Avg shot speed", html.Span(f"{p2_shot_spd} km/h")], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p2", style={"width":"65%"}), className="bar-track")]),
                    html.Div([html.Div(["Avg move speed", html.Span(f"{p2_mov_spd} km/h")], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p2", style={"width":"57%"}), className="bar-track")]),
                    html.Div([html.Div(["Shots taken", html.Span(p2_shots)], className="bar-label-row"),
                              html.Div(html.Div(className="bar-p2", style={"width":"49%"}), className="bar-track")]),
                ], className="player-card"),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"12px"}),
        ])

    elif active == "ball":
        min_spd = f"{stats.get('min_ball_speed', 0):.0f}"
        avg_spd = f"{stats.get('avg_ball_speed', 0):.0f}"
        max_spd = f"{stats.get('max_ball_speed', 0):.0f}"
        shots = str(stats.get('ball_shots', 0))

        content = html.Div([
            html.Div("Ball trajectory analysis", className="section-title"),
            html.Div([
                html.Div([html.Div("Min speed", className="stat-label"),
                          html.Div([html.Span(min_spd,  className="stat-val"), html.Span(" km/h", className="stat-unit")])],
                         className="stat-card"),
                html.Div([html.Div("Avg speed", className="stat-label"),
                          html.Div([html.Span(avg_spd, className="stat-val"), html.Span(" km/h", className="stat-unit")])],
                         className="stat-card"),
                html.Div([html.Div("Max speed", className="stat-label"),
                          html.Div([html.Span(max_spd, className="stat-val"), html.Span(" km/h", className="stat-unit")])],
                         className="stat-card"),
            ], style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"10px","marginBottom":"10px"}),
            html.Div(f"Ball trajectory interpolated across {shots} shot segments using YOLOv5 ball detector "
                     "with position interpolation to fill missing frames.",
                     className="info-box"),
        ])

    else:  # court
        kps = str(stats.get('court_keypoints', 14))
        content = html.Div([
            html.Div("Court detection", className="section-title"),
            html.Div(f"{kps} court keypoints detected via CNN. Double line width used for pixel-to-metre "
                     "conversion. Mini court overlay active in output frames.",
                     className="success-box"),
        ])

    return content, cls("players"), cls("ball"), cls("court")


# ── Callback: reset ────────────────────────────────────────────────────────────
@app.callback(
    Output("stage-store",      "data",    allow_duplicate=True),
    Output("stage-upload",     "style",   allow_duplicate=True),
    Output("stage-processing", "style",   allow_duplicate=True),
    Output("stage-result",     "style",   allow_duplicate=True),
    Output("file-preview-area","children", allow_duplicate=True),
    Output("start-btn",        "disabled", allow_duplicate=True),
    Input("reset-btn",         "n_clicks"),
    prevent_initial_call=True,
)
def reset(n):
    if not n:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    return "upload", {"display":"block"}, {"display":"none"}, {"display":"none"}, "", True


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)