"""
analytics_tabs.py — Expert analytics pillar renderers
Three pillars: Kinematics | Trajectory | Topography
"""
import random
import math
import plotly.graph_objects as go
from dash import dcc, html

# ── shared layout helpers ──────────────────────────────────────────────────────
_BG   = "rgba(0,0,0,0)"
_GRID = "rgba(255,255,255,0.06)"
_FONT = dict(color="#8b949e", family="JetBrains Mono", size=10)
_MAR  = dict(l=44, r=20, t=28, b=28)

def _card(children, style=None):
    s = {"background":"rgba(255,255,255,0.02)","border":"1px solid rgba(255,255,255,0.08)",
         "borderRadius":"16px","padding":"20px"}
    if style: s.update(style)
    return html.Div(children, style=s)

def _label(txt):
    return html.Div(txt, style={"fontFamily":"JetBrains Mono","fontSize":"9px",
                                "letterSpacing":"2px","color":"#8b949e","marginBottom":"6px"})

def _kpi(label, val, unit="", color="#fff"):
    return _card([
        _label(label),
        html.Div([
            html.Span(val, style={"fontFamily":"Space Grotesk","fontSize":"28px",
                                  "fontWeight":"700","color":color}),
            html.Span(f" {unit}", style={"fontSize":"13px","color":"#8b949e"}) if unit else "",
        ])
    ])

def _graph(fig, h=220):
    return dcc.Graph(figure=fig, config={"displayModeBar":False},
                     style={"height":f"{h}px"})

def _fig_base(h=220):
    fig = go.Figure()
    fig.update_layout(paper_bgcolor=_BG, plot_bgcolor=_BG, font=_FONT,
                      margin=_MAR, height=h,
                      xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
                      yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
                      legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)))
    return fig

# ── seeded synthetic data so charts look consistent ───────────────────────────
rng = random.Random(42)

def _speed_series(n=40, base=3.5, spike=8.2):
    pts = []
    for i in range(n):
        v = base + rng.gauss(0, 0.8)
        if i % 7 == 0: v = spike + rng.gauss(0, 0.4)
        pts.append(max(0, v))
    return pts

def _distance_series(n=40):
    cum, pts = 0.0, []
    for _ in range(n):
        cum += rng.uniform(0.3, 1.2)
        pts.append(round(cum, 2))
    return pts

def _ball_arc(max_spd):
    xs = [i*0.25 for i in range(29)]
    ys = []
    for x in xs:
        h = -4*(x-3.5)**2 + (0.6 + max_spd*0.003)
        ys.append(max(0, h))
    return xs, ys

def _velocity_decay(max_spd):
    xs = [0, 0.05, 0.15, 0.3, 0.5, 0.8, 1.2, 1.7, 2.3, 3.0]
    ys = [max_spd * math.exp(-0.55*x) for x in xs]
    return xs, ys

def _shot_scatter(n=80):
    shots = []
    for _ in range(n):
        stype = rng.choice(["Serve", "Forehand", "Backhand"])
        outcome = rng.choice(["Winner", "In Play", "In Play", "In Play", "Error"])
        if stype == "Serve":
            x = rng.gauss(0, 2.5); y = rng.uniform(18, 23.7)
        elif stype == "Forehand":
            x = rng.gauss(2, 2); y = rng.uniform(14, 23.7)
        else:
            x = rng.gauss(-2, 2); y = rng.uniform(14, 23.7)
        shots.append({"x":round(x,2), "y":round(y,2), "type":stype, "outcome":outcome})
    return shots

SHOTS = _shot_scatter()


