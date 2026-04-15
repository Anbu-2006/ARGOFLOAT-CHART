<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A2647,25:144272,50:205295,75:2C74B3,100:0A2647&height=260&section=header&text=🌊%20FloatChart&fontSize=80&fontColor=ffffff&animation=twinkling&fontAlignY=35&desc=The%20Open%20Intelligence%20Layer%20for%20ARGO%20Ocean%20Data&descSize=22&descAlignY=58&descAlign=50" width="100%"/>

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=1000&color=2C74B3&center=true&vCenter=true&multiline=true&repeat=false&width=900&height=70&lines=Ask+questions+in+plain+English+%E2%80%94+get+instant+ocean+insights;Agent-Ready+API+%7C+46M%2B+records+%7C+100%25+Offline" alt="Typing SVG" /></a>

<br/>

<p>
<img src="https://img.shields.io/badge/🌊_Ocean_Records-46M+-0A2647?style=for-the-badge&labelColor=144272" alt="Records"/>
<img src="https://img.shields.io/badge/🔵_ARGO_Floats-4000+-205295?style=for-the-badge&labelColor=2C74B3" alt="Floats"/>
<img src="https://img.shields.io/badge/🤖_API-Agent--Ready-22c55e?style=for-the-badge&labelColor=16a34a" alt="Agent Ready"/>
<img src="https://img.shields.io/badge/⚡_Response-sub--second-f59e0b?style=for-the-badge&labelColor=d97706" alt="Speed"/>
</p>

<p>
<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Flask-2.0+-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask"/>
<img src="https://img.shields.io/badge/PostgreSQL-15+-316192?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
<img src="https://img.shields.io/badge/NVIDIA-Llama_3.3_70B-76B900?style=flat-square&logo=nvidia&logoColor=white" alt="NVIDIA NIM"/>
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="License"/>
</p>

<br/>

<a href="#-quick-start">
  <img src="https://img.shields.io/badge/⚡_GET_STARTED-5_MIN_SETUP-22c55e?style=for-the-badge&labelColor=16a34a" alt="Quick Start"/>
</a>
&nbsp;&nbsp;
<a href="#-developer-api">
  <img src="https://img.shields.io/badge/🤖_DEVELOPER_API-DOCS-2C74B3?style=for-the-badge&labelColor=144272" alt="API Docs"/>
</a>
&nbsp;&nbsp;
<a href="https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/issues">
  <img src="https://img.shields.io/badge/🐛_ISSUES-REPORT-ef4444?style=for-the-badge&labelColor=dc2626" alt="Report Bug"/>
</a>

</div>

<br/>

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">
</p>

---

<p align="center">
  <img src="assets/dashboard.png" width="100%" alt="FloatChart Dashboard Preview" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
</p>

## 🎯 What is FloatChart?

**FloatChart** is the **Open Intelligence Layer for ARGO Ocean Data** — a free, self-hostable platform that turns the world's largest ocean observation network into an instantly queryable intelligence layer. Ask questions in plain English and receive charts, maps, and data exports in seconds.

> *"The ARGO programme collects 4,000+ autonomous floats collecting 46 million+ ocean profiles. FloatChart makes every one of those measurements accessible to anyone — no oceanography PhD required."*

### 🔑 Core Principles

| Principle | Implementation |
|:----------|:--------------|
| **Open Intelligence Layer** | All data, all queries, all code — publicly accessible |
| **Agent-Ready** | Versioned REST API (`/api/v1/query`) for LLM integration |
| **Offline-First** | 100% on-device — no cloud dependency after setup |
| **Privacy-First** | No telemetry, no tracking, no raw GPS to the cloud |
| **Safety-First** | SQL Sanitizer prevents any destructive query from executing |

> **🚀 Roadmap Note:** FloatChart currently utilises local/open-weight models for basic routing, but we are actively migrating our complex, multi-step oceanographic reasoning pipeline to the **Claude 3.5/4.x family**. We are building this to be a premier MCP (Model Context Protocol) server for the Claude ecosystem.

---

## 🏗️ System Architecture

<p align="center">
  <img src="assets/architecture.png" width="100%" alt="FloatChart System Architecture" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
</p>

---

## ✨ Platform Features

<table>
<tr>
<td width="50%" valign="top">

### 💬 AI Chat Interface
> *Ask anything about ocean data*

- Natural language → SQL → charts
- Instant AI-generated data summaries
- 7 query types (statistics, proximity, profiles...)
- Export results to CSV
- Smart query suggestions

**Try:** *"Show temperature trends in Bay of Bengal for 2024"*

</td>
<td width="50%" valign="top">

### 🗺️ Interactive Map
> *Explore 4,000+ floats worldwide*

- Click anywhere to find nearby floats
- Real-time trajectory visualisation
- Date range filtering
- Float details on hover
- Depth profile charts

**Try:** *Click any point in the ocean!*

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📊 Analytics Dashboard
> *Visualise oceanographic patterns*

- Temperature time series
- Salinity distributions
- Vertical depth profiles
- Statistical summaries
- Comparative analysis

