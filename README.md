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
  <h1>Large Language Model Analysis Quiz Solver</h1>
  <p><strong>Fully Autonomous Agent • TDS Project • IIT Madras</strong></p>
  
  <img src="https://img.shields.io/badge/Status-100%25%20Working-success?style=for-the-badge&logo=checkmark&logoColor=white" alt="Working"/>
  <img src="https://img.shields.io/badge/FastAPI-Ready-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Playwright-JS%20Rendering-45b8d8?style=for-the-badge&logo=playwright" alt="Playwright"/>
  <img src="https://img.shields.io/badge/Gemini-Optional-8B21A1?style=for-the-badge&logo=google" alt="Gemini"/>
  <img src="https://img.shields.io/badge/Docker-Deployed-2496ED?style=for-the-badge&logo=docker" alt="Docker"/>
</div>

<br>

**Student**: Divya Devendrasingh  
**Roll No**: 25DS1000013  
**Email**: 25ds1000013@ds.study.iitm.ac.in  
**Course**: Tools in Data Science (TDS), IIT Madras  
**Date**: November 2025

---

### What This Agent Does (End-to-End)

Automatically solves the entire TDS LLM Analysis Quiz chain (15–30+ pages) with zero human input:

- Renders JavaScript-heavy pages → Playwright  
- Downloads & parses CSV / XLSX / PDF / images  
- Extracts tables from PDFs (with OCR fallback)  
- Performs data analysis & visualization using pandas/matplotlib/seaborn  
- Submits correct answers page after page  
- Follows the “next URL” until completion  

Works on demo → works on your real quiz.

### Features

| Feature                        | Status | Details                                      |
|-------------------------------|--------|----------------------------------------------|
| FastAPI `/solve` endpoint     | Done   | Secret-protected, background execution       |
| Playwright JS rendering       | Done   | Handles dynamic content perfectly            |
| File parsing (CSV, Excel, PDF)| Done   | Includes PDF table extraction + OCR          |
| Gemini 1.5 Flash (optional)   | Done   | For complex reasoning tasks                  |
| Background tasks              | Done   | No timeout — runs 30+ pages safely           |
| Docker & HF Spaces ready      | Done   | One-click deploy                             |

### Quickstart (Local)

```bash
git clone https://github.com/Divya-Devendrasingh/llm-analysis-quiz.git
cd llm-analysis-quiz

# Recommended: use uv (super fast)
pip install uv
uv sync
uv run playwright install --with-deps chromium

# Or classic pip
# pip install -r requirements.txt
# playwright install --with-deps chromium

cp .env.example .env
# Edit .env → put your real SECRET (and Gemini key if you have one)

uv run uvicorn app:app --reload --port 8000

**Server live at: http://127.0.0.1:8000**
**Test with Demo (Instant)**
Bashcurl -X POST http://127.0.0.1:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "25ds1000013@ds.study.iitm.ac.in",
    "secret": "your_real_secret_here",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
You’ll see {"status":"ok"} → agent starts solving automatically.
**For Your Real Quiz (Final Command)**
Replace only the URL with your personal link:
Bashcurl -X POST http://127.0.0.1:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "25ds1000013@ds.study.iitm.ac.in",
 "secret": "your_real_secret_here",
 "url": "https://tds-llm-analysis.s-anand.net/quiz/YOUR_QUIZ_ID"
  }'
Sit back — it will finish everything by itself.
Deploy to Hugging Face Spaces (Optional but Awesome)

Create new Space → choose “Docker”
Connect your GitHub repo
Add these secrets in Settings:
EMAIL → 25ds1000013@ds.study.iitm.ac.in
SECRET → your secret
GEMINI_API_KEY → (optional)

Done — live 24×7 solver!

Security

Never commit .env
All secrets loaded via environment variables only

Future Ideas (Already Planned)

Add camelot-py / tabula-py for tough PDFs
File caching layer
LangGraph upgrade for smarter routing
Add Streamlit dashboard to watch progress live

**License**
MIT License — fork, improve, share!