# ══════════════════════════════════════════════════════════════════════════════
# PILLAR 1 — KINEMATICS
# ══════════════════════════════════════════════════════════════════════════════
def build_kinematics(stats):
    p1_spd = stats.get("player_1_avg_shot_speed",  136.0) or 136.0
    p1_mov = stats.get("player_1_avg_player_speed",  6.8) or 6.8
    p1_sho = stats.get("player_1_shots", 24) or 24
    p2_spd = stats.get("player_2_avg_shot_speed",  128.0) or 128.0
    p2_mov = stats.get("player_2_avg_player_speed",  5.9) or 5.9
    p2_sho = stats.get("player_2_shots", 22) or 22

    n = 40
    p1_spd_s = _speed_series(n, 3.2, p1_mov*1.4)
    p2_spd_s = _speed_series(n, 2.8, p2_mov*1.3)
    p1_dis_s = _distance_series(n)
    p2_dis_s = _distance_series(n)
    frames   = list(range(n))

    # — Speed over time —
    spd_fig = _fig_base(200)
    spd_fig.add_trace(go.Scatter(x=frames, y=p1_spd_s, name="P1",
        line=dict(color="#1D9E75", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(29,158,117,0.08)"))
    spd_fig.add_trace(go.Scatter(x=frames, y=p2_spd_s, name="P2",
        line=dict(color="#D29922", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(210,153,34,0.08)"))
    spd_fig.update_layout(xaxis_title="Frame", yaxis_title="Speed (m/s)")

    # — Distance covered —
    dis_fig = _fig_base(200)
    dis_fig.add_trace(go.Scatter(x=frames, y=p1_dis_s, name="P1",
        line=dict(color="#1D9E75", width=2, dash="solid"),
        fill="tonexty", fillcolor="rgba(29,158,117,0.05)"))
    dis_fig.add_trace(go.Scatter(x=frames, y=p2_dis_s, name="P2",
        line=dict(color="#D29922", width=2, dash="dot")))
    dis_fig.update_layout(xaxis_title="Frame", yaxis_title="Distance (m)")

    # — Radar —
    rad_fig = _fig_base(260)
    cats = ["Shot Speed", "Move Speed", "Shot Volume", "Recovery", "Consistency"]
    p1_vals = [p1_spd/200, p1_mov/10, p1_sho/50, 0.72, 0.81]
    p2_vals = [p2_spd/200, p2_mov/10, p2_sho/50, 0.65, 0.77]
    scale = 100
    rad_fig.add_trace(go.Scatterpolar(r=[v*scale for v in p1_vals]+[p1_vals[0]*scale],
        theta=cats+[cats[0]], fill="toself", name="Player 1",
        line=dict(color="#1D9E75", width=2), fillcolor="rgba(29,158,117,0.15)"))
    rad_fig.add_trace(go.Scatterpolar(r=[v*scale for v in p2_vals]+[p2_vals[0]*scale],
        theta=cats+[cats[0]], fill="toself", name="Player 2",
        line=dict(color="#D29922", width=2), fillcolor="rgba(210,153,34,0.12)"))
    rad_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100], gridcolor=_GRID,
                                   tickfont=dict(size=8)),
                   angularaxis=dict(gridcolor=_GRID),
                   bgcolor=_BG))

    # — KPI row —
    stats_row = html.Div([
        _kpi("P1 PEAK SHOT SPD",  f"{p1_spd:.0f}", "km/h", "#1D9E75"),
        _kpi("P2 PEAK SHOT SPD",  f"{p2_spd:.0f}", "km/h", "#D29922"),
        _kpi("P1 MOVE SPD",       f"{p1_mov:.1f}", "m/s",  "#1D9E75"),
        _kpi("P2 MOVE SPD",       f"{p2_mov:.1f}", "m/s",  "#D29922"),
        _kpi("P1 SHOTS",          str(p1_sho), "",  "#1D9E75"),
        _kpi("P2 SHOTS",          str(p2_sho), "",  "#D29922"),
    ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"10px","marginBottom":"20px"})

    rows = html.Div([
        stats_row,
        html.Div([
            _card([_label("SPEED OVER TIME — BURST & RECOVERY"), _graph(spd_fig, 200)]),
            _card([_label("CUMULATIVE DISTANCE COVERED (m)"),   _graph(dis_fig, 200)]),
        ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px","marginBottom":"16px"}),
        _card([_label("PERFORMANCE RADAR — MULTI-AXIS COMPARISON"), _graph(rad_fig, 260)]),
    ])
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# PILLAR 2 — TRAJECTORY
# ══════════════════════════════════════════════════════════════════════════════
def build_trajectory(stats):
    avg_spd = stats.get("avg_ball_speed", 136.0) or 136.0
    max_spd = stats.get("max_ball_speed", 198.0) or 198.0
    min_spd = stats.get("min_ball_speed",  88.0) or 88.0

    # — Flight path arc —
    arc_fig = _fig_base(230)
    ax, ay = _ball_arc(max_spd)
    net_x = [3.5, 3.5]; net_y = [0, 0.91]
    arc_fig.add_shape(type="line", x0=3.5, x1=3.5, y0=0, y1=0.91,
        line=dict(color="#D29922", width=2, dash="dot"))
    arc_fig.add_annotation(x=3.5, y=0.95, text="NET", font=dict(size=8, color="#D29922"),
        showarrow=False)
    arc_fig.add_trace(go.Scatter(x=ax, y=ay, name="Flight Arc",
        line=dict(color="#1D9E75", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(29,158,117,0.08)"))
    arc_fig.add_trace(go.Scatter(
        x=[ax[14]], y=[max(ay)], mode="markers",
        marker=dict(size=10, color="#ffbd2e", symbol="circle"),
        name="Peak Height"))
    arc_fig.update_layout(xaxis_title="Court Length (m)", yaxis_title="Height (m)")

    # — Velocity decay after bounce —
    dec_fig = _fig_base(220)
    dx, dy   = _velocity_decay(max_spd)
    dx2, dy2 = _velocity_decay(avg_spd)
    dec_fig.add_trace(go.Scatter(x=dx, y=dy, name="Peak Shot",
        line=dict(color="#1D9E75", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(29,158,117,0.08)"))
    dec_fig.add_trace(go.Scatter(x=dx2, y=dy2, name="Avg Shot",
        line=dict(color="#D29922", width=2, shape="spline", dash="dot")))
    dec_fig.update_layout(xaxis_title="Time after bounce (s)", yaxis_title="Speed (km/h)")

    # — KPIs —
    launch_ang = round(14 + max_spd * 0.02, 1)
    net_clear  = round(0.18 + avg_spd * 0.001, 2)
    topspin    = int(1800 + max_spd * 6)

    kpi_row = html.Div([
        _kpi("PEAK VELOCITY",   f"{max_spd:.0f}", "km/h", "#1D9E75"),
        _kpi("AVG VELOCITY",    f"{avg_spd:.0f}", "km/h", "#8b949e"),
        _kpi("MIN VELOCITY",    f"{min_spd:.0f}", "km/h", "#D29922"),
        _kpi("LAUNCH ANGLE",    f"{launch_ang}",  "°",    "#1D9E75"),
        _kpi("AVG NET CLEAR",   f"{net_clear}",   "m",    "#8b949e"),
        _kpi("EST. TOPSPIN",    f"{topspin:,}",   "RPM",  "#D29922"),
    ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"10px","marginBottom":"20px"})

    rows = html.Div([
        kpi_row,
        html.Div([
            _card([_label("FLIGHT PATH ARC — NET CLEARANCE & BOUNCE HEIGHT"), _graph(arc_fig, 230)]),
            _card([_label("VELOCITY DECAY AFTER BOUNCE"),                      _graph(dec_fig, 230)]),
        ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}),
    ])
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# PILLAR 3 — TOPOGRAPHY
# ══════════════════════════════════════════════════════════════════════════════
COURT_W = 10.97  # metres half-width either side → total 10.97
COURT_L = 23.77  # metres full length

def _court_bg(fig):
    """Draw a top-down half-court outline on a figure."""
    shapes = []
    def rect(x0, y0, x1, y1, color="#3a4a3a", width=1):
        shapes.append(dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                           line=dict(color=color, width=width),
                           fillcolor="rgba(0,0,0,0)"))
    # outer
    rect(-COURT_W/2, 0, COURT_W/2, COURT_L)
    # service boxes
    rect(-COURT_W/2, COURT_L/2, 0, COURT_L)          # left service left
    rect(0, COURT_L/2, COURT_W/2, COURT_L)             # right service left
    # centre line
    shapes.append(dict(type="line", x0=0, y0=COURT_L/2, x1=0, y1=COURT_L,
                       line=dict(color="#3a4a3a", width=1)))
    # net
    shapes.append(dict(type="line", x0=-COURT_W/2, y0=COURT_L/2, x1=COURT_W/2, y1=COURT_L/2,
                       line=dict(color="#D29922", width=2, dash="dot")))
    fig.update_layout(shapes=shapes)

OUTCOME_COL = {"Winner":"#1D9E75", "In Play":"#4a9eff", "Error":"#ff5555"}
TYPE_SYM    = {"Serve":"circle", "Forehand":"square", "Backhand":"diamond"}

def build_topography(stats, shot_filter="All", outcome_filter="All"):
    filtered = [s for s in SHOTS
                if (shot_filter=="All" or s["type"]==shot_filter)
                and (outcome_filter=="All" or s["outcome"]==outcome_filter)]

    # — Scatter plot —
    scat_fig = _fig_base(380)
    scat_fig.update_layout(
        xaxis=dict(range=[-COURT_W/2-0.5, COURT_W/2+0.5], showgrid=False,
                   zeroline=False, visible=False),
        yaxis=dict(range=[-0.5, COURT_L+0.5], showgrid=False,
                   zeroline=False, visible=False),
        plot_bgcolor="#0a1a0e",
    )
    _court_bg(scat_fig)

    for stype in ["Serve","Forehand","Backhand"]:
        pts = [s for s in filtered if s["type"]==stype]
        if not pts: continue
        scat_fig.add_trace(go.Scatter(
            x=[s["x"] for s in pts], y=[s["y"] for s in pts],
            mode="markers", name=stype,
            marker=dict(
                color=[OUTCOME_COL.get(s["outcome"],"#888") for s in pts],
                size=9, symbol=TYPE_SYM[stype],
                line=dict(color="rgba(0,0,0,0.4)", width=1)
            ),
            text=[f"{s['type']}<br>{s['outcome']}" for s in pts],
            hovertemplate="%{text}<extra></extra>",
        ))

    # — Heatmap —
    if filtered:
        heat_fig = _fig_base(380)
        heat_fig.update_layout(
            xaxis=dict(range=[-COURT_W/2-0.5, COURT_W/2+0.5], showgrid=False, visible=False),
            yaxis=dict(range=[-0.5, COURT_L+0.5], showgrid=False, visible=False),
            plot_bgcolor="#0a1a0e",
        )
        _court_bg(heat_fig)
        heat_fig.add_trace(go.Histogram2dContour(
            x=[s["x"] for s in filtered],
            y=[s["y"] for s in filtered],
            colorscale=[[0,"rgba(0,0,0,0)"],[0.4,"rgba(29,158,117,0.3)"],
                        [0.7,"rgba(29,158,117,0.7)"],[1,"#1D9E75"]],
            showscale=False, ncontours=12,
            contours=dict(showlines=False),
            line=dict(width=0),
        ))
    else:
        heat_fig = _fig_base(380)
        heat_fig.add_annotation(text="No data for selection", x=0.5, y=0.5,
                                 showarrow=False, font=dict(color="#8b949e"))

    # — KPI tallies —
    winners   = sum(1 for s in filtered if s["outcome"]=="Winner")
    errors    = sum(1 for s in filtered if s["outcome"]=="Error")
    in_play   = sum(1 for s in filtered if s["outcome"]=="In Play")
    deep_pct  = round(sum(1 for s in filtered if s["y"] > 20) / max(len(filtered),1) * 100)
    net_pct   = round(sum(1 for s in filtered if s["y"] < 15) / max(len(filtered),1) * 100)

    kpi_row = html.Div([
        _kpi("TOTAL SHOTS",   str(len(filtered)), "",  "#fff"),
        _kpi("WINNERS",       str(winners),       "",  "#1D9E75"),
        _kpi("ERRORS",        str(errors),        "",  "#ff5555"),
        _kpi("IN PLAY",       str(in_play),       "",  "#4a9eff"),
        _kpi("DEEP LANDING",  f"{deep_pct}",      "%", "#1D9E75"),
        _kpi("NET-ZONE PLAY", f"{net_pct}",       "%", "#D29922"),
    ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"10px","marginBottom":"20px"})

    # — Filter controls —
    filter_bar = html.Div([
        html.Div("FILTER BY SHOT TYPE:", style={"fontFamily":"JetBrains Mono","fontSize":"9px",
            "color":"#8b949e","letterSpacing":"2px","marginRight":"8px","alignSelf":"center"}),
        dcc.RadioItems(id="topo-shot-filter",
            options=[{"label":v,"value":v} for v in ["All","Serve","Forehand","Backhand"]],
            value=shot_filter, inline=True,
            inputStyle={"marginRight":"4px","accentColor":"#1D9E75"},
            labelStyle={"marginRight":"16px","fontSize":"12px","color":"#e6edf3","cursor":"pointer"},
        ),
        html.Div("OUTCOME:", style={"fontFamily":"JetBrains Mono","fontSize":"9px",
            "color":"#8b949e","letterSpacing":"2px","marginRight":"8px","marginLeft":"20px",
            "alignSelf":"center"}),
        dcc.RadioItems(id="topo-outcome-filter",
            options=[{"label":v,"value":v} for v in ["All","Winner","In Play","Error"]],
            value=outcome_filter, inline=True,
            inputStyle={"marginRight":"4px","accentColor":"#1D9E75"},
            labelStyle={"marginRight":"16px","fontSize":"12px","color":"#e6edf3","cursor":"pointer"},
        ),
    ], style={"display":"flex","flexWrap":"wrap","alignItems":"center","padding":"14px 20px",
              "borderBottom":"1px solid rgba(255,255,255,0.08)","marginBottom":"20px",
              "background":"rgba(255,255,255,0.02)","borderRadius":"12px"})

    rows = html.Div([
        filter_bar,
        kpi_row,
        html.Div([
            _card([_label("SHOT LANDING — GROUPING BY TYPE & OUTCOME"), _graph(scat_fig, 380)]),
            _card([_label("COURT COVERAGE HEATMAP — DENSITY CONTOURS"),  _graph(heat_fig, 380)]),
        ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}),
    ])
    return rows
