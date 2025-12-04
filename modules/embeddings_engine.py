from typing import List

import streamlit as st
from openai import OpenAI

from .text_chunker import TextChunk


def compute_embeddings(
    client: OpenAI,
    chunks: List[TextChunk],
    model_name: str = "text-embedding-3-small",
    batch_size: int = 64,
) -> List[List[float]]:
    """
    Calcula embeddings para cada chunk utilizando el modelo indicado.
    Muestra barra de progreso en Streamlit.
    """
    texts = [c.text for c in chunks]
    total = len(texts)
    embeddings: List[List[float]] = []

    if total == 0:
        st.warning("No hay chunks de texto para vectorizar.")
        return embeddings

    progress = st.progress(0, text="Generando embeddings...")
    processed = 0

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(
                model=model_name,
                input=batch,
            )
        except Exception as e:
            st.error(f"Error generando embeddings en el batch {i // batch_size + 1}: {e}")
            raise

        for item in response.data:
            embeddings.append(item.embedding)

        processed += len(batch)
        progress.progress(
            processed / total,
            text=f"Generando embeddings… {processed}/{total} fragmentos",
        )

    progress.progress(1.0, text="Embeddings generados.")
    return embeddings
