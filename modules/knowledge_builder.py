import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .pdf_loader import PDFDocument
from .text_chunker import TextChunk


def build_knowledge_vectors(
    documents: List[PDFDocument],
    chunks: List[TextChunk],
    embeddings: List[List[float]],
    model_name: str = "text-embedding-3-small",
) -> Dict[str, Any]:
    """Combina documentos + chunks + embeddings en la estructura JSON final."""
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Número de chunks ({len(chunks)}) y embeddings ({len(embeddings)}) no coincide."
        )

    docs_by_id = {doc.doc_id: doc for doc in documents}
    documents_out: Dict[str, Dict[str, Any]] = {}

    for chunk, emb in zip(chunks, embeddings):
        doc = docs_by_id.get(chunk.doc_id)
        if doc is None:
            continue

        if chunk.doc_id not in documents_out:
            documents_out[chunk.doc_id] = {
                "doc_id": doc.doc_id,
                "source_path": doc.source_path,
                "title": doc.title,
                "chunks": [],
            }

        documents_out[chunk.doc_id]["chunks"].append(
            {
                "chunk_id": chunk.chunk_id,
                "page": chunk.page,
                "position": chunk.position,
                "text": chunk.text,
                "embedding": emb,
            }
        )

    knowledge: Dict[str, Any] = {
        "metadata": {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "model": model_name,
            "num_documents": len(documents_out),
            "num_chunks": len(chunks),
        },
        "documents": list(documents_out.values()),
    }

    return knowledge


def save_knowledge_vectors(knowledge: Dict[str, Any], output_path: Path) -> None:
    """Guarda la estructura JSON en disco en la ruta indicada."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False)
