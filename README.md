---
title: LLM Analysis Quiz Solver – Autonomous Agent
emoji: Robot
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

<div align="center">

<img src="https://img.shields.io/badge/TDS%20Project-100%25%20Autonomous-success?style=for-the-badge&logo=robot" alt="100% Autonomous"/>
<img src="https://img.shields.io/badge/FastAPI-Ready-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
<img src="https://img.shields.io/badge/endpoint?url=https://img.shields.io/badge/Playwright-Working-45b8d8?style=for-the-badge&logo=playwright" alt="Playwright"/>
<img src="https://img.shields.io/badge/Docker-Deployed-2496ED?style=for-the-badge&logo=docker" alt="Docker"/>

# Large Language Model Analysis Quiz Solver

**Fully Autonomous Agent • Tools in Data Science • IIT Madras**

**Student**: Divya Devendrasingh  
**Roll No**: 25DS1000013  
**Email**: 25ds1000013@ds.study.iitm.ac.in  
**November 2025**

</div>

---

### What This Agent Does (100% Hands-Free)

Solves the **entire TDS LLM Analysis Quiz chain** (15–30+ pages) automatically:

- Renders JavaScript-heavy pages → **Playwright**
- Downloads & parses CSV / XLSX / PDF / images
- Extracts tables from PDFs (with OCR fallback)
- Runs full data analysis (pandas, matplotlib, seaborn)
- Generates correct answers & visualizations
- Submits every page correctly
- Follows the next URL until completion

Works perfectly on demo → will work perfectly on your real quiz.

---

### Features

| Feature                         | Status | Details                                      |
|--------------------------------| :white_check_mark: |----------------------------------------------|
| FastAPI `/solve` endpoint      | Done       | Secret-protected + background execution       |
| Playwright JS rendering        | Done       | Handles all dynamic content                  |
| File parsing (CSV, Excel, PDF) | Done       | Includes smart table + OCR extraction        |
| Gemini 1.5 Flash (optional)    | Done       | For complex reasoning & code generation      |
| No timeout (background tasks)  | Done       | Safely runs 30+ pages                        |
| Docker + HF Spaces ready       | Done       | One-click deploy                             |

---

### Quickstart (Local Setup)

```bash
# 1. Clone the repo
git clone https://github.com/Divya-Devendrasingh/llm-analysis-quiz.git
cd llm-analysis-quiz

# 2. Install (recommended: uv = lightning fast)
pip install uv
uv sync
uv run playwright install --with-deps chromium

# 3. Setup secrets
cp .env.example .env
# Edit .env → add your real SECRET (and Gemini key if you have one)

# 4. Launch server
uv run uvicorn app:app --reload --port 8000
Server running at: http://127.0.0.1:8000

Test Instantly (Demo Quiz)
Bashcurl -X POST http://127.0.0.1:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "25ds1000013@ds.study.iitm.ac.in",
    "secret": "your_real_secret_here",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
You’ll get {"status":"ok"} → watch the terminal as it solves every page automatically!

Final Step: Run Your Real Quiz (Just One Command)
When you get your personal quiz link, run this (replace only the URL):
Bashcurl -X POST http://127.0.0.1:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "25ds1000013@ds.study.iitm.ac.in",
    "secret": "your_real_secret_here",
    "url": "https://tds-llm-analysis.s-anand.net/quiz/YOUR_QUIZ_ID_HERE"
  }'
Go have coffee — it will finish everything perfectly.

One-Click Deploy to Hugging Face Spaces (Optional)

Create new Space → select Docker
Connect this GitHub repo
Add secrets:
EMAIL → 25ds1000013@ds.study.iitm.ac.in
SECRET → your secret
GEMINI_API_KEY → (optional)

Done — your solver runs 24×7 online!


Security

Never commit .env file
All secrets loaded via environment variables only
No hard-coded credentials


Future Upgrades (Already Planned)

Add camelot-py / tabula-py for complex PDFs
File caching system
LangGraph integration for advanced routing
Live progress dashboard (Streamlit)


License
MIT License — fork, improve, share freely!


  Made with passion for Tools in Data Science, IIT Madras

  Divya Devendrasingh • November 2025

```
