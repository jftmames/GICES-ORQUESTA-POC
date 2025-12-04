import os
import time
from pathlib import Path

import streamlit as st
from openai import OpenAI

from modules.pdf_loader import load_pdfs
from modules.text_chunker import chunk_documents
from modules.embeddings_engine import compute_embeddings
from modules.knowledge_builder import build_knowledge_vectors, save_knowledge_vectors


def get_openai_client() -> OpenAI | None:
    """
    Inicializa el cliente de OpenAI.
    Intenta primero con st.secrets y luego con variables de entorno.
    """
    api_key = None

    # Streamlit Cloud: secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        # Fallback: variable de entorno (por si lo ejecutas en otro entorno)
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def main() -> None:
    st.set_page_config(
        page_title="GICES · Motor de Inteligencia Vectorial",
        layout="wide",
    )

    st.title("GICES · Motor de Inteligencia Vectorial (Ingesta y Contexto)")
    st.caption("Componente 01 — Indexación de normativa UE y generación de `knowledge_vectors.json`")

    base_path = Path(__file__).parent
    kb_path = base_path / "rag" / "knowledge_base"
    output_path = base_path / "rag" / "knowledge_vectors.json"

    kb_path.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(kb_path.glob("*.pdf"))

    st.subheader("Munición disponible (PDFs de normativa)")
    st.write(f"Carpeta de entrada: `{kb_path}`")
    st.write(f"PDFs detectados: **{len(pdf_files)}**")

    if pdf_files:
        with st.expander("Ver lista de PDFs"):
            for p in pdf_files:
                st.write(f"- {p.name}")
    else:
        st.info(
            "No se han encontrado documentos en `rag/knowledge_base`.\n\n"
            "Sube aquí los Reglamentos, Directivas u otros PDFs que quieras indexar."
        )

    client = get_openai_client()
    if client is None:
        st.warning(
            "No se ha encontrado `OPENAI_API_KEY` ni en `st.secrets` ni en variables de entorno.\n"
            "Configura la clave antes de ejecutar la indexación."
        )

    st.markdown("---")

    if st.button("🔄 Indexar PDFs y Crear Vectores", type="primary", use_container_width=True):
        if not pdf_files:
            st.warning("No se han encontrado PDFs en `/rag/knowledge_base`. Añade documentos y vuelve a intentarlo.")
            return

        if client is None:
            st.error("No hay cliente de OpenAI configurado. Revisa `OPENAI_API_KEY` en los Secrets.")
            return

        start_time = time.time()

        with st.status("Iniciando proceso de indexación…", expanded=True) as status:
            # 1/4 Carga de PDFs
            st.write("1/4 Cargando y extrayendo texto de los PDFs…")
            documents = load_pdfs(pdf_files)
            st.write(f"   → Documentos cargados correctamente: {len(documents)}")

            if not documents:
                status.update(
                    label="No se han podido cargar documentos válidos.",
                    state="error",
                )
                return

            # 2/4 Fragmentación
            st.write("2/4 Fragmentando documentos…")
            chunks = chunk_documents(documents)
            st.write(f"   → Fragmentos generados: {len(chunks)}")

            if not chunks:
                status.update(
                    label="No se han generado fragmentos. Revisa el contenido de los PDFs.",
                    state="error",
                )
                return

            # 3/4 Embeddings
            st.write("3/4 Calculando embeddings con `text-embedding-3-small`…")
            embeddings = compute_embeddings(
                client=client,
                chunks=chunks,
                model_name="text-embedding-3-small",
            )

            # 4/4 Construcción y guardado
            st.write("4/4 Construyendo y guardando `knowledge_vectors.json`…")
            knowledge = build_knowledge_vectors(
                documents=documents,
                chunks=chunks,
                embeddings=embeddings,
                model_name="text-embedding-3-small",
            )
            save_knowledge_vectors(knowledge, output_path)

            status.update(
                label="Indexación completada con éxito ✅",
                state="complete",
            )

        total_time = time.time() - start_time

        st.success("Proceso de indexación finalizado correctamente.")

        with st.expander("Diagnóstico y métricas de indexación", expanded=True):
            st.write(f"Tiempo total: **{total_time:.2f}** segundos")
            st.write(f"Documentos procesados: **{len(documents)}**")
            st.write(f"Fragmentos generados: **{len(chunks)}**")
            st.write("Modelo de embeddings: `text-embedding-3-small`")
            st.write(f"Archivo de salida: `{output_path}`")


if __name__ == "__main__":
    main()

