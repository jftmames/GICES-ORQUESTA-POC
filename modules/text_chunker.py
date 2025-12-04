from dataclasses import dataclass
from typing import List

from .pdf_loader import PDFDocument


@dataclass
class TextChunk:
    chunk_id: str
    doc_id: str
    page: int
    position: int
    text: str


def chunk_documents(
    documents: List[PDFDocument],
    chunk_size: int = 800,      # nº aproximado de palabras por chunk
    overlap: int = 200,         # solapamiento entre chunks
) -> List[TextChunk]:
    """Fragmenta documentos en chunks de texto con metadatos (doc, página, posición)."""
    chunks: List[TextChunk] = []

    for doc in documents:
        for page in doc.pages:
            words = page.text.split()
            if not words:
                continue

            start = 0
            position = 1

            while start < len(words):
                end = start + chunk_size
                fragment_words = words[start:end]
                text = " ".join(fragment_words).strip()

                if not text:
                    break

                chunk_id = f"{doc.doc_id}_p{page.page_number}_c{position}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        page=page.page_number,
                        position=position,
                        text=text,
                    )
                )

                if end >= len(words):
                    break

                # Retrocede solapando overlap palabras
                start = max(0, end - overlap)
                position += 1

    return chunks
