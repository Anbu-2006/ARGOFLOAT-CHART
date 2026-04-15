# Contributing to FloatChart 🌊

Thank you for your interest in FloatChart! We're building the **Open Intelligence Layer for ARGO ocean data**, and we'd love your help.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Submitting Changes](#submitting-changes)
- [Adding a New Agent Tool](#adding-a-new-agent-tool)
- [Testing](#testing)
- [Style Guide](#style-guide)

---

## Code of Conduct

This project is welcoming to everyone. We expect all contributors to be respectful and constructive. Harassment of any kind will not be tolerated.

---

## How to Contribute

| Contribution Type | Where to Start |
|:------------------|:---------------|
| 🐛 Bug fix | Open an [Issue](https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/issues) first |
| ✨ New feature | Open a Discussion before a PR |
| 🤖 New Agent Tool | See [Adding a New Agent Tool](#adding-a-new-agent-tool) below |
| 📖 Documentation | Edit `README.md` or docstrings — PRs welcome! |
| 🌍 New location support | Add to `LOCATIONS` dict in `brain.py` |
| 🧪 Tests | Add to `tests/` — no test, no merge for core code |
| 🎨 UI / frontend | Target `ARGO_CHATBOT/static/` |

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-fork>/ARGOFLOAT-CHART.git
cd ARGOFLOAT-CHART

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r ARGO_CHATBOT/requirements.txt

# 4. Copy and fill in credentials
cp .env.example .env
# Edit .env: set DATABASE_URL and NVIDIA_API_KEY

# 5. Run the app
cd ARGO_CHATBOT
python app.py
```

The app opens at **http://localhost:5000**.

---

## Project Architecture

```
ARGOFLOAT-CHART/
├── ARGO_CHATBOT/
│   ├── app.py            ← Flask server & all API routes
│   ├── brain.py          ← LLM orchestration, intent parsing, AI summary
│   ├── sql_builder.py    ← Dynamic SQL generation (7 query types)
│   ├── sql_sanitizer.py  ← ⚠️  Safety layer — validates every query ⚠️
│   ├── agent_tools.py    ← Public, LLM-callable tool wrappers
│   └── static/           ← Frontend (HTML/CSS/JS, Chart.js, Leaflet)
│
└── DATA_GENERATOR/
    ├── app.py            ← Data Manager UI (port 5001)
    ├── bulk_fetch.py     ← ERDDAP bulk downloader
    └── database_utils.py ← DB helpers
```

### Key module contracts

| Module | Input | Output |
|:-------|:------|:-------|
| `brain.get_intelligent_answer` | plain English string | structured dict (answer, data, chart_type, sql) |
| `sql_builder.build_query` | intent dict + db_context | SQL string (safety-checked) |
| `sql_sanitizer.SQLSanitizer.validate` | SQL string | `{safe, reason, checks}` |
| `agent_tools.query_ocean_data` | plain English string | agent-ready JSON dict |

---

## Submitting Changes

1. **Branch** from `main`:
   ```bash
   git checkout -b feature/my-new-tool
   ```

2. **Write code** following the [Style Guide](#style-guide).

3. **Test** your changes (see [Testing](#testing)).

4. **Open a Pull Request** with:
   - A clear title: `feat: add XYZ` / `fix: broken proximity query`
   - A description of *what* changed and *why*
   - Screenshots for any UI changes

---

## Adding a New Agent Tool

Agent tools live in `ARGO_CHATBOT/agent_tools.py`. They are the public-facing functions that AI agents (Claude, GPT, Gemini, etc.) call to query ocean data.

### Checklist for a new tool

- [ ] Add a function with a **full NumPy-style docstring** (see existing functions for format).
- [ ] Include `Args`, `Returns`, and at least one `Example` in the docstring — LLMs read these.
- [ ] Return a `dict` with `success`, `data`, and `error` keys (consistent schema).
- [ ] Register the tool in the `TOOL_MANIFEST` at the bottom of `agent_tools.py`.
- [ ] Make sure the underlying SQL goes through `sql_builder.build_query` (which enforces the safety gate automatically).

### Template

```python
def get_my_new_tool(param: str) -> dict:
    """
    One-line summary.

    Longer description of what this tool does and when to call it.

    Args:
        param (str): What this parameter means.

    Returns:
        dict with keys:
            success (bool)
            data    (list[dict])
            error   (str | None)

    Example:
        >>> result = get_my_new_tool("example value")
        >>> print(result["data"])
    """
    return query_ocean_data(f"<natural language question using {param}>")
```

---

## Testing

We use **pytest**. Run the test suite before submitting any PR:

```bash
pytest tests/ -v
```

For adding tests:
- Place tests in `tests/`
- Unit-test the `sql_sanitizer` if you add new safety rules
- Integration tests for new agent tools should mock `brain.get_intelligent_answer`

---

## Style Guide

| Aspect | Rule |
|:-------|:-----|
| Formatting | Black (`black .`) |
| Imports | isort (`isort .`) |
| Docstrings | NumPy / Google style — required for every public function |
| SQL | Always parameterised (use SQLAlchemy `text()` with bound params) |
| Return types | All public functions must have type hints |
| Naming | `snake_case` functions, `UPPER_CASE` constants |

### Safety rule — never bypass the sanitizer

All AI-generated SQL **must** pass through `sql_builder.build_query` (which calls `sql_sanitizer.SQLSanitizer.validate` internally). Never execute raw LLM-generated strings directly against the database.

```python
# ✅ Correct
sql = sql_builder.build_query(intent, db_context, engine)
conn.execute(text(sql))

# ❌ Never do this
conn.execute(text(llm_output_raw))
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/Anbu-Navin-Devs/ARGOFLOAT-CHART/discussions) or reach out to the team via Issues.

**Built with 💙 by Anbuselvan T & Navin — exploring the ocean, one query at a time.**
