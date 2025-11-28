---
title: LLM Analysis Quiz Solver – Autonomous Agent
emoji: Robot
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# LLM Analysis Quiz Solver – TDS Project

**Course**: Tools in Data Science (TDS)  
**Institution**: IIT Madras  
**Student**: Divya Devendrasingh   
**Email**: 25ds1000013@ds.study.iitm.ac.in  

A fully autonomous quiz-solving agent for the **TDS LLM Analysis Quiz** that runs end-to-end without any human intervention.

Successfully solves multi-step quiz chains involving:
- JavaScript-rendered pages (Playwright)
- File downloads (CSV, XLSX, PDF, images)
- Data cleaning, analysis, and visualization
- Automatic answer submission across 15–30 pages

## Features

- FastAPI server with secret validation (`/solve` endpoint)
- Headless Playwright for dynamic content rendering
- Robust file parsing (CSV, Excel, PDF with table extraction + OCR fallback OCR)
- Optional Google Gemini integration for complex reasoning
- Background task processing (no timeout on long chains)
- Docker-ready — deploys instantly on Hugging Face Spaces, Render, Railway
- Clean, secure, and well-documented

## Repository Status

| Item                    | Status  | Notes                              |
|-------------------------|---------|------------------------------------|
| `app.py`                | Present | FastAPI + background solver        |
| `requirements.txt`      | Present | All dependencies listed            |
| `Dockerfile`            | Present | Works on HF Spaces & cloud         |
| `.env.example`          | Present | Never commit real secrets!         |
| Playwright support      | Present | Handles JS-heavy quiz pages        |
| PDF/Table/OCR helpers   | Present | Ready for real-world data tasks    |

## Quickstart (Local)

```bash
# 1. Clone and enter
git clone https://github.com/Divya-Devendrasingh/llm-analysis-quiz.git
cd llm-analysis-quiz

# 2. Install (recommended: uv for speed)
pip install uv
uv sync
uv run playwright install --with-deps chromium

# Or with pip
pip install -r requirements.txt
playwright install --with-deps chromium

# 3. Set up secrets
cp .env.example .env
# Edit .env → put your real SECRET and (optional) Gemini key

# 4. Run server
uv run uvicorn app:app --reload --port 8000
