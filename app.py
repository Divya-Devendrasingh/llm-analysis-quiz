# app.py
"""
LLM Analysis Quiz solver endpoint
- Validates incoming secret
- Renders JS pages using Playwright
- Extracts tasks (base64 / JSON / text)
- Downloads referenced files (CSV/XLSX/PDF) and computes answers
- Optionally calls Gemini (Google Generative API) to interpret tasks
"""
import os
import re
import json
import base64
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse
import httpx
import uvicorn

from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# utils
from utils.pdf_utils import extract_text_from_pdf_bytes, extract_tables_from_pdf_bytes
from utils.ocr_utils import ocr_image_bytes
import pandas as pd

# Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except Exception:
    HAS_GEMINI = False

logger = logging.getLogger("llm_analysis_quiz")
logging.basicConfig(level=logging.INFO)

APP_SECRET = os.getenv("SECRET", "change-me")
EMAIL_DEFAULT = os.getenv("EMAIL", "your-email@example.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY and HAS_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)
    # model selection: change if needed
    GEM_MODEL_NAME = "gemini-1.5"
else:
    GEM_MODEL_NAME = None

app = FastAPI(title="LLM Analysis Quiz Endpoint")

class TaskPayload(BaseModel):
    email: str
    secret: str
    url: str

async def call_gemini_text(prompt: str, max_output_tokens: int = 512) -> str:
    """Call Gemini model (blocking call in thread). Return text or empty string."""
    if not GEM_MODEL_NAME:
        return ""
    def _sync_call():
        model = genai.get_model(GEM_MODEL_NAME)
        resp = model.generate(prompt=genai.Prompt.from_text(prompt), max_output_tokens=max_output_tokens)
        # unify response text extraction for different SDK shapes
        try:
            # newer SDK: resp.candidates[0].content[0].text
            candidates = getattr(resp, "candidates", None)
            if candidates:
                texts = []
                for cand in candidates:
                    # try nested content extraction
                    try:
                        parts = cand.content
                        for part in parts:
                            texts.append(part.text)
                    except Exception:
                        try:
                            texts.append(cand["content"])
                        except Exception:
                            pass
                return "\\n".join(texts)
        except Exception:
            pass
        # fallback: stringify
        return str(resp)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_call)

