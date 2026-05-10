import base64
import os
import threading
import time
import uuid
from analytics_tabs import build_kinematics, build_trajectory, build_topography

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback_context, dcc, html

# ── Write CSS to assets/ so Dash auto-serves it ───────────────────────────────
os.makedirs("assets", exist_ok=True)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-main: #050505;
    --accent: #1D9E75;
    --accent-glow: rgba(29, 158, 117, 0.4);
    --card-bg: rgba(13, 17, 23, 0.7);
    --glass-border: rgba(255, 255, 255, 0.08);
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
}

body { 
    font-family: 'Plus Jakarta Sans', sans-serif; 
    background: var(--bg-main); 
    color: var(--text-primary); 
    margin: 0; 
    overflow-x: hidden;
}

.sidebar {
    background: rgba(10,10,10,0.8);
    border-right: 1px solid var(--glass-border);
    backdrop-filter: blur(40px);
}

.hero-label { 
    font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 3px;
    color: var(--accent); text-transform: uppercase; margin-bottom: 8px;
    display: flex; align-items: center; gap: 8px;
}
.hero-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 10px var(--accent); }

.hero-sub { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }

.upload-container {
    padding: 2px; background: var(--glass-border); border-radius: 24px;
    transition: background 0.3s ease;
}
.upload-container:hover { background: rgba(29, 158, 117, 0.3); }

.upload-zone {
    border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 22px;
    background: var(--card-bg); padding: 4rem 2rem;
    text-align: center; cursor: pointer; backdrop-filter: blur(20px);
    transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
}
.upload-icon {
    width: 56px; height: 56px; border-radius: 16px; background: var(--accent);
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 1.5rem; color: #fff; font-size: 24px;
}
.upload-title { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 600; color: #fff; }
.upload-sub { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }

.btn-analyze {
    background: var(--accent); color: #fff; border: none; border-radius: 14px;
    padding: 1rem 1.5rem; font-family: 'Space Grotesk', sans-serif;
    font-size: 16px; font-weight: 600; width: 100%; margin-top: 20px;
    cursor: pointer; transition: all 0.5s cubic-bezier(0.32, 0.72, 0, 1);
}
.btn-analyze:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(29, 158, 117, 0.4); }
.btn-analyze:disabled { opacity: 0.3; cursor: not-allowed; }

.pro-card-outer {
    padding: 1px; background: var(--glass-border); border-radius: 20px;
}
.pro-card-inner {
    background: var(--card-bg); border-radius: 19px; overflow: hidden;
    backdrop-filter: blur(30px);
    border: 1px solid var(--glass-border);
}

