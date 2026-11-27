
"""
PyMuPDF (fitz) smart router to discriminate digital text PDFs from scanned PDFs
and legacy-encoded Tamil newspaper clippings.
Routes digital PDFs to text prompts (~70% token savings) and scanned/image documents
to Gemini Multimodal Vision.
"""

import logging
import mimetypes
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

logger = logging.getLogger("auction_engine.router")


class RoutePath(str, Enum):
    """Execution pathway for OCR / extraction."""
    DIGITAL_TEXT = "DIGITAL_TEXT"
    MULTIMODAL_VISION = "MULTIMODAL_VISION"


@dataclass
class RoutedDocument:
    """Routing metadata and payload ready for LLM consumption."""
    route: RoutePath
    mime_type: str
    text_content: Optional[str] = None
    file_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    page_count: int = 1
    reason: str = ""


# Keywords indicating genuine SARFAESI sale notice text
SARFAESI_KEYWORDS = ("reserve", "emd", "sarfaesi", "survey")

# Known non-Unicode legacy Tamil font names used in Indian regional newspapers & deeds
LEGACY_TAMIL_FONTS = (
    "bamini",
    "tab",
    "tam_",
    "senthamil",
    "vanavil",
    "kamban",
    "softview",
    "shree",
    "dinamani",
    "vikatan",
    "tamil",
)


def has_legacy_tamil_encoding(doc: "fitz.Document", text: str) -> bool:
    """
    Detect whether a PDF uses legacy ASCII-mapped Tamil fonts (Bamini, TAB, TAM)
    which result in corrupted mojibake when read as plain digital text.
    """
    # 1. Inspect font metadata across all pages
    for page_index in range(len(doc)):
        try:
            fonts = doc.get_page_fonts(page_index)
            for font in fonts:
                font_name = (font[3] or "").lower()
                if any(leg in font_name for leg in LEGACY_TAMIL_FONTS):
                    logger.info("Detected legacy Tamil font '%s' on page %d", font_name, page_index + 1)
                    return True
        except Exception as e:
            logger.debug("Could not inspect page fonts: %s", e)

    # 2. Check for characteristic glyph corruption / replacement indicators
    if "\ufffd" in text and text.count("\ufffd") > 5:
        return True

    return False


