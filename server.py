import os
import time
import json
import re
import base64
import tempfile
import logging
from urllib.parse import urljoin, urlparse
from flask import Flask, request, jsonify, abort
import requests
import pandas as pd
import pdfplumber
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Config
SECRET = os.environ.get("QUIZ_SECRET", "changeme")
MAX_TOTAL_SECONDS = int(os.environ.get("MAX_TOTAL_SECONDS", "170"))  # must be < 180
PAGE_LOAD_TIMEOUT_MS = int(os.environ.get("PAGE_LOAD_TIMEOUT_MS", "60000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm-quiz")

app = Flask(__name__)

# --- Helpers ---
def safe_request_get(url, timeout=30, stream=False):
    headers = {"User-Agent": "LLM-Quiz-Agent/1.0"}
    return requests.get(url, headers=headers, timeout=timeout, stream=stream)

def find_submit_url(text):
    m = re.search(r"(https?://[^\s'\"<>]+/submit[^\s'\"<>]*)", text)
    return m.group(1) if m else None

def extract_base64_candidates(text):
    return re.findall(r"([A-Za-z0-9+/=\n]{80,})", text)

def try_decode_base64(chunk):
    try:
        s = "".join(chunk.split())
        dec = base64.b64decode(s, validate=False)
        return dec.decode("utf-8", errors="replace")
    except Exception:
        return None

def find_data_links(text, base_url=None):
    exts = r"(https?://[^\s'\"<>]+?\.(?:pdf|csv|xlsx|xls|json)(?:\?[^\s'\"<>]*)?)"
    found = re.findall(exts, text, flags=re.IGNORECASE)
    if not found and base_url:
        rels = re.findall(r'href=[\'\"]([^\'\"]+\.(?:pdf|csv|xlsx|xls|json))', text, flags=re.IGNORECASE)
        for r in rels:
            found.append(urljoin(base_url, r))
    return list(dict.fromkeys(found))

def download_to_temp(url, timeout=60):
    logger.info("Downloading: %s", url)
    r = safe_request_get(url, timeout=timeout, stream=True)
    r.raise_for_status()
    suffix = os.path.splitext(urlparse(url).path)[1]
    fd, path = tempfile.mkstemp(suffix=suffix if suffix else ".dat")
    os.close(fd)
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    return path

def sum_column_from_dataframe(df, colnames=None):
    if colnames:
        for c in colnames:
            if c and c in df.columns:
                try:
                    return int(df[c].astype(float).sum())
                except Exception:
                    pass
    for candidate in ["value","Value","VALUE","amount","Amount","quantity","Quantity","total","Total"]:
        if candidate in df.columns:
            try:
                return int(df[candidate].astype(float).sum())
            except Exception:
                pass
    for col in df.columns:
        try:
            series = pd.to_numeric(df[col], errors="coerce")
            if series.notna().any():
                return int(series.sum(skipna=True))
        except Exception:
            continue
    return None

def extract_from_pdf(path, target_page=None):
    tables = []
    with pdfplumber.open(path) as pdf:
        if target_page and 1 <= target_page <= len(pdf.pages):
            pages_to_scan = [pdf.pages[target_page-1]]
        else:
            pages_to_scan = pdf.pages
        for page in pages_to_scan:
            try:
                page_tables = page.extract_tables()
                for t in page_tables:
                    if t and len(t) > 0:
                        df = pd.DataFrame(t[1:], columns=t[0])
                        tables.append(df)
            except Exception:
                continue
    return tables

def compute_answer_from_text_and_page(text, page_obj, base_url=None, time_left=60):
    for cand in extract_base64_candidates(text):
        dec = try_decode_base64(cand)
        if dec:
            try:
                j = json.loads(dec)
                file_url = j.get("url") or j.get("file") or j.get("file_url")
                col = j.get("column") or j.get("col") or j.get("column_name")
                page_num = j.get("page") or j.get("page_number")
                if file_url:
                    try:
                        path = download_to_temp(file_url)
                        ans = compute_answer_from_file(path, col, page_num)
                        if ans is not None:
                            return ans, {"source":"decoded-json","file":file_url,"col":col,"page":page_num}
                    except Exception as e:
                        logger.info("download/compute failed from decoded json: %s", e)
            except Exception:
                pass
    data_links = find_data_links(text, base_url=base_url)
    if data_links:
        for link in data_links:
            try:
                path = download_to_temp(link)
                ans = compute_answer_from_file(path, None, None, time_left=time_left)
                if ans is not None:
                    return ans, {"source":"data-link","link":link}
            except Exception as e:
                logger.info("failed to handle link %s : %s", link, e)
    try:
        pre = page_obj.query_selector("pre")
        if pre:
            pre_text = pre.inner_text()
            try:
                j = json.loads(pre_text)
                file_url = j.get("url") or j.get("file") or j.get("file_url")
                col = j.get("column") or j.get("col")
                page_num = j.get("page") or j.get("page_number")
                if file_url:
                    path = download_to_temp(file_url)
                    ans = compute_answer_from_file(path, col, page_num)
                    if ans is not None:
                        return ans, {"source":"pre-json","file":file_url}
            except Exception:
                pass
    except Exception:
        pass
    m = re.search(r"sum of the [\"']?(\w+)[\"']? column.*page\s*(\d+)", text, flags=re.I)
    if m:
        col = m.group(1)
        page_requested = int(m.group(2))
        for link in data_links:
            if link.lower().endswith(".pdf"):
                try:
                    path = download_to_temp(link)
                    ans = compute_answer_from_file(path, col, page_requested)
                    if ans is not None:
                        return ans, {"source":"heuristic-text","file":link,"col":col,"page":page_requested}
                except Exception as e:
                    logger.info("pdf heuristic failed: %s", e)
    numbers = re.findall(r"[-+]?\d+", text)
    if numbers:
        return int(numbers[0]), {"source":"fallback-first-number"}
    return None, {"source":"unable-to-compute"}

def compute_answer_from_file(path, column_hint=None, page_hint=None, time_left=60):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in [".csv"]:
            df = pd.read_csv(path)
            val = sum_column_from_dataframe(df, colnames=[column_hint] if column_hint else None)
            return val
        if ext in [".xls", ".xlsx"]:
            df = pd.read_excel(path, sheet_name=0)
            val = sum_column_from_dataframe(df, colnames=[column_hint] if column_hint else None)
            return val
        if ext in [".json"]:
            with open(path, "r", encoding="utf-8") as f:
                j = json.load(f)
            if isinstance(j, list) and len(j) > 0 and isinstance(j[0], dict):
                df = pd.DataFrame(j)
                val = sum_column_from_dataframe(df, colnames=[column_hint] if column_hint else None)
                return val
            return None
        if ext == ".pdf":
            target_page = page_hint or None
            tables = extract_from_pdf(path, target_page)
            for df in tables:
                val = sum_column_from_dataframe(df, colnames=[column_hint] if column_hint else None)
                if val is not None:
                    return val
            text = ""
            with pdfplumber.open(path) as pdf:
                if target_page and 1 <= target_page <= len(pdf.pages):
                    text = pdf.pages[target_page-1].extract_text() or ""
                else:
                    for p in pdf.pages:
                        text += "\n" + (p.extract_text() or "")
            numbers = re.findall(r"[-+]?\d+", text)
            if numbers:
                return int(numbers[0])
            return None
    except Exception as e:
        logger.exception("compute_from_file failed: %s", e)
        return None

def solve_single_url(start_url, email, secret):
    start_time = time.time()
    deadline = start_time + MAX_TOTAL_SECONDS
    current_url = start_url
    session_results = []
    iteration = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        while True:
            iteration += 1
            elapsed = time.time() - start_time
            if time.time() > deadline:
                logger.warning("Time expired before finishing (elapsed %.1fs)", elapsed)
                break
            try:
                page.goto(current_url, timeout=PAGE_LOAD_TIMEOUT_MS)
                page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
            except PWTimeout:
                logger.info("Page load timeout for %s", current_url)
            except Exception as e:
                logger.exception("navigation error: %s", e)
                break
            rendered_text = ""
            try:
                rendered_text = page.evaluate("() => document.body.innerText")
            except Exception:
                rendered_text = page.content()
            submit_url = find_submit_url(rendered_text)
            if not submit_url:
                for cand in extract_base64_candidates(rendered_text):
                    dec = try_decode_base64(cand)
                    if dec:
                        s = dec + "\n" + rendered_text
                        rendered_text = s
                        if not submit_url:
                            submit_url = find_submit_url(s)
            ans, dbg = compute_answer_from_text_and_page(rendered_text, page, base_url=current_url, time_left=(deadline-time.time()))
            logger.info("Iteration %d computed ans=%s dbg=%s", iteration, str(ans), dbg)
            if not submit_url:
                try:
                    anchors = page.query_selector_all("a")
                    for a in anchors:
                        href = a.get_attribute("href")
                        if href and "/submit" in href:
                            submit_url = href if href.startswith("http") else urljoin(current_url, href)
                            break
                except Exception:
                    pass
            if submit_url and ans is not None:
                payload = {"email": email, "secret": secret, "url": current_url, "answer": ans}
                try:
                    logger.info("POSTing answer to %s : %s", submit_url, payload)
                    resp = requests.post(submit_url, json=payload, timeout=30)
                    try:
                        resp_json = resp.json()
                    except Exception:
                        resp_json = {"status_code": resp.status_code, "text": resp.text[:1000]}
                    session_results.append({"url": current_url, "answer": ans, "submit_response": resp_json, "dbg": dbg})
                    new_url = resp_json.get("url") if isinstance(resp_json, dict) else None
                    if new_url:
                        current_url = new_url
                        logger.info("Received next url: %s", new_url)
                        continue
                    else:
                        browser.close()
                        return {"success": True, "results": session_results}
                except Exception as e:
                    logger.exception("error posting answer: %s", e)
                    session_results.append({"url": current_url, "answer": ans, "post_error": str(e), "dbg": dbg})
                    browser.close()
                    return {"success": False, "results": session_results, "reason": "post_error"}
            else:
                session_results.append({"url": current_url, "answer": ans, "dbg": dbg, "submit_url": submit_url})
                logger.info("Could not compute or missing submit URL; ending.")
                browser.close()
                return {"success": False, "results": session_results, "reason": "could_not_compute_or_no_submit_url"}
    return {"success": False, "results": session_results, "reason": "timeout_or_other"}

from flask import Flask
app = Flask(__name__)

@app.route("/llm-analysis-quiz", methods=["POST"])
def receive_trigger():
    try:
        data = request.get_json(force=True)
    except Exception:
        abort(400, description="Invalid JSON")
    email = data.get("email")
    secret = data.get("secret")
    url = data.get("url")
    if not (email and secret and url):
        abort(400, description="Missing required fields (email, secret, url)")
    if secret != SECRET:
        abort(403, description="Invalid secret")
    result = solve_single_url(url, email, secret)
    return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