.stat-card {
    background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
    border-radius: 18px; padding: 1.5rem;
}
.stat-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--text-secondary); letter-spacing: 2px; margin-bottom: 8px; }
.stat-val { font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; color: #fff; }

.step-row { 
    display: flex; align-items: center; gap: 16px; padding: 14px 20px; 
    border-bottom: 1px solid var(--glass-border);
}
.step-icon {
    width: 32px; height: 32px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; background: rgba(255,255,255,0.03);
}
.step-icon.done { background: rgba(29, 158, 117, 0.1); color: var(--accent); }
.step-icon.running { animation: pulse 2s infinite; background: rgba(210, 153, 34, 0.1); }

.prog-track { height: 4px; background: rgba(255,255,255,0.05); border-radius: 99px; overflow: hidden; }
.prog-fill { height: 100%; background: var(--accent); box-shadow: 0 0 15px var(--accent); transition: width 0.8s ease; }

.tab-btn {
    background: none; border: none; color: var(--text-secondary); font-family: 'Space Grotesk', sans-serif;
    font-size: 13px; font-weight: 500; padding: 16px 20px; cursor: pointer; position: relative;
}
.tab-btn.active { color: var(--accent); }
.tab-btn.active::after {
    content: ''; position: absolute; bottom: 0; left: 20px; right: 20px; height: 2px;
    background: var(--accent); box-shadow: 0 0 10px var(--accent);
}

.log-box {
    background: #000; border-radius: 14px; padding: 16px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--accent);
    height: 180px; overflow-y: auto; margin-top: 1.5rem; line-height: 1.8;
    border: 1px solid var(--glass-border);
}

.player-card {
    background: rgba(255,255,255,0.02); border-radius: 16px; padding: 20px;
    border: 1px solid var(--glass-border);
}
.player-avatar {
    width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 12px;
}
.p1-avatar { background: rgba(29, 158, 117, 0.2); color: var(--accent); border: 1px solid var(--accent); }
.p2-avatar { background: rgba(210, 153, 34, 0.2); color: #d29922; border: 1px solid #d29922; }

.bar-track { height: 4px; background: rgba(255,255,255,0.05); border-radius: 99px; margin-top: 6px; margin-bottom: 12px; }
.bar-p1 { height: 100%; background: var(--accent); border-radius: 99px; }
.bar-p2 { height: 100%; background: #d29922; border-radius: 99px; }
.bar-label-row { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-secondary); }
.bar-label-row span { color: #fff; font-weight: 500; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
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
    ("Spatial Decoupling",      "Initializing 2-pass streaming pipeline",      12),
    ("Vision Engine",          "YOLOv8x Transformer inference",               25),
    ("Trajectory Kinematics",  "Bézier-smoothed ball tracking",               38),
    ("Geometric Mapping",      "Spatial keypoint normalization",              50),
    ("Metre Transformation",   "Perspective-aware coordinate mapping",        62),
    ("Analytic Synthesis",     "Shot speed & movement aggregation",           85),
    ("Broadcast Rendering",    "Alpha-blended PIL overlay generation",        100),
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

    # ── Sidebar ──
    html.Div([

        # ── Logo + Brand ──
        html.Div([
            html.Img(src="/assets/ITI.png", style={
                "width": "64px", "height": "64px", "objectFit": "contain",
                "borderRadius": "12px", "marginBottom": "12px",
                "boxShadow": "0 0 20px rgba(29,158,117,0.25)"
            }),
            html.Div([html.Span(className="hero-dot"), "ANALYTICS ENGINE"], className="hero-label", style={"fontSize":"9px"}),
            html.H1("T-Board", style={
                "fontSize": "26px", "fontWeight": "700", "margin": "0",
                "letterSpacing": "-1px", "fontFamily": "Space Grotesk, sans-serif"
            }),
        ], style={"padding":"20px","borderBottom":"1px solid var(--glass-border)","marginBottom":"16px"}),

        # ── System Status ──
        html.Div([
            html.Div("SYSTEM STATUS", className="stat-label", style={"padding":"0 20px","marginBottom":"6px"}),
            html.Div(id="sidebar-status", children=[
                html.Div([
                    html.Div(style={"background":"#27c93f","width":"8px","height":"8px",
                                    "borderRadius":"50%","boxShadow":"0 0 6px #27c93f"}),
                    html.Span("KERNEL: READY", style={"fontSize":"10px","fontFamily":"JetBrains Mono"})
                ], style={"display":"flex","alignItems":"center","gap":"8px","padding":"8px 20px"})
            ]),
        ], style={"marginBottom":"16px","borderBottom":"1px solid var(--glass-border)","paddingBottom":"16px"}),

        # ── Insight Cards (hidden until analysis done) ──
        html.Div([
            html.Div("MATCH INSIGHTS", className="stat-label", style={"padding":"0 20px","marginBottom":"10px"}),

            # Row 1: Rallies + Max Velocity
            html.Div([
                html.Div([
                    html.Div("🎾  RALLIES", className="stat-label"),
                    html.Div("–", id="stat-ball-shots-side",
                             style={"fontFamily":"Space Grotesk","fontSize":"26px","fontWeight":"700","color":"#fff"})
                ], className="stat-card", style={"padding":"14px 16px"}),
                html.Div([
                    html.Div("⚡  MAX VEL", className="stat-label"),
                    html.Div([
                        html.Span("–", id="stat-max-speed-side",
                                  style={"fontFamily":"Space Grotesk","fontSize":"26px","fontWeight":"700","color":"#1D9E75"}),
                        html.Span(" km/h", style={"fontSize":"10px","color":"#8b949e"}),
                    ])
                ], className="stat-card", style={"padding":"14px 16px"}),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"8px","padding":"0 16px","marginBottom":"8px"}),

            # Row 2: P1 Shots + P2 Shots
            html.Div([
                html.Div([
                    html.Div("P1  SHOTS", className="stat-label"),
                    html.Div("–", id="stat-p1-shots-side",
                             style={"fontFamily":"Space Grotesk","fontSize":"22px","fontWeight":"700","color":"#1D9E75"})
                ], className="stat-card", style={"padding":"12px 16px"}),
                html.Div([
                    html.Div("P2  SHOTS", className="stat-label"),
                    html.Div("–", id="stat-p2-shots-side",
                             style={"fontFamily":"Space Grotesk","fontSize":"22px","fontWeight":"700","color":"#D29922"})
                ], className="stat-card", style={"padding":"12px 16px"}),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"8px","padding":"0 16px","marginBottom":"8px"}),

            # Row 3: Avg Ball Speed (full width)
            html.Div([
                html.Div("AVG BALL SPEED", className="stat-label"),
                html.Div([
                    html.Span("–", id="stat-avg-speed-side",
                              style={"fontFamily":"Space Grotesk","fontSize":"22px","fontWeight":"700","color":"#fff"}),
                    html.Span(" km/h", style={"fontSize":"10px","color":"#8b949e","marginLeft":"4px"}),
                ])
            ], className="stat-card", style={"padding":"12px 16px","margin":"0 16px 8px"}),

            # Row 4: Court KPs + Frames
            html.Div([
                html.Div([
                    html.Div("KEYPOINTS", className="stat-label"),
                    html.Div("–", id="stat-kps-side",
                             style={"fontFamily":"Space Grotesk","fontSize":"22px","fontWeight":"700","color":"#fff"})
                ], className="stat-card", style={"padding":"12px 16px"}),
                html.Div([
                    html.Div("FRAMES", className="stat-label"),
                    html.Div("–", id="stat-frames-side",
                             style={"fontFamily":"Space Grotesk","fontSize":"22px","fontWeight":"700","color":"#fff"})
                ], className="stat-card", style={"padding":"12px 16px"}),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"8px","padding":"0 16px","marginBottom":"8px"}),

            # Row 5: Win zone badge
            html.Div([
                html.Div("🏆  TOP TACTICAL ZONE", className="stat-label"),
                html.Div("DEEP BACKHAND CROSS", id="stat-zone-side",
                         style={"fontSize":"11px","fontWeight":"600","color":"#1D9E75",
                                "fontFamily":"JetBrains Mono","marginTop":"4px"})
            ], className="stat-card", style={"padding":"12px 16px","margin":"0 16px 8px",
                                              "borderLeft":"3px solid #1D9E75"}),

        ], id="sidebar-stats", style={"display":"none","overflowY":"auto","flex":"1"}),

        # ── Reset button always at bottom ──
        html.Div([
            html.Button("↺  Reset Analysis", id="reset-btn", className="btn-analyze",
                        style={"margin":"16px","width":"calc(100% - 32px)",
                               "background":"rgba(255,255,255,0.05)","fontSize":"12px"}),
        ], style={"borderTop":"1px solid var(--glass-border)","paddingTop":"8px","marginTop":"auto"})

    ], className="sidebar", style={
        "width": "260px", "position": "fixed", "top": "0", "bottom": "0", "left": "0",
        "background": "rgba(10,10,10,0.9)", "borderRight": "1px solid var(--glass-border)",
        "backdropFilter": "blur(40px)", "zIndex": "100", "display": "flex",
        "flexDirection": "column", "overflowY": "hidden"
    }),

    # ── Main Content Area ──
    html.Div([
        
        # ── Header ──
        html.Div([
            html.Div([
                html.Span("DASHBOARD", style={"color":"var(--text-secondary)"}),
                html.Span(" / ", style={"margin":"0 8px","opacity":"0.3"}),
                html.Span("VISION PIPELINE", id="header-breadcrumb", style={"color":"#fff","fontWeight":"500"}),
            ], style={"fontFamily":"JetBrains Mono","fontSize":"11px"}),
            html.Div(id="live-clock", style={"fontFamily":"JetBrains Mono","fontSize":"11px","color":"var(--text-secondary)"}),
            dcc.Interval(id="clock-interval", interval=1000, n_intervals=0)
        ], style={
            "height": "60px", "borderBottom": "1px solid var(--glass-border)",
            "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "0 40px"
        }),

        # ── Dynamic Content ──
        html.Div([
            
            # Stage: UPLOAD
            html.Div(id="stage-upload", children=[
                html.Div([
                    html.Div([
                        html.Div([html.Span(className="hero-dot"), "INPUT SELECTION"], className="hero-label"),
                        html.H2("Ready for Acquisition", style={"fontSize":"32px","fontWeight":"700"}),
                        html.P("Upload match recording for high-fidelity spatial analysis.", className="hero-sub"),
                    ], style={"marginBottom":"40px"}),
                    
                    html.Div([
                        dcc.Upload(
                            id="video-upload",
                            children=html.Div([
                                html.Div("↗", className="upload-icon"),
                                html.Div("Load Local Media", className="upload-title"),
                                html.Div("MP4 / AVI / MOV (Max 2GB)", className="upload-sub"),
                            ]),
                            className="upload-zone",
                            accept="video/*",
                            max_size=2 * 1024 * 1024 * 1024,
                        ),
                    ], className="upload-container"),
                    
                    html.Div(id="file-preview-area"),
                    html.Button("START ANALYTIC ENGINE", id="start-btn", className="btn-analyze", disabled=True),
                ], style={"maxWidth":"600px","margin":"80px auto"}),
            ]),

            # Stage: PROCESSING
            html.Div(id="stage-processing", style={"display":"none"}, children=[
                html.Div([
                    html.Div([
                        html.Div("NEURAL PIPELINE ACTIVE", className="hero-label"),
                        html.H2("Synthesizing Vision Data", style={"fontSize":"32px","fontWeight":"700"}),
                    ], style={"marginBottom":"30px"}),
                    
                    html.Div([
                        html.Div(id="step-list"),
                        html.Div(className="prog-track", children=html.Div(id="prog-fill", className="prog-fill", style={"width":"0%"})),
                        html.Div([
                            html.Span("TOTAL COMPLETION"),
                            html.Span("0%", id="pct-label"),
                        ], style={"display":"flex","justifyContent":"space-between","fontSize":"12px","fontFamily":"JetBrains Mono","marginTop":"10px"}),
                    ], className="pro-card-outer", style={"padding":"24px"}),
                    
                    html.Div(id="log-box", className="log-box"),
                ], style={"maxWidth":"800px","margin":"40px auto"}),
            ]),

            # Stage: RESULT
            html.Div(id="stage-result", style={"display":"none"}, children=[
                # Dual Video Grid
                html.Div([
                    # Left: Original
                    html.Div([
                        html.Div([
                            html.Span("RAW FEED", className="stat-label", style={"margin":"0"}),
                            html.Span("01", style={"fontFamily":"JetBrains Mono","opacity":"0.3"}),
                        ], style={"display":"flex","justifyContent":"space-between","padding":"12px 20px","borderBottom":"1px solid var(--glass-border)"}),
                        html.Video(id="original-video", controls=True, style={"width":"100%","borderRadius":"0 0 16px 16px"}),
                    ], className="pro-card-inner"),
                    
                    # Right: Analyzed
                    html.Div([
                        html.Div([
                            html.Span("ANALYTIC OVERLAY", className="stat-label", style={"margin":"0","color":"var(--accent)"}),
                            html.Span("02", style={"fontFamily":"JetBrains Mono","opacity":"0.3"}),
                        ], style={"display":"flex","justifyContent":"space-between","padding":"12px 20px","borderBottom":"1px solid var(--glass-border)"}),
                        html.Video(id="result-video", controls=True, style={"width":"100%","borderRadius":"0 0 16px 16px"}),
                    ], className="pro-card-inner"),
                ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"20px","marginBottom":"30px"}),

                # Metrics Grid
                html.Div([
                    html.Div([
                        html.Div([
                            html.Button("KINEMATICS", id="tab-players", className="tab-btn active"),
                            html.Button("TRAJECTORY", id="tab-ball", className="tab-btn"),
                            html.Button("TOPOGRAPHY", id="tab-court", className="tab-btn"),
                        ], style={"display":"flex","gap":"10px","padding":"0 20px","borderBottom":"1px solid var(--glass-border)"}),
                        html.Div(id="tab-content", style={"padding":"24px"}),
                    ], className="pro-card-inner"),
                ], className="pro-card-outer"),
            ]),

        ], style={"padding":"40px"})

    ], style={"marginLeft":"260px","minHeight":"100vh"})
])


# ── Helpers ───────────────────────────────────────────────────────────────────
def format_bytes(b):
    if b < 1024 * 1024:
        return f"{b/1024:.1f} KB"
    return f"{b/1024/1024:.1f} MB"


def run_pipeline(job_id: str, input_path: str, output_path: str):
    """Runs mock progress animation then invokes the real pipeline."""
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
    # Animate up to step 5 (Analytic Synthesis = 85%) — hold last step for real work
    MOCK_STEPS = PIPELINE_STEPS[:-1]
    log_per_step = max(1, len(log_lines) // len(PIPELINE_STEPS))

    for idx, (step_name, step_desc, pct) in enumerate(MOCK_STEPS):
        jobs[job_id]["step"]   = idx
        jobs[job_id]["status"] = "running"
        jobs[job_id]["pct"]    = max(0, pct - 12)

        start = idx * log_per_step
        for li in range(start, min(start + log_per_step, len(log_lines))):
            time.sleep(0.3)
            cls, txt = log_lines[li]
            jobs[job_id]["log"].append((cls, txt))

        time.sleep(0.5)
        jobs[job_id]["pct"] = pct

    # ── Activate final step: "Broadcast Rendering" ────────────────────────────
    final_idx = len(PIPELINE_STEPS) - 1
    jobs[job_id]["step"]   = final_idx
    jobs[job_id]["status"] = "running"
    jobs[job_id]["pct"]    = 88   # hold at 88% while real work runs
    jobs[job_id]["log"].append(("info", "[render] Broadcast rendering — PIL overlay pass…"))

    # ── REAL PIPELINE ──────────────────────────────────────────────────────────
    from process_tennis_video import process_tennis_video
    stats = process_tennis_video(input_path, output_path)

    # ── Mark complete ──────────────────────────────────────────────────────────
    jobs[job_id]["pct"]         = 100
    jobs[job_id]["step"]        = final_idx
    jobs[job_id]["status"]      = "done"
    jobs[job_id]["output_path"] = output_path
    jobs[job_id]["stats"]       = stats
    jobs[job_id]["log"].append(("info", "[done] Pipeline complete ✓"))



# ── Callback: handle upload ───────────────────────────────────────────────────
@app.callback(
    Output("file-preview-area", "children"),
    Output("start-btn", "disabled"),
    Output("job-id-store", "data"),
    Input("video-upload", "contents"),
    State("video-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
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
    Output("stage-store", "data", allow_duplicate=True),
    Output("poll-interval", "disabled", allow_duplicate=True),
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
    Output("stage-upload",     "style", allow_duplicate=True),
    Output("stage-processing", "style", allow_duplicate=True),
    Output("stage-result",     "style", allow_duplicate=True),
    Output("step-list",        "children"),
    Output("prog-fill",        "style"),
    Output("pct-label",        "children"),
    Output("log-box",          "children"),
    Output("poll-interval",    "disabled", allow_duplicate=True),
    Output("stage-store",      "data",     allow_duplicate=True),
    Output("result-video",     "src"),
    Output("original-video",   "src"),
    Output("stats-store",      "data"),
    Output("stat-ball-shots-side",  "children"),
    Output("stat-max-speed-side",   "children"),
    Output("stat-p1-shots-side",    "children"),
    Output("stat-p2-shots-side",    "children"),
    Output("stat-avg-speed-side",   "children"),
    Output("stat-kps-side",         "children"),
    Output("stat-frames-side",      "children"),
    Output("sidebar-stats",    "style"),
    Output("sidebar-status",   "children"),
    Input("poll-interval",     "n_intervals"),
    State("stage-store",       "data"),
    State("job-id-store",      "data"),
    prevent_initial_call=True,
)
def poll_state(n, stage, job_id):
    show  = {"display": "block"}
    hide  = {"display": "none"}
    blank = dash.no_update

    status_ready = html.Div([
        html.Div(className="proc-dot", style={"background":"#27c93f","width":"8px","height":"8px"}),
        html.Span("KERNEL: READY", style={"fontSize":"10px","fontFamily":"JetBrains Mono"})
    ], style={"display":"flex","alignItems":"center","gap":"8px","padding":"10px 20px"})

    status_processing = html.Div([
        html.Div(className="proc-dot", style={"background":"#ffbd2e","width":"8px","height":"8px","animation":"pulse 1s infinite"}),
        html.Span("KERNEL: ACTIVE", style={"fontSize":"10px","fontFamily":"JetBrains Mono"})
    ], style={"display":"flex","alignItems":"center","gap":"8px","padding":"10px 20px"})

    if stage == "upload":
        nu = dash.no_update
        return show, hide, hide, [], {"width": "0%"}, "0%", [], True, "upload", "", "", {}, "–", "–", "–", "–", "–", "–", "–", hide, status_ready

    if stage == "processing" and job_id and job_id in jobs:
        job = jobs[job_id]
        pct = job["pct"]

        # Build step rows
        step_rows = []
        for si, (sname, sdesc, _) in enumerate(PIPELINE_STEPS):
            if si < job["step"]:
                cls, badge_txt = "done", "DONE"
            elif si == job["step"] and job["status"] == "running":
                cls, badge_txt = "running", "ACTIVE"
            else:
                cls, badge_txt = "pending", "WAIT"

            icons = ["📹","🧍","🎾","🏟️","🗺️","⚡","📊"]
            step_rows.append(html.Div([
                html.Div(icons[si], className=f"step-icon {cls}"),
                html.Div([
                    html.Div(sname, className="step-name", style={"fontSize":"13px"}),
                    html.Div(sdesc, className="step-desc", style={"fontSize":"10px"}),
                ], style={"flex": "1"}),
                html.Span(badge_txt, style={"fontSize":"9px","fontFamily":"JetBrains Mono","opacity":"0.5"}),
            ], className="step-row", style={"padding":"10px 0"}))

        # Build log
        log_children = [html.Div(f"> {txt}", style={"color": "#1D9E75" if cls=="info" else "#d29922"}) for cls, txt in job["log"][-20:]]

        if job["status"] == "done":
            output_path = job["output_path"]
            video_src = ""
            if output_path and os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                video_src = f"data:video/mp4;base64,{data}"

            orig_src = ""
            input_path = job.get("input_path", "")
            if input_path and os.path.exists(input_path):
                with open(input_path, "rb") as f:
                    orig_data = base64.b64encode(f.read()).decode()
                orig_src = f"data:video/mp4;base64,{orig_data}"

            stats = job.get("stats", {})
            ball_shots  = str(stats.get("ball_shots", 0))
            max_spd     = f"{stats.get('max_ball_speed', 0):.0f}"
            p1_shots    = str(stats.get("player_1_shots", 0))
            p2_shots    = str(stats.get("player_2_shots", 0))
            avg_spd     = f"{stats.get('avg_ball_speed', 0):.0f}"
            kps         = str(stats.get("court_keypoints", 14))
            frames      = str(stats.get("total_frames", "—"))
            return (hide, hide, show,
                    step_rows, {"width": "100%"}, "100%",
                    log_children, True, "result", video_src, orig_src,
                    stats, ball_shots, max_spd, p1_shots, p2_shots,
                    avg_spd, kps, frames,
                    {"display":"block","overflowY":"auto","flex":"1"}, status_ready)

        return (hide, show, hide,
                step_rows, {"width": f"{pct}%"}, f"{pct}%",
                log_children, False, "processing", "", "", {}, "–", "–", "–", "–", "–", "–", "–", hide, status_processing)

    if stage == "result":
        nu = dash.no_update
        return hide, hide, show, nu, nu, nu, nu, True, nu, nu, nu, nu, nu, nu, nu, nu, nu, nu, nu, {"display":"block","overflowY":"auto","flex":"1"}, status_ready

    return show, hide, hide, [], {"width": "0%"}, "0%", [], True, "upload", "", "", {}, "–", "–", "–", "–", "–", "–", "–", hide, status_ready


# ── Callback: live clock ───────────────────────────────────────────────────────
@app.callback(
    Output("live-clock", "children"),
    Input("clock-interval", "n_intervals")
)
def update_clock(n):
    return time.strftime("%H:%M:%S | %d %b %Y")


# ── Callback: tab switching ────────────────────────────────────────────────────
@app.callback(
    Output("tab-content",  "children"),
    Output("tab-players",  "className"),
    Output("tab-ball",     "className"),
    Output("tab-court",    "className"),
    Input("tab-players",   "n_clicks"),
    Input("tab-ball",      "n_clicks"),
    Input("tab-court",     "n_clicks"),
    Input("stats-store",   "data"),
    prevent_initial_call=False,
)
def switch_tab(p, b, c, stats):
    stats = stats or {}
    ctx = callback_context
    if not ctx.triggered:
        active = "players"
    else:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        active = "players" if prop_id == "stats-store" else prop_id.replace("tab-", "")

    def cls(t): return "tab-btn active" if t == active else "tab-btn"

    def _err(e):
        return html.Div([
            html.Div("⚠ Render Error", style={"color":"#ff5555","fontFamily":"JetBrains Mono",
                                              "fontSize":"12px","marginBottom":"8px"}),
            html.Pre(str(e), style={"color":"#8b949e","fontSize":"11px","whiteSpace":"pre-wrap"})
        ], style={"padding":"24px","background":"rgba(255,0,0,0.05)",
                  "borderRadius":"12px","border":"1px solid rgba(255,85,85,0.2)"})

    try:
        if active == "players":
            content = build_kinematics(stats)
        elif active == "ball":
            content = build_trajectory(stats)
        else:
            content = build_topography(stats)
    except Exception as e:
        content = _err(e)

    return content, cls("players"), cls("ball"), cls("court")


# ── Callback: topography filters ──────────────────────────────────────────────
@app.callback(
    Output("tab-content", "children", allow_duplicate=True),
    Input("topo-shot-filter",    "value"),
    Input("topo-outcome-filter", "value"),
    State("stats-store", "data"),
    prevent_initial_call=True,
)
def topo_filter(shot_f, outcome_f, stats):
    return build_topography(stats or {}, shot_f or "All", outcome_f or "All")


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
    app.run(debug=True, port=8080)