def route_document(
    input_source: Union[str, Path, bytes],
    file_name: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> RoutedDocument:
    """
    Evaluate document content and route to DIGITAL_TEXT or MULTIMODAL_VISION.

    Rules:
      1. Image files (.jpg, .png, .webp, etc.) -> MULTIMODAL_VISION directly.
      2. PDF files with PyMuPDF:
         - Count total alphanumeric characters.
         - Check for presence of SARFAESI keywords.
         - Check for legacy Tamil font encodings.
         - If alphanumeric count >= 300 AND has keywords AND NOT legacy Tamil -> DIGITAL_TEXT.
         - Otherwise -> MULTIMODAL_VISION.
    """
    file_bytes: Optional[bytes] = None
    file_path_str: Optional[str] = None
    resolved_mime = mime_type

    # Determine input type & load bytes/path
    if isinstance(input_source, (str, Path)):
        path = Path(input_source)
        file_path_str = str(path.resolve())
        if not path.exists():
            raise FileNotFoundError(f"Input document not found: {file_path_str}")
        file_bytes = path.read_bytes()
        if not resolved_mime:
            guessed_mime, _ = mimetypes.guess_type(file_path_str)
            resolved_mime = guessed_mime or "application/octet-stream"
        if not file_name:
            file_name = path.name
    elif isinstance(input_source, bytes):
        file_bytes = input_source
        if not resolved_mime:
            if file_name:
                guessed_mime, _ = mimetypes.guess_type(file_name)
                resolved_mime = guessed_mime or "application/pdf"
            else:
                resolved_mime = "application/pdf"

    # Identify if image
    ext = Path(file_name or "").suffix.lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp") or (
        resolved_mime and resolved_mime.startswith("image/")
    )

    if is_image:
        return RoutedDocument(
            route=RoutePath.MULTIMODAL_VISION,
            mime_type=resolved_mime or "image/jpeg",
            file_bytes=file_bytes,
            file_path=file_path_str,
            page_count=1,
            reason="Image notice file (newspaper clipping) routes to Multimodal Vision",
        )

    # If PyMuPDF is not installed, fallback to vision for PDFs
    if fitz is None:
        logger.warning("PyMuPDF (fitz) is not installed. Routing document to Multimodal Vision.")
        return RoutedDocument(
            route=RoutePath.MULTIMODAL_VISION,
            mime_type=resolved_mime or "application/pdf",
            file_bytes=file_bytes,
            file_path=file_path_str,
            page_count=1,
            reason="PyMuPDF unavailable; falling back to Multimodal Vision",
        )

    # Process PDF with PyMuPDF
    try:
        if file_bytes:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        else:
            doc = fitz.open(file_path_str)

        page_count = len(doc)
        page_texts: List[str] = []

        for pno in range(page_count):
            page_texts.append(doc[pno].get_text("text", sort=True))

        full_text = "\n".join(page_texts)
        alphanumeric_chars = re.findall(r"[a-zA-Z0-9]", full_text)
        alphanumeric_count = len(alphanumeric_chars)
        lower_text = full_text.lower()

        has_sarfaesi_keywords = any(kw in lower_text for kw in SARFAESI_KEYWORDS)
        legacy_tamil = has_legacy_tamil_encoding(doc, full_text)

        doc.close()

        # Decision rule: >= 300 alphanumeric chars, has keywords, and no legacy fonts
        if alphanumeric_count >= 300 and has_sarfaesi_keywords and not legacy_tamil:
            return RoutedDocument(
                route=RoutePath.DIGITAL_TEXT,
                mime_type="text/plain",
                text_content=full_text,
                file_bytes=file_bytes,
                file_path=file_path_str,
                page_count=page_count,
                reason=f"Digital PDF with {alphanumeric_count} chars and SARFAESI keywords",
            )
        else:
            reasons = []
            if alphanumeric_count < 300:
                reasons.append(f"low character count ({alphanumeric_count} < 300)")
            if not has_sarfaesi_keywords:
                reasons.append("missing SARFAESI keywords")
            if legacy_tamil:
                reasons.append("legacy Bamini/TAB Tamil encoding detected")

            return RoutedDocument(
                route=RoutePath.MULTIMODAL_VISION,
                mime_type="application/pdf",
                file_bytes=file_bytes,
                file_path=file_path_str,
                page_count=page_count,
                reason=f"Scanned / legacy PDF: {', '.join(reasons)}",
            )

    except Exception as e:
        logger.warning("PyMuPDF failed to process PDF: %s. Routing to Multimodal Vision.", e)
        return RoutedDocument(
            route=RoutePath.MULTIMODAL_VISION,
            mime_type=resolved_mime or "application/pdf",
            file_bytes=file_bytes,
            file_path=file_path_str,
            page_count=1,
            reason=f"PyMuPDF parse error ({e}); falling back to Multimodal Vision",
        )


def extract_pdf_images(file_source: Union[str, Path, bytes], min_size_bytes: int = 2048) -> List[bytes]:
    """
    Extract embedded property photographs, building plans, and scans from PDF pages.
    Filters out small icons, borders, or watermark graphics smaller than min_size_bytes.
    """
    images = []
    if not fitz:
        return images
    try:
        if isinstance(file_source, bytes):
            doc = fitz.open(stream=file_source, filetype="pdf")
        else:
            doc = fitz.open(str(file_source))

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                base_img = doc.extract_image(xref)
                img_bytes = base_img.get("image")
                # Filter out tiny bullets, icons, or horizontal rules (< 2KB)
                if img_bytes and len(img_bytes) >= min_size_bytes:
                    images.append(img_bytes)
    except Exception as e:
        logger.debug("PDF image extraction notice: %s", e)
    return images
