from dataclasses import dataclass
from pathlib import Path
from typing import List

import streamlit as st
from pypdf import PdfReader


@dataclass
class PDFPage:
    page_number: int
    text: str


@dataclass
class PDFDocument:
    doc_id: str
    title: str
    source_path: str
    pages: List[PDFPage]


def load_pdfs(pdf_paths: List[Path]) -> List[PDFDocument]:
    """Carga PDFs, extrae texto por página y devuelve una lista de PDFDocument."""
    documents: List[PDFDocument] = []

    for path in pdf_paths:
        try:
            reader = PdfReader(str(path))
            pages: List[PDFPage] = []

            for i, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                text = raw_text.strip()
                if not text:
                    continue

                pages.append(
                    PDFPage(
                        page_number=i + 1,
                        text=text,
                    )
                )

            if not pages:
                st.warning(f"{path.name}: no se ha podido extraer texto útil.")
                continue

            doc_id = path.stem
            documents.append(
                PDFDocument(
                    doc_id=doc_id,
                    title=path.stem,
                    source_path=str(path),
                    pages=pages,
                )
            )

        except Exception as e:
            st.error(f"Error leyendo {path.name}: {e}")

    return documents
