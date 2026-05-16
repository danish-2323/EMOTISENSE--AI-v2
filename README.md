# EMOTISENSE AI 🧠
**Multimodal Emotion Recognition — React + FastAPI**

Real-time emotion monitoring combining facial detection and audio stress analysis.
Custom React frontend replaces Streamlit for a professional, responsive UI.

---

## 🗂 Project Structure

```
EMOTISENSE-AI/
├── backend/
│   └── server.py               # FastAPI server (WebSocket + REST)
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # Root — WebSocket, state, routing
│       ├── styles/
│       │   └── globals.css
│       └── components/
│           ├── Sidebar.jsx     # Navigation + session controls
│           ├── Dashboard.jsx   # Live monitoring page
│           ├── MetricCard.jsx  # Stress / Engagement / Confidence / Confusion
│           ├── StressGauge.jsx # SVG arc gauge
│           ├── TimelineChart.jsx # Recharts live chart
│           └── SessionReport.jsx # Report + CSV/PDF export
├── src/                        # Your existing ML pipeline (unchanged)
│   ├── webcam/
│   ├── audio/
│   ├── fusion/
│   ├── logger/
│   ├── fallback/
│   ├── config.py
│   └── utils.py
└── requirements.txt
```

---

## 🚀 Setup

### 1 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2 — Install frontend dependencies
```bash
cd frontend
npm install
```

### 3 — Run both servers

**Terminal 1 — Backend (FastAPI)**
```bash
uvicorn backend.server:app --reload --port 8000
```

**Terminal 2 — Frontend (React + Vite)**
```bash
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

---

## ⚙️ How It Works

```
Browser (React)  ←── WebSocket ──→  FastAPI  ←──→  src/ ML pipeline
```

- FastAPI runs your existing emotion pipeline every ~1 second
- Live data is streamed to React via WebSocket — no page refresh
- REST endpoints handle session start/stop, CSV + PDF export
- Falls back to simulation mode automatically if camera/mic unavailable

---

## 🎨 UI Design

- **Font:** DM Sans (body) + DM Mono (metrics/numbers)
- **Palette:** Off-white background, charcoal text, calm blue accent (`#1D4ED8`)
- **Components:** Metric cards, SVG arc stress gauge, live Recharts timeline, emotion bar readouts
- **Feel:** Clean, clinical, professional — like a monitoring terminal

---

## 📡 API Reference

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| GET    | `/health`             | Backend status                 |
| POST   | `/session/start`      | Start session `{ simulation }` |
| POST   | `/session/stop`       | Stop + get stats               |
| GET    | `/session/stats`      | Current session stats          |
| GET    | `/session/export/csv` | Download CSV                   |
| POST   | `/session/export/pdf` | Download PDF report            |
| WS     | `/ws/stream`          | Live emotion stream (1 fps)    |

---

## 👨‍💻 Team PRIMELOGIX
B.Tech AI & Data Science · SRM IST × NOOBTRON Hackfest