</td>
<td width="50%" valign="top">

### 🤖 Developer API
> *Integrate FloatChart into your apps*

- `POST /api/v1/query` — Natural language to data
- `GET /api/v1/tools` — Agent tool manifest
- `POST /api/v1/validate-sql` — Safety checks
- Sub-second responses
- No auth required (local)

</td>
</tr>
</table>

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">
</p>

## 🤖 Developer API

FloatChart exposes a stable, versioned REST API that makes it easy to integrate ocean intelligence into any application — including LLM agents, Jupyter notebooks, and custom dashboards.

### Quick Start

```bash
# Ask a natural language question, get structured JSON back
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show average temperature in Bay of Bengal for 2024"}'
```

**Response:**
```json
{
  "success":      true,
  "answer":       "Average temperature in Bay of Bengal (2024): 28.4°C based on 3,201 measurements.",
  "data":         [{"day": "2024-01-01", "temperature": 27.9, "salinity": 32.1}, "..."],
  "chart_type":   "line",
  "query_type":   "Time-Series",
  "sql":          "SELECT DATE_TRUNC('day', \"timestamp\") as day, AVG(...) FROM argo_data ...",
  "record_count": 365,
  "api_version":  "v1",
  "cached":       false,
  "elapsed_ms":   218.4
}
```

### API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/api/v1/query` | Natural language → structured ocean data |
| `GET`  | `/api/v1/query?query=...` | Same, via URL param |
| `GET`  | `/api/v1/tools` | Machine-readable agent tool manifest |
| `POST` | `/api/v1/validate-sql` | SQL safety checker |
| `GET`  | `/api/health` | Health check + DB status |
| `GET`  | `/api/stats` | Database statistics |

### Python Integration

```python
import requests

def ask_ocean(question: str) -> dict:
    """Query FloatChart from any Python script or agent."""
    response = requests.post(
        "http://localhost:5000/api/v1/query",
        json={"query": question, "max_rows": 500}
    )
    return response.json()

# Examples
result = ask_ocean("Find the 5 nearest floats to Chennai")
result = ask_ocean("What is the salinity in Arabian Sea this year?")
result = ask_ocean("Show depth profile of float 2902115")

print(result["answer"])
for row in result["data"]:
    print(row)
```

### 🔌 Model Context Protocol (MCP) & Agent Integration

FloatChart is designed as a native tool for the agentic ecosystem. AI agents (like Claude via the **Model Context Protocol**) can auto-discover our capabilities to query ocean data directly from their environments.

```bash
curl http://localhost:5000/api/v1/tools
```

Returns a fully compliant JSON schema describing all callable tools, enabling zero-configuration integration for autonomous researchers and terminal agents.

### Available Agent Tools (`agent_tools.py`)

| Tool | Description |
|:-----|:------------|
| `query_ocean_data(question)` | Ask any natural-language question |
| `get_floats_near_location(location, radius_km)` | Proximity search |
| `get_temperature_trend(location, year)` | Time-series for a region |
| `get_depth_profile(float_id)` | Vertical profile for one float |
| `get_database_stats()` | Database summary statistics |
| `validate_sql_safety(sql)` | Run the safety sanitizer |

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">
</p>

## 🛡️ AI Alignment & Governance Layer

FloatChart implements strict **AI alignment protocols** via a custom SQL Safety Layer (`sql_sanitizer.py`). This validates every LLM-generated query before it reaches the database, enforcing a strict **read-only contract**. This ensures that autonomous agents remain helpful and harmless, completely preventing prompt-injection-based database corruption.

### Safety Checks (7 Layers)

| # | Check | What It Prevents |
|:--|:------|:-----------------|
| 1 | **Allowlist only SELECT/WITH** | Any non-SELECT statement |
| 2 | **Blocked keyword scan** | `DROP`, `DELETE`, `INSERT`, `UPDATE`, `TRUNCATE`, `ALTER`, `GRANT`, ... |
| 3 | **No stacked statements** | SQL injection via `;`-chained queries |
| 4 | **No comment injection** | `--` and `/* */` bypass attempts |
| 5 | **LIMIT cap enforcement** | Runaway queries fetching millions of rows |
| 6 | **No system function abuse** | `pg_read_file`, `pg_sleep`, `COPY` |
| 7 | **Graceful error surface** | Every rejection includes a clear, human-readable reason |

```python
from sql_sanitizer import SQLSanitizer

# Safe query — passes all checks
result = SQLSanitizer.validate("SELECT AVG(temperature) FROM argo_data WHERE ...")
# → {"safe": True, "reason": None, "checks": {...}}

# Unsafe query — blocked immediately
result = SQLSanitizer.validate("DROP TABLE argo_data;")
# → {"safe": False, "reason": "Blocked keyword detected: DROP", "checks": {...}}
```

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">
</p>

## ⚡ Quick Start

### Prerequisites

