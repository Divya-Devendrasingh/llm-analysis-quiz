# llm-analysis-quiz

This repository implements the HTTP endpoint for the **LLM Analysis Quiz** project.

Features:
- FastAPI server that validates incoming requests with a secret
- Headless Playwright rendering for JS-heavy quiz pages
- File fetching and parsing for CSV / XLSX / PDF
- Optional Gemini (Google Generative AI) integration to interpret ambiguous tasks
- Helpers for OCR and PDF table extraction

## Security

**Do not commit real secrets to the repository.** Use environment variables:

- `SECRET` — the secret string registered in the Google Form
- `EMAIL` — your student email (used in submissions)
- `GEMINI_API_KEY` — optional, if you want to enable Gemini for interpretation

## Quickstart (local)

1. Copy `.env.example` to `.env` and set values (do NOT commit `.env`).

2. Install dependencies:

```bash
pip install -r requirements.txt
playwright install --with-deps
```

3. Run the server:

```bash
export SECRET=secret_llm_p2
export EMAIL=25ds10000@ds.study.iitm.ac.in
export GEMINI_API_KEY=""  # optional
uvicorn app:app --reload
```

4. Test with the demo:

```bash
curl -X POST http://127.0.0.1:8000/ -H "Content-Type: application/json" \
  -d '{"email":"25ds10000@ds.study.iitm.ac.in","secret":"secret_llm_p2","url":"https://tds-llm-analysis.s-anand.net/demo"}'
```

## Deployment

Deploy to any HTTPS-capable host (Cloud Run, Render, Railway). Configure environment variables in the platform settings.

## Extending the solver

- Add more robust PDF table extraction with `camelot` or `tabula-py` for complex tabular PDFs.
- Add caching for downloaded files.
- Expand Gemini prompts and parsing strategy for more diverse quiz types.

