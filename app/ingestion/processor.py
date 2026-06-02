# processor.py extracts raw text from uploaded documents.
# Supports PDF and DOCX — the two most common academic formats.
#
# Why separate extraction from chunking?
# Different file types require different parsing libraries.
# Keeping extraction isolated means adding new file types
# (e.g. .pptx, .txt) only requires adding one new function here
# without touching anything else in the pipeline.
#
# Libraries:
# pypdf — extracts text from PDF files page by page
# python-docx — extracts text from DOCX paragraphs

import os
from pypdf import PdfReader
from docx import Document
from loguru import logger
from app.core.settings import APP_NAME

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file by reading each page.
    Pages are joined with double newlines to preserve structure.

    Args:
        file_path: Absolute path to the PDF file

    Returns:
        Full extracted text as a single string

    Raises:
        ValueError: If the PDF contains no extractable text
        FileNotFoundError: If the file path does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    logger.info(f"[{APP_NAME}] Processor: Extracting text from PDF — {file_path}")

    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
        else:
            logger.warning(f"[{APP_NAME}] Processor: Page {i+1} has no extractable text — skipping")

    if not pages:
        raise ValueError(f"No extractable text found in PDF: {file_path}")

    full_text = "\n\n".join(pages)
    logger.info(f"[{APP_NAME}] Processor: Extracted {len(pages)} pages, {len(full_text)} characters")
    return full_text


def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts all text from a DOCX file by reading each paragraph.
    Empty paragraphs are filtered out to reduce noise.

    Args:
        file_path: Absolute path to the DOCX file

    Returns:
        Full extracted text as a single string

    Raises:
        ValueError: If the DOCX contains no extractable text
        FileNotFoundError: If the file path does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    logger.info(f"[{APP_NAME}] Processor: Extracting text from DOCX — {file_path}")

    doc = Document(file_path)
    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        raise ValueError(f"No extractable text found in DOCX: {file_path}")

    full_text = "\n\n".join(paragraphs)
    logger.info(f"[{APP_NAME}] Processor: Extracted {len(paragraphs)} paragraphs, {len(full_text)} characters")
    return full_text


def extract_text(file_path: str, file_type: str) -> str:
    """
    Routes document extraction to the correct parser
    based on the file type.

    Args:
        file_path: Absolute path to the uploaded file
        file_type: File extension — 'pdf' or 'docx'

    Returns:
        Full extracted text as a single string

    Raises:
        ValueError: If the file type is not supported
    """
    file_type = file_type.lower().strip(".")

    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(
            f"Unsupported file type: '{file_type}'. "
            f"HERVEX currently supports PDF and DOCX."
        )