| Service | Cost | Get Key At |
| :--- | :--- | :--- |
| NVIDIA NIM | Varies | [build.nvidia.com](https://build.nvidia.com) |
| DeepSeek | Cheap | [platform.deepseek.com](https://platform.deepseek.com/) |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART.git
cd ARGOFLOAT-CHART

# 2. Run the one-click setup wizard
python local_setup.py

# 3. Follow the prompts — opens automatically at http://localhost:5000 🎉
```

> **That's it!** The wizard installs all dependencies, configures your database, and launches the app.

### Configuration

```env
# .env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/floatchart
# 2. Get an NVIDIA API Key for Llama 3.3
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxx
NVIDIA_MODEL=meta/llama-3.3-70b-instruct

# Optional premium LLM providers
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# DEEPSEEK_API_KEY=...
```

---

## 🏗️ Repository Structure

```
ARGOFLOAT-CHART/
│
├── 🤖 ARGO_CHATBOT/              # Main Application
│   ├── app.py                    # Flask server & all API routes
│   ├── brain.py                  # LLM orchestration & AI summaries
│   ├── sql_builder.py            # Dynamic SQL generation (7 query types)
│   ├── sql_sanitizer.py          # ⚠️  Safety layer — read-only enforcement
│   ├── agent_tools.py            # 🤖 Public agent-callable tool wrappers
│   └── static/
│       ├── index.html            # 💬 Chat UI
│       ├── map.html              # 🗺️  Map UI
│       └── dashboard.html        # 📊 Dashboard UI
│
├── 📥 DATA_GENERATOR/            # Data Manager (Local Only)
│   ├── app.py                    # Manager web UI (port 5001)
│   ├── bulk_fetch.py             # ERDDAP bulk downloader
│   └── database_utils.py         # DB helpers
│
├── 🚀 local_setup.py             # One-click setup wizard
├── 📋 requirements.txt           # Python dependencies
├── 📄 .env.example               # Config template
└── 🤝 CONTRIBUTING.md            # Contributor guide
```

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|:-----:|:-----------|
| **Backend** | Python 3.9+ · Flask 2.0+ |
| **AI / LLM** | NVIDIA Llama 3.3 70B · DeepSeek · OpenAI · Anthropic Claude · Gemini |
| **Database** | PostgreSQL 15+ · SQLAlchemy |
| **Frontend** | HTML5 · CSS3 · JavaScript |
| **Visualisation** | Chart.js · Leaflet.js |
| **Safety** | SQLSanitizer (custom, stdlib-only) |

</div>

---

## 👥 Team

<div align="center">

<table>
<tr>
<td align="center" width="50%">

<a href="https://github.com/Anbu-2006">
<img src="https://github.com/Anbu-2006.png" width="120" style="border-radius:50%;" alt="Anbuselvan T"/>
</a>

### Anbuselvan T
**AI & Backend Engineer**

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Anbu-2006)

`AI/LLM` `Database` `API Design` `SQL`

</td>
<td align="center" width="50%">

<a href="https://github.com/navin18-cmd">
<img src="https://github.com/navin18-cmd.png" width="120" style="border-radius:50%;" alt="Navin"/>
</a>

### Navin
**Frontend Developer**

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/navin18-cmd)

`UI/UX` `Maps` `Charts` `CSS`

</td>
</tr>
</table>

</div>

---

## 📚 Resources

<div align="center">

| Resource | Link |
|:--------:|:-----|
| 🌊 **ARGO Program** | [argo.ucsd.edu](https://argo.ucsd.edu) |
| 📡 **ERDDAP Server** | [erddap.ifremer.fr](https://erddap.ifremer.fr) |
| 🧠 **NVIDIA NIM** | [build.nvidia.com](https://build.nvidia.com) |
| 🤝 **Contributing** | [CONTRIBUTING.md](./CONTRIBUTING.md) |

</div>

---

## 📄 License

**MIT License** — Free to use, modify, and distribute.  
See [LICENSE](LICENSE) for details.

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">
</p>

<div align="center">

## ⭐ Support the Project

**If FloatChart helped you, please give it a star!**

<br/>

[![Stargazers](https://img.shields.io/github/stars/Anbu-Navin-Devs/ARGOFLOAT-CHART?style=for-the-badge&logo=github&label=Stars&color=f59e0b)](https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/stargazers)
&nbsp;
[![Forks](https://img.shields.io/github/forks/Anbu-Navin-Devs/ARGOFLOAT-CHART?style=for-the-badge&logo=github&label=Forks&color=3b82f6)](https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/network/members)
&nbsp;
[![Issues](https://img.shields.io/github/issues/Anbu-Navin-Devs/ARGOFLOAT-CHART?style=for-the-badge&logo=github&label=Issues&color=ef4444)](https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/issues)

<br/>

---

<br/>

**Built with 💙 by [Anbuselvan T](https://github.com/Anbu-2006) & [Navin](https://github.com/navin18-cmd)**

*The Open Intelligence Layer for ARGO Ocean Data* 🌊

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A2647,25:144272,50:205295,75:2C74B3,100:0A2647&height=120&section=footer" width="100%"/>

</div>