async def fetch_url_bytes(url: str, timeout: int = 60) -> Tuple[Optional[bytes], Optional[str]]:
    """Fetch a URL and return raw bytes and content-type header."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.content, r.headers.get("content-type", "")
    except Exception as e:
        logger.warning("fetch_url_bytes error: %s", e)
    return None, None

def try_sum_value_in_dataframe(df: pd.DataFrame) -> Optional[float]:
    """If DataFrame has a 'value' column (case-insensitive), sum numeric entries."""
    cols = {c.lower(): c for c in df.columns}
    if "value" in cols:
        colname = cols["value"]
        try:
            series = pd.to_numeric(df[colname], errors="coerce").dropna()
            return float(series.sum())
        except Exception:
            return None
    return None

async def extract_answer_from_file_bytes(url: str) -> Optional[Any]:
    """Download a file and attempt to compute an answer (sum of 'value' column or numeric extraction)."""
    content, ctype = await fetch_url_bytes(url)
    if not content:
        return None
    url_l = url.lower()
    # CSV
    try:
        if url_l.endswith(".csv") or "text/csv" in (ctype or ""):
            text = content.decode("utf-8", errors="ignore")
            df = pd.read_csv(pd.compat.StringIO(text)) if hasattr(pd, "compat") else pd.read_csv(pd.io.common.StringIO(text))
            s = try_sum_value_in_dataframe(df)
            if s is not None:
                return int(s)
    except Exception:
        logger.info("CSV parsing failed for %s", url)
    # XLSX
    try:
        if url_l.endswith(".xlsx") or "spreadsheet" in (ctype or "") or url_l.endswith(".xls"):
            from io import BytesIO
            df_list = pd.read_excel(BytesIO(content), sheet_name=None)
            # try each sheet
            for name, df in df_list.items():
                s = try_sum_value_in_dataframe(df)
                if s is not None:
                    return int(s)
    except Exception:
        logger.info("XLSX parsing failed for %s", url)
    # PDF: try to extract tables or numbers
    try:
        if url_l.endswith(".pdf") or "pdf" in (ctype or ""):
            # try refine: extract tables first
            tables = extract_tables_from_pdf_bytes(content)
            for df in tables:
                s = try_sum_value_in_dataframe(df)
                if s is not None:
                    return int(s)
            # fallback: extract full text and sum numbers heuristically
            text = extract_text_from_pdf_bytes(content)
            nums = re.findall(r"[-+]?[0-9]*\\.?[0-9]+", text)
            if nums:
                # sum all numeric tokens as a fallback
                vals = [float(n) for n in nums]
                return int(sum(vals))
    except Exception as e:
        logger.info("PDF parsing failed for %s: %s", url, e)
    return None

def extract_base64_strings_from_html(html: str) -> list:
    """Return list of decoded strings from common base64 embedding patterns."""
    candidates = []
    # patterns like atob(`...`) or atob("...") or innerHTML=atob(`...`)
    matches = re.findall(r'atob\\((?:\\`|\\"|\\\')([A-Za-z0-9+/=\\n\\r\\s]+)(?:\\`|\\"|\\\')\\)', html)
    matches += re.findall(r'([A-Za-z0-9+/]{120,}={0,2})', html)
    for m in matches:
        try:
            cleaned = "".join(m.split())
            decoded = base64.b64decode(cleaned).decode("utf-8", errors="ignore")
            candidates.append(decoded)
        except Exception:
            continue
    return candidates

@app.post("/", response_class=JSONResponse)
async def receive_task(payload: TaskPayload):
    if payload.secret != APP_SECRET:
        logger.warning("Invalid secret for %s", payload.email)
        raise HTTPException(status_code=403, detail="Invalid secret")
    try:
        result = await solve_quiz_url(payload.email, payload.secret, payload.url)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        logger.exception("Unhandled error solving quiz")
        raise HTTPException(status_code=500, detail=str(e))

async def solve_quiz_url(email: str, secret: str, url: str, overall_timeout_seconds: int = 170) -> dict:
    """Main orchestrator to solve a quiz url and submit the answer."""
    deadline = datetime.utcnow() + timedelta(seconds=overall_timeout_seconds)
    decoded_snippets = []
    submit_url = None
    submitted_payload = None
    submit_response = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        # friendly user agent
        await page.set_extra_http_headers({"user-agent": "LLM-Quiz-Solver/1.0 (+https://example.com)"})
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception:
            logger.info("Initial navigation timeout, attempting to continue")

        # capture rendered content
        try:
            body_text = await page.inner_text("body")
            content = await page.content()
        except Exception:
            body_text = ""
            content = ""

        # extract base64 decoded content if present
        decoded_snippets = extract_base64_strings_from_html(content)
        # also include body text
        combined_text = "\\n".join(decoded_snippets + [body_text, content])

        # try to detect JSON payload inside decoded snippets
        parsed_question = None
        for txt in decoded_snippets + [body_text, content]:
            m = re.search(r'\\{[\\s\\S]{20,}\\}', txt)
            if m:
                try:
                    j = json.loads(m.group(0))
                    parsed_question = j
                    # often the page includes a submit url inside the JSON
                    for k in ("submit_url", "submit", "post", "submitUrl", "url"):
                        if isinstance(j, dict) and k in j and isinstance(j[k], str) and j[k].startswith("http"):
                            submit_url = j[k]
                    break
                except Exception:
                    continue

        # try find explicit submit URL in visible text
        if not submit_url:
            m2 = re.search(r'(https?://[^\\s\"\\']+/submit[^\\s\"\\']*)', combined_text)
            if m2:
                submit_url = m2.group(1)

        # try form action
        if not submit_url:
            try:
                forms = await page.query_selector_all("form")
                for f in forms:
                    action = await f.get_attribute("action")
                    if action:
                        if action.startswith("http"):
                            submit_url = action
                        else:
                            submit_url = page.url.rstrip("/") + "/" + action.lstrip("/")
                        break
            except Exception:
                pass

        answer = None

        # If parsed_question includes direct 'answer', use it
        if parsed_question and isinstance(parsed_question, dict) and "answer" in parsed_question:
            answer = parsed_question["answer"]

        # Strategy: if page asks for 'sum of the "value" column', try to find linked csv/pdf/xlsx
        if answer is None and re.search(r'sum of the\\s+[\"\\']value[\"\\']\\s+column', combined_text, re.I):
            # find file link
            mfile = re.search(r'(https?://[^\\s\"\\']+\\.(?:csv|pdf|xlsx|xls))', combined_text, re.I)
            if mfile:
                file_url = mfile.group(1)
                answer = await extract_answer_from_file_bytes(file_url)

        # If not found and Gemini available, ask Gemini to interpret task and propose an answer
        if answer is None and GEM_MODEL_NAME:
            prompt = (
                "You are a helpful assistant. The following is the rendered content of a quiz page. "
                "Identify what the quiz is asking and provide a JSON object with an 'answer' key that contains "
                "the answer (number, boolean, string or JSON as appropriate).\\n\\n"
                "Rendered content:\\n" + combined_text[:8000]
            )
            try:
                gem_resp = await call_gemini_text(prompt)
                # try find JSON in response
                mj = re.search(r'\\{[\\s\\S]{10,}\\}', gem_resp)
                if mj:
                    try:
                        j = json.loads(mj.group(0))
                        if "answer" in j:
                            answer = j["answer"]
                    except Exception:
                        pass
                # otherwise try to extract a numeric
                if answer is None:
                    mnum = re.search(r'(-?\\d+[\\d,\\.]+)', gem_resp)
                    if mnum:
                        candidate = mnum.group(1).replace(",", "")
                        try:
                            answer = int(float(candidate))
                        except Exception:
                            pass
            except Exception as e:
                logger.info("Gemini call failed: %s", e)

        # last-resort heuristics: find explicit 'answer:' tokens
        if answer is None:
            m = re.search(r'answer[:\\s]*([0-9]{1,12})', combined_text, re.I)
            if m:
                answer = int(m.group(1))
        if answer is None:
            answer = "could-not-solve-automatically"

        # prepare payload and submit
        submitted_payload = {"email": email or EMAIL_DEFAULT, "secret": secret, "url": url, "answer": answer}

        if not submit_url:
            await browser.close()
            return {"correct": False, "reason": "No submit URL found on page", "debug": {"snippets": decoded_snippets[:3]}}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(submit_url, json=submitted_payload)
                try:
                    submit_response = r.json()
                except Exception:
                    submit_response = {"status_code": r.status_code, "text": r.text[:1000]}
        except Exception as e:
            await browser.close()
            return {"correct": False, "reason": f"Failed to POST answer: {e}"}

        await browser.close()
        return {"submit_url": submit_url, "submitted_payload": submitted_payload, "submit_response": submit_response}
