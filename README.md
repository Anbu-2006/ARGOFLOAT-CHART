# 🌊 FloatChart

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Query ocean data using plain English.**

[Live Demo](https://argofloat-chart.onrender.com) · [Report Bug](https://github.com/Anbu-2006/ARGOFLOAT-CHART/issues) · [Request Feature](https://github.com/Anbu-2006/ARGOFLOAT-CHART/issues)

</div>

---

## About

FloatChart lets you explore ARGO float oceanographic data through natural language queries. Instead of writing complex SQL, just ask questions like *"What's the average temperature in the Bay of Bengal?"* and get instant visualizations.

**What are ARGO floats?** They're autonomous instruments drifting across the world's oceans, diving to 2000m depth to measure temperature, salinity, and pressure. Over 4,000 are currently deployed, generating millions of data points for climate research.

---

## Demo

**→ [argofloat-chart.onrender.com](https://argofloat-chart.onrender.com)**

The demo includes 1.5M+ records covering global oceans from 2020-2026.

> **Note:** The demo runs on Render's free tier, so there may be a ~30s cold start delay if the server has been idle.

---

## Features

- **Natural language queries** — Ask questions in plain English
- **Interactive maps** — Visualize float positions and trajectories
- **Multiple chart types** — Time series, scatter plots, depth profiles
- **Voice input** — Speak your queries (Chrome/Edge)
- **Dark/Light themes** — Easy on the eyes
- **Keyboard shortcuts** — Press `?` to see all shortcuts
- **Export data** — Download as CSV or JSON
- **Works offline** — Installable as a PWA

---

## Quick Start

### Option 1: Use the Demo

Just visit [argofloat-chart.onrender.com](https://argofloat-chart.onrender.com) — no setup needed.

### Option 2: Run Locally

**Prerequisites:** Python 3.10+, PostgreSQL

```bash
# Clone the repo
git clone https://github.com/Anbu-2006/ARGOFLOAT-CHART.git
cd ARGOFLOAT-CHART/ARGO_CHATBOT

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see .env.example)
cp .env.example .env
# Edit .env with your database URL and API keys

# Run the app
python app.py
```

Open [localhost:5000](http://localhost:5000) in your browser.

---

## Configuration

Create a `.env` file in the `ARGO_CHATBOT` folder:

```env
# Database (required)
DATABASE_URL=postgresql://user:password@localhost:5432/argo_db

# AI Provider (at least one required)
GROQ_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here
```

The app supports multiple LLM providers and will automatically use whichever key you provide.

---

## Project Structure

```
ARGOFLOAT-CHART/
├── ARGO_CHATBOT/           # Web application
│   ├── app.py              # Flask server
│   ├── brain.py            # AI query processing
│   ├── sql_builder.py      # SQL generation
│   ├── requirements.txt
│   └── static/             # Frontend assets
│       ├── index.html
│       ├── css/
│       └── js/
│
└── DATA_GENERATOR/         # Tools for fetching ARGO data
    ├── gui.py              # Desktop GUI
    ├── fetch_argo_data.py  # CLI tool
    └── setup_local_db.py   # Database setup
```

---

## Sample Queries

Try these in the app:

| Type | Example |
|------|---------|
| **Location** | "Show floats near Chennai" |
| **Statistics** | "Average temperature in Arabian Sea" |
| **Time-based** | "Temperature trends in 2024" |
| **Specific float** | "Trajectory of float 2902115" |
| **Comparison** | "Salinity vs temperature in Bay of Bengal" |

---

## API

The app exposes a simple REST API:

```
GET  /api/status          # Health check
POST /api/query           # Natural language query
GET  /api/nearest_floats  # Find floats near coordinates
GET  /api/float_trajectory/<id>  # Get float path
```

Example:
```bash
curl -X POST https://argofloat-chart.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "average temperature in indian ocean"}'
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Send query |
| `Ctrl + K` | Command palette |
| `Ctrl + D` | Toggle theme |
| `Ctrl + E` | Export data |
| `?` | Show all shortcuts |

---

## Deployment

### Render (Recommended)

1. Fork this repo
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repo
4. Set environment variables in Render dashboard
5. Deploy

The included `Procfile` handles the rest.

### Other Platforms

Works with any platform that supports Python/Flask:
- Heroku
- Railway
- DigitalOcean App Platform
- Your own VPS

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask, SQLAlchemy |
| AI | LangChain + Groq/OpenAI/Gemini |
| Database | PostgreSQL (Supabase for cloud) |
| Frontend | Vanilla JS, Leaflet.js, Chart.js |
| Data Source | NOAA ERDDAP |

---

## Known Limitations

- **Demo data is static** — The live demo uses a snapshot of ARGO data
- **GPS accuracy** — Some float markers may appear near coastlines due to ~10-50m GPS error
- **Cold starts** — Free tier hosting has idle timeouts

For real-time data updates, run locally with the DATA_GENERATOR tools.

---

## Contributing

Contributions welcome! Feel free to:

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [ARGO Program](https://argo.ucsd.edu/) for the ocean observation network
- [ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/) for data access
- [Groq](https://groq.com/) for fast LLM inference

---

<div align="center">

Built by [@Anbu-2006](https://github.com/Anbu-2006)

If this helped you, consider giving it a ⭐

</div>
