# utils/ocr_utils.py
import io
from PIL import Image
import pytesseract

def ocr_image_bytes(img_bytes: bytes) -> str:
    """Run Tesseract OCR on image bytes and return extracted text."""
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return ""
