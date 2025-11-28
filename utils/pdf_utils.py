# utils/pdf_utils.py
import io
from typing import List
import pdfplumber
import pandas as pd

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts text from all pages of a PDF given as bytes."""
    output = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            try:
                output.append(page.extract_text() or "")
            except Exception:
                continue
    return "\n".join(output)

def extract_tables_from_pdf_bytes(pdf_bytes: bytes) -> List[pd.DataFrame]:
    """Extract tables found in a PDF as DataFrames (best-effort)."""
    dfs = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
                for table in tables:
                    # convert to DataFrame, handle empty cells
                    df = pd.DataFrame(table[1:], columns=table[0])
                    dfs.append(df)
            except Exception:
                continue
    return dfs
