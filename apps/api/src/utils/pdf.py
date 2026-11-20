"""
Brainly API - PDF Processing Utilities

Extract text and tables from PDF files using PyMuPDF and pdfplumber.
"""
import io
from typing import Any
import fitz  # PyMuPDF
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from PDF using PyMuPDF.

    Fast and handles most PDFs well.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{text}")

    doc.close()
    return "\n\n".join(text_parts)


def extract_tables_from_pdf(file_bytes: bytes) -> list[dict[str, Any]]:
    """
    Extract tables from PDF using pdfplumber.

    Returns list of tables with markdown representation.
    """
    tables = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            extracted_tables = page.extract_tables()
            for table_idx, table in enumerate(extracted_tables):
                if table and len(table) > 1:  # Has header + data
                    markdown = _table_to_markdown(table)
                    tables.append({
                        "page": page_num + 1,
                        "table_index": table_idx,
                        "markdown": markdown,
                        "rows": len(table),
                        "cols": len(table[0]) if table else 0,
                    })

    return tables


def _table_to_markdown(table: list[list[str | None]]) -> str:
    """Convert table to markdown format."""
    if not table:
        return ""

    # Clean cells
    clean_table = []
    for row in table:
        clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
        clean_table.append(clean_row)

    if not clean_table:
        return ""

    # Header
    header = clean_table[0]
    markdown = "| " + " | ".join(header) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(header)) + " |\n"

    # Data rows
    for row in clean_table[1:]:
        markdown += "| " + " | ".join(row) + " |\n"

    return markdown


def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    """
    Extract all content from PDF: text + tables.

    Returns combined content for chunking.
    """
    text = extract_text_from_pdf(file_bytes)
    tables = extract_tables_from_pdf(file_bytes)

    # Append tables as markdown to text
    if tables:
        table_text = "\n\n=== TABLES ===\n\n"
        for table in tables:
            table_text += f"[Page {table['page']}, Table {table['table_index'] + 1}]\n"
            table_text += table["markdown"] + "\n\n"
        text += table_text

    return {
        "text": text,
        "tables": tables,
        "page_count": len(tables) > 0 and max(t["page"] for t in tables) or 1,
    }