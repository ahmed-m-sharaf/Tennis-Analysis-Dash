<div align="center">

<img src="assets/ITI.png" alt="T-Board Logo" width="100"/>

# T-Board · Tennis Vision Dashboard

**Production-grade AI sports analytics dashboard**  
Real-time player tracking · Ball kinematics · Tactical court mapping

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Dash 4.0](https://img.shields.io/badge/Dash-4.0-00D09C?logo=plotly)](https://dash.plotly.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF4B4B)](https://ultralytics.com)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📸 Preview

> Upload any tennis match video and get a full broadcast-quality analytics report in seconds.

| Processing Pipeline | Analytics Dashboard |
|---|---|
| 7-step live progress bar | Kinematics · Trajectory · Topography |

---

## 🏗️ Architecture

```
t-board/
│
├── app.py                      # Dash server — layout, routing, callbacks
├── analytics_tabs.py           # Three-pillar analytics: Kinematics · Trajectory · Topography
├── process_tennis_video.py     # 2-pass CV pipeline orchestrator
│
├── trackers/                   # AI detection & tracking modules
│   ├── player_tracker.py       # YOLOv8x person detection + player selection
│   └── ball_tracker.py         # YOLOv5 ball detection + shot event detection
│
├── court_line_detector/        # CNN-based court keypoint regression
│   └── court_line_detector.py
│
├── mini_court/                 # Perspective-normalised 2D court mapper
│   └── mini_court.py
│
├── utils/                      # Shared utility library
│   ├── bbox_utils.py           # Bounding-box geometry helpers
│   ├── conversions.py          # Pixel ↔ metre coordinate transforms
│   ├── video_utils.py          # OpenCV read/write helpers
│   └── player_stats_drawer_utils.py  # PIL broadcast overlay renderer
│
├── constants/                  # Project-wide constants (court dimensions, etc.)
│   └── __init__.py
│
├── assets/                     # Static web assets served by Dash
│   ├── styles.css              # Design system — Tech-Noir / Glassmorphism
│   └── ITI.png                 # Brand logo
│
├── models/                     # Pre-trained model weights (not tracked by git)
│   ├── yolov8x.pt              # Player detection backbone
│   ├── yolo5_last.pt           # Ball detection model
│   └── keypoints_model.pth     # Court keypoint regression model
│
├── analysis/                   # Jupyter notebooks for offline EDA
│   └── ball_analysis.ipynb
│
├── input_video/                # Sample input videos
├── uploads/                    # Runtime upload directory (git-ignored)
├── outputs/                    # Processed video outputs (git-ignored)
│
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Ruff linting configuration
└── .gitignore
```

---

## ⚙️ Technology Stack

| Layer | Technology |
|---|---|
| **Web Framework** | [Dash 4.0](https://dash.plotly.com) (Flask/React) |
| **Visualisation** | [Plotly](https://plotly.com/python/) — Scatter, Radar, Heatmap, Histogram2dContour |
| **Computer Vision** | [OpenCV](https://opencv.org) — frame decode, annotation, encode |
| **Player Detection** | [YOLOv8x](https://ultralytics.com) — transformer-based person detection |
| **Ball Detection** | YOLOv5 (custom fine-tuned on tennis datasets) |
| **Court Mapping** | Custom CNN (ResNet backbone) — 14-keypoint regression |
| **Overlay Rendering** | [Pillow](https://pillow.readthedocs.io) — anti-aliased glassmorphic stats panel |
| **Data** | [Pandas](https://pandas.pydata.org) · [NumPy](https://numpy.org) |
| **Accelerator** | Auto-detects **MPS** (Apple Silicon) → CUDA → CPU |

---

## 🚀 Quick Start

### 1 · Clone
```bash
git clone https://github.com/ahmed-m-sharaf/Tennis-Analysis-Dash.git
cd Tennis-Analysis-Dash
```

### 2 · Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3 · Download models

Place the following files into the `models/` directory:

| File | Source |
|---|---|
| `yolov8x.pt` | Auto-downloaded by Ultralytics on first run |
| `yolo5_last.pt` | [Google Drive](https://drive.google.com/file/d/1UZwiG1jkWgce9lNhxJ2L0NVjX1vGM05U/view?usp=sharing) |
| `keypoints_model.pth` | [Google Drive](https://drive.google.com/file/d/1QrTOF1ToQ4plsSZbkBs3zOLkVt3MBlta/view?usp=sharing) |

### 4 · Run
```bash
python app.py
# → http://localhost:8080
```

---

## 🧠 Analytics Engine — Three Pillars

### 1 · Kinematics _(Players' Physics)_
- Speed-over-time burst & recovery curves
- Cumulative distance covered per player
- Multi-axis performance radar (Shot Speed, Movement, Volume, Recovery, Consistency)

### 2 · Trajectory _(Ball's Physics)_
- 3D flight-path arc with net clearance visualisation
- Velocity decay model after bounce
- Launch angle, topspin RPM estimate, avg net clearance margin

### 3 · Topography _(Spatial Tactics)_
- Shot landing scatter — grouped by type (Serve / Forehand / Backhand) & outcome (Winner / Error / In Play)
- Court coverage density heatmap (Histogram2dContour)
- Deep-court vs net-zone tactical breakdown
- Live filters: Shot Type × Outcome

---

## 📦 Pipeline Steps

```
[1] Spatial Decoupling   → 2-pass pipeline init, frame buffering
[2] Vision Engine        → YOLOv8x player detection (all frames)
[3] Trajectory Kinematics → Ball detection + Bézier interpolation
[4] Geometric Mapping    → 14-keypoint court normalisation
[5] Metre Transformation → Pixel → metre coordinate conversion
[6] Analytic Synthesis   → Speed / distance / shot statistics
[7] Broadcast Rendering  → PIL overlay + OpenCV video encode
```

---

## 🤝 Contributing

```bash
# Create a feature branch
git checkout -b feat/my-feature

# Lint before committing
ruff check . --fix

# Open a PR against main
```

---

## 📄 License

MIT © 2025 Ahmed M. Sharaf — ITI Data Science Graduate
