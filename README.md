# 🌊 FloatChart – AI-Powered Ocean Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=for-the-badge&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?style=for-the-badge&logo=postgresql)
![LangChain](https://img.shields.io/badge/LangChain-AI-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**An AI-powered web application for querying and visualizing ARGO float oceanographic data using natural language.**

[🌐 Live Demo](https://argofloat-chart.onrender.com) • [💻 Local Setup](#-local-setup-full-features) • [📖 Documentation](#-features)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Deployment Modes](#-deployment-modes)
- [Features](#-features)
- [Live Demo](#-live-demo)
- [Local Setup](#-local-setup-full-features)
- [Project Structure](#-project-structure)
- [Sample Queries](#-sample-queries)
- [API Reference](#-api-reference)
- [Limitations](#-limitations)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌐 Overview

**FloatChart** is an intelligent oceanographic data platform that allows users to query ARGO float data using natural language. The system leverages AI (LLM) to interpret user questions, generate SQL queries, and present results through interactive visualizations.

### What are ARGO Floats?
ARGO floats are autonomous profiling instruments that drift with ocean currents, diving to depths of 2000m and measuring temperature, salinity, and pressure. Over 4,000 floats are currently deployed worldwide, providing critical data for climate research and oceanography.

---

## 🔄 Deployment Modes

FloatChart supports **two deployment modes** to suit different use cases:

### 🌐 Cloud Deployment (Recommended for Quick Access)
- **Database:** Supabase PostgreSQL (cloud-hosted)
- **Hosting:** Render.com
- **Data:** Pre-loaded 1.5M+ records (Jan 2020 - Jun 2026)
- **Best for:** Quick exploration, demos, sharing with others

### 💻 Local Development (Full Features)
- **Database:** Local PostgreSQL
- **Hosting:** Local Flask server
- **Data:** Fetch real-time data from ERDDAP
- **Best for:** Research, custom data, full control

| Feature | 🌐 Cloud Demo | 💻 Local Setup |
|---------|--------------|----------------|
| Database | Supabase (500MB limit) | Local PostgreSQL (unlimited) |
| Records | 1.5M (static) | Unlimited (fetch anytime) |
| Data Source | Pre-loaded | Real-time ERDDAP |
| Update Data | ❌ Not possible | ✅ Anytime via CLI/GUI |
| Custom Regions | ❌ Fixed dataset | ✅ Any ocean region |
| Historical Data | Jan 2020 - Jun 2026 | Any available dates |
| Setup Time | Instant (just visit) | 10-15 minutes |

---

## ✨ Features

| Feature | Description | Cloud | Local |
|---------|-------------|:-----:|:-----:|
| 💬 **Natural Language Queries** | Ask questions in plain English | ✅ | ✅ |
| 🗺️ **Interactive Map Explorer** | Click anywhere to find floats | ✅ | ✅ |
| 📊 **Dynamic Visualizations** | Multiple chart types | ✅ | ✅ |
| 📈 **Float Trajectories** | Track float movement | ✅ | ✅ |
| 🔍 **Proximity Search** | Find floats near cities | ✅ | ✅ |
| ⬇️ **CSV Export** | Download data | ✅ | ✅ |
| 🔄 **Data Updates** | Fetch new ARGO data | ❌ | ✅ |
| 🗄️ **Custom Database** | Use your own PostgreSQL | ❌ | ✅ |
| 📡 **ERDDAP Integration** | Real-time data fetch | ❌ | ✅ |
| 🖥️ **Desktop GUI** | Tkinter data manager | ❌ | ✅ |

---

## 🌐 Live Demo

**🔗 [https://argofloat-chart.onrender.com](https://argofloat-chart.onrender.com)**

### Database Statistics
| Metric | Value |
|--------|-------|
| **Total Records** | 1,513,324+ |
| **Date Range** | January 2020 - June 2026 |
| **Coverage** | Global (Pacific, Atlantic, Indian, Mediterranean, Caribbean) |
| **Metrics** | Temperature, Salinity, Pressure, Dissolved Oxygen |

### ⚠️ Demo Limitations
- Data is **static** (cannot add new records)
- Supabase free tier (500MB storage limit)
- Cold start delay (~30s if inactive)
- Rate limited API calls

---

## 💻 Local Setup (Full Features)

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (local installation)
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/Anbu-2006/ARGOFLOAT-CHART.git
cd ARGOFLOAT-CHART
```

### Step 2: Set Up PostgreSQL Database

```sql
-- Connect to PostgreSQL and create database
CREATE DATABASE argo_chatbot;
```

### Step 3: Configure Environment

Create `.env` file in `ARGO_CHATBOT/` folder:

```env
# Local PostgreSQL
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/argo_chatbot

# LLM Provider (at least one required)
GROQ_API_KEY=your_groq_api_key
# OR
GOOGLE_API_KEY=your_google_api_key
```

### Step 4: Install Dependencies

```bash
# Web Application
cd ARGO_CHATBOT
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Data Generator (optional, for fetching data)
cd ../DATA_GENERATOR
pip install -r requirements.txt
```

### Step 5: Initialize Database

```bash
cd DATA_GENERATOR
python setup_local_db.py
```

### Step 6: Fetch ARGO Data

```bash
# Fetch data from a specific region
python fetch_argo_data.py --region "Bay of Bengal" --days 30

# Or fetch from multiple regions
python fetch_argo_data.py --all-regions --days 7

# Or use the GUI
python gui.py
```

### Step 7: Run Web Application

```bash
cd ../ARGO_CHATBOT
python app.py
```

Open browser: **http://localhost:5000**

---

## 📁 Project Structure

```
ARGOFLOAT-CHART/
│
├── 📂 ARGO_CHATBOT/              # 🌐 Web Application
│   ├── app.py                    # Flask server & API routes
│   ├── brain.py                  # AI/NLP with LangChain
│   ├── sql_builder.py            # Dynamic SQL generation
│   ├── database_utils.py         # Database utilities
│   ├── requirements.txt          # Python dependencies
│   ├── Procfile                  # Render deployment
│   ├── .env.example              # Environment template
│   │
│   └── 📂 static/                # Frontend
│       ├── index.html            # Chat interface
│       ├── map.html              # Interactive map
│       ├── 📂 css/styles.css     # Styles
│       └── 📂 js/app.js          # JavaScript
│
├── 📂 DATA_GENERATOR/            # 💻 Local Data Tools
│   ├── gui.py                    # Desktop GUI (Tkinter)
│   ├── fetch_argo_data.py        # CLI data fetcher
│   ├── setup_local_db.py         # Database setup script
│   ├── config.py                 # Configuration
│   ├── env_utils.py              # Environment utilities
│   ├── update_manager.py         # Data sync manager
│   └── requirements.txt          # Dependencies
│
├── README.md                     # This documentation
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

---

## 💬 Sample Queries

### 📍 Location-Based
```
• "Find 5 nearest floats to Chennai"
• "Show floats in Bay of Bengal"
• "Floats near Kollam"
• "Data from Arabian Sea"
```

### 🌡️ Data Analysis
```
• "Average temperature in Indian Ocean"
• "Maximum salinity in Pacific"
• "Temperature trends in 2024"
```

### 🔢 Specific Float
```
• "Show data for float 2902115"
• "Trajectory of float 5907083"
```

### Supported Locations

| Category | Locations |
|----------|-----------|
| **Indian Ocean** | Arabian Sea, Bay of Bengal, Andaman Sea, Laccadive Sea |
| **Pacific Ocean** | South China Sea, Philippine Sea, Coral Sea, Tasman Sea |
| **Atlantic Ocean** | Caribbean Sea, Gulf of Mexico, Mediterranean Sea |
| **Indian Cities** | Chennai, Mumbai, Kollam, Kochi, Goa, Kolkata, Vizag, Mangalore, Trivandrum, Pondicherry, Port Blair |
| **International** | Singapore, Tokyo, Sydney, Cape Town, Miami, Maldives, Mauritius |

---

## 📡 API Reference

### Base URL
- **Cloud:** `https://argofloat-chart.onrender.com/api`
- **Local:** `http://localhost:5000/api`

### Endpoints

#### `GET /api/status`
```json
{
  "status": "online",
  "database": "connected",
  "records": 1513324
}
```

#### `POST /api/query`
```json
// Request
{ "query": "Find 5 nearest floats to Chennai" }

// Response
{
  "success": true,
  "query_type": "Proximity",
  "data": [...],
  "summary": "Found 5 floats..."
}
```

---

## 🚫 Limitations

### Cloud Deployment Limitations

| Limitation | Details |
|------------|---------|
| **Static Data** | Cannot add new records (Supabase read-only in production) |
| **Storage Cap** | 500MB Supabase free tier (~1.5M records max) |
| **Cold Start** | ~30 second delay if server is idle |
| **Rate Limits** | API throttling on heavy use |
| **Date Range** | Fixed: Jan 2020 - Jun 2026 |

### Local Deployment Limitations

| Limitation | Details |
|------------|---------|
| **Setup Required** | Need PostgreSQL + Python environment |
| **ERDDAP Dependency** | Data fetch depends on ERDDAP availability |
| **Local Only** | Not accessible from internet (without tunneling) |

### Data Quality Notes

- Some float markers may appear on coastlines due to GPS accuracy (~10-50m error)
- ARGO floats operate in open ocean; coastal proximity is for reference only
- Temperature/salinity values are real measurements from ARGO program

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.10+ | Core language |
| Flask 3.0 | Web framework |
| LangChain | AI orchestration |
| Groq / Gemini | LLM providers |
| SQLAlchemy | Database ORM |
| PostgreSQL | Database |

### Frontend
| Technology | Purpose |
|------------|---------|
| HTML5/CSS3 | Structure & styling |
| JavaScript | Interactivity |
| Leaflet.js | Maps |
| Chart.js | Visualizations |

### Data Sources
| Source | Purpose |
|--------|---------|
| ERDDAP | Real-time ARGO data |
| Supabase | Cloud PostgreSQL |

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing`)
3. **Commit** changes (`git commit -m 'Add feature'`)
4. **Push** to branch (`git push origin feature/amazing`)
5. **Open** Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **[ARGO Program](https://argo.ucsd.edu/)** - Global ocean observation
- **[ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/)** - Data distribution
- **[Groq](https://groq.com/)** - Fast LLM inference
- **[Supabase](https://supabase.com/)** - Cloud PostgreSQL
- **[Render](https://render.com/)** - Deployment platform

---

<div align="center">

### 🌊 Made with ❤️ for Ocean Research

**⭐ Star this repo if you find it helpful!**

| | |
|---|---|
| **Developer** | Anbu |
| **GitHub** | [@Anbu-2006](https://github.com/Anbu-2006) |
| **Live Demo** | [argofloat-chart.onrender.com](https://argofloat-chart.onrender.com) |

</div>
