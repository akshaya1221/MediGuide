import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import fitz
import pytesseract
from PIL import Image


@dataclass
class ExtractionResult:
    text: str
    confidence: float
    used_ocr: bool


def _ocr_image(image: Image.Image) -> tuple[str, float]:
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words: list[str] = []
    confidences: list[float] = []
    for word, confidence in zip(data["text"], data["conf"], strict=False):
        word = word.strip()
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            score = -1
        if word:
            words.append(word)
            if score >= 0:
                confidences.append(score)
    return " ".join(words), (sum(confidences) / len(confidences) / 100 if confidences else 0.45)


def extract_text(path: Path, content_type: str) -> ExtractionResult:
    if content_type.startswith("image/"):
        text, confidence = _ocr_image(Image.open(path).convert("RGB"))
        return ExtractionResult(text=text, confidence=confidence, used_ocr=True)

    doc = fitz.open(path)
    direct_pages = [page.get_text("text").strip() for page in doc]
    direct_text = "\n\n".join(text for text in direct_pages if text)
    if len(direct_text) >= 80:
        return ExtractionResult(text=direct_text, confidence=0.99, used_ocr=False)

    texts: list[str] = []
    scores: list[float] = []
    for page in doc:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
        text, confidence = _ocr_image(image)
        texts.append(text)
        scores.append(confidence)
    return ExtractionResult(text="\n\n".join(texts), confidence=sum(scores) / len(scores) if scores else 0, used_ocr=True)


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


DATE_PATTERNS = [r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", r"\b(\d{4}-\d{2}-\d{2})\b"]
LAB_PATTERN = re.compile(
    r"(?im)^\s*([A-Za-z][A-Za-z0-9 ()/%+-]{2,45}?)\s*[:\-]?\s+(\d+(?:\.\d+)?)\s*([a-zA-Z/%µμ][a-zA-Z0-9/%µμ.^-]{0,15})?\s*$"
)
MED_PATTERN = re.compile(
    r"(?im)\b(?:tab(?:let)?|cap(?:sule)?|syrup|inj(?:ection)?)\.?\s+([A-Za-z][A-Za-z0-9-]{2,40})(?:\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|ml)))?(?:\s+([^\n]{0,80}))?"
)


def extract_structured_items(text: str, confidence: float) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text):
            key = ("date", match.group(1))
            if key not in seen:
                seen.add(key)
                items.append({"data_type": "date", "item_name": "Mentioned date", "item_value": match.group(1), "confidence": confidence, "source_text": match.group(0)})
    for match in LAB_PATTERN.finditer(text):
        name, value, unit = (part.strip() if part else None for part in match.groups())
        if not name or any(token in name.lower() for token in ("phone", "age", "page")):
            continue
        key = (name.lower(), value or "")
        if key not in seen:
            seen.add(key)
            items.append({"data_type": "lab_value", "item_name": name[:120], "item_value": value or "", "unit": unit, "confidence": confidence, "source_text": match.group(0).strip()})
    return items[:100]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def heuristic_medications(text: str) -> list[dict[str, str | bool | None]]:
    medications: list[dict[str, str | bool | None]] = []
    for match in MED_PATTERN.finditer(text):
        name, dosage, timing = match.groups()
        medications.append({
            "name": name,
            "dosage_text": dosage,
            "timing_text": timing.strip(" .,-") if timing else None,
            "source_text": match.group(0).strip(),
            "needs_confirmation": True,
        })
    return medications[:20]


def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
    chunks: list[str] = []
    cursor = 0
    while cursor < len(text):
        end = min(len(text), cursor + chunk_size)
        if end < len(text):
            boundary = max(text.rfind("\n", cursor, end), text.rfind(". ", cursor, end))
            if boundary > cursor + chunk_size // 2:
                end = boundary + 1
        chunks.append(text[cursor:end].strip())
        cursor = max(end - overlap, cursor + 1)
    return [chunk for chunk in chunks if chunk]

