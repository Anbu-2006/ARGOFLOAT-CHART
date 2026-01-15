# 🌊 FloatChart – AI-Powered Ocean Intelligence Platform

An AI-powered web application for querying and visualizing ARGO float oceanographic data using natural language. Features interactive maps, dynamic charts, and a data pipeline for fetching real-time ocean observations from the Indian Ocean region.

---

## 🌐 Live Demo

**Try it now:** [https://floatchat.onrender.com](https://floatchat.onrender.com)

> ⚠️ **Note:** The live demo contains sample data for demonstration purposes. For full access to real-time ARGO data, set up the local version.

---

## 🚀 Two Ways to Use This Project

| Mode | Data | Best For |
|------|------|----------|
| **🌐 Live Demo** | Sample data (14 records) | Quick preview, sharing with others |
| **💻 Local Setup** | Full ARGO data (1000s of records) | Research, full functionality |

---

## ✨ Features

- 💬 **Natural Language Queries** - Ask questions like "Show temperature trends in Arabian Sea"
- 🗺️ **Interactive Map** - Leaflet.js with float location markers
- 📊 **Dynamic Charts** - Temperature, salinity, depth visualizations
- 📋 **Data Tables** - Browse, filter, and export results
- ⬇️ **CSV Export** - Download query results
- 🤖 **AI-Powered** - Uses Groq (LLaMA 3.3) for intelligent query processing

---

## 📁 Project Structure

```
ARGOFLOAT-CHART/
├── ARGO_CHATBOT/          # 🌐 Web Application (Deployed)
│   ├── app.py             # Flask server
│   ├── brain.py           # AI/NLP processing (Groq)
│   ├── sql_builder.py     # Query generation
│   ├── Procfile           # Deployment config
│   └── static/            # Frontend (HTML/CSS/JS)
│
└── DATA_GENERATOR/        # 🖥️ Desktop App (Local Only)
    ├── gui.py             # Tkinter GUI
    └── pipeline/          # ETL modules for ERDDAP data
```

---

## 💻 Local Setup (Full Data Access)

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Anbu-2006/ARGOFLOAT-CHART.git
cd ARGOFLOAT-CHART

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Setup PostgreSQL database
# Create database 'argo_db' and run the SQL from schema below

# 4. Configure environment
copy .env.example .env
# Edit .env with your DATABASE_URL and GROQ_API_KEY

# 5. Run Data Generator (fetch real ARGO data)
cd DATA_GENERATOR
pip install -r requirements.txt
python gui.py  # Click "Update Latest Data"

# 6. Run Web Application
cd ../ARGO_CHATBOT
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000
```

### Database Schema

```sql
CREATE TABLE argo_data (
    id SERIAL PRIMARY KEY,
    float_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    dissolved_oxygen DOUBLE PRECISION,
    chlorophyll DOUBLE PRECISION
);

CREATE INDEX idx_argo_float_id ON argo_data(float_id);
CREATE INDEX idx_argo_timestamp ON argo_data(timestamp);
```

---

## ⚙️ Environment Variables

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/argo_db

# AI (Groq - FREE)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=llama-3.3-70b-versatile
```

**Get your FREE API key:** [console.groq.com/keys](https://console.groq.com/keys)

---

## 🌐 Deployment (For Developers)

The web app is deployed on **Render** with **Supabase** database.

### Deployment Stack
- **Hosting:** [Render](https://render.com) (Free tier)
- **Database:** [Supabase](https://supabase.com) (Free tier)
- **AI:** [Groq](https://groq.com) (Free tier)

### To Deploy Your Own:
1. Fork this repository
2. Create Supabase project and database
3. Create Render web service pointing to `ARGO_CHATBOT/`
4. Set environment variables on Render
5. Deploy!

---

## 🔬 Example Queries

Try these in the chatbot:
- "Show all ARGO floats"
- "What is the average temperature?"
- "Temperature trends in Arabian Sea"
- "Show trajectory of float 2902115"
- "Nearest floats to Chennai"
- "Compare temperature and salinity"

---

## 📊 Data Source

- **ARGO Program:** Global ocean observation network
- **ERDDAP Server:** Ifremer (France) / NOAA CoastWatch
- **Region:** Indian Ocean (50°E-100°E, 20°S-25°N)
- **Parameters:** Temperature, Salinity, Dissolved Oxygen, Chlorophyll

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask, SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript |
| Database | PostgreSQL |
| AI/LLM | Groq (LLaMA 3.3 70B) |
| Maps | Leaflet.js |
| Charts | Chart.js |
| Deployment | Render + Supabase |

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 👤 Author

**Anbu** - [GitHub](https://github.com/Anbu-2006)

---

Made with 💙 for Ocean Science 🌊
