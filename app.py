import os
import time
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from openai import OpenAI

# Intentamos importar yaml (pyyaml). Si no está instalada,
# degradamos a un modo sin catálogo para que la app no se caiga.
try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    yaml = None

from modules.pdf_loader import load_pdfs
from modules.text_chunker import chunk_documents
from modules.embeddings_engine import compute_embeddings
from modules.knowledge_builder import build_knowledge_vectors, save_knowledge_vectors


# ---------------------------
# Utilidades para OpenAI
# ---------------------------

def get_openai_client() -> OpenAI | None:
    """
    Inicializa el cliente de OpenAI.
    Intenta primero con st.secrets y luego con variables de entorno.
    """
    api_key: str | None = None

    # Streamlit Cloud: secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        # Fallback: variable de entorno (por si se ejecuta en otro entorno)
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


# ---------------------------
# Utilidades para sources.yaml
# ---------------------------

def load_sources_catalog(catalog_path: Path) -> Dict[str, Any] | None:
    """
    Carga el catálogo de fuentes normativas desde sources.yaml, si existe.
    Si 'yaml' (pyyaml) no está disponible, devuelve None y muestra un aviso.
    """
    if yaml is None:
        # Dependencia no instalada: no rompemos la app, solo desactivamos esta función
        st.info(
            "La librería 'pyyaml' no está instalada. "
            "Se omite la lectura de `sources.yaml`, pero la indexación de PDFs funciona igual."
        )
        return None

    try:
        with catalog_path.open("r", encoding="utf-8") as f:
            catalog: Dict[str, Any] = yaml.safe_load(f)
        return catalog
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error al leer sources.yaml: {e}")
        return None


def check_sources_coverage(
    catalog: Dict[str, Any],
    kb_path: Path,
) -> List[Dict[str, Any]]:
    """
    Compara las fuentes definidas en sources.yaml con los ficheros
    realmente presentes en rag/knowledge_base.
    Devuelve una lista de filas con id, label, filename y exists.
    """
    rows: List[Dict[str, Any]] = []
    sources = catalog.get("sources", []) or []

    for src in sources:
        repo_filename = src.get("repo_filename")
        if not repo_filename:
            continue

        expected_path = kb_path / repo_filename
        exists = expected_path.exists()

        rows.append(
            {
                "id": src.get("id", ""),
                "label": src.get("label", ""),
                "filename": repo_filename,
                "exists": "✅" if exists else "❌",
            }
        )

    return rows


# ---------------------------
# Aplicación principal
# ---------------------------

def main() -> None:
    st.set_page_config(
        page_title="GICES · Motor de Inteligencia Vectorial",
        layout="wide",
    )

    st.title("GICES · Motor de Inteligencia Vectorial (Ingesta y Contexto)")
    st.caption("Componente 01 — Indexación de normativa UE/ES y generación de `knowledge_vectors.json`")

    base_path = Path(__file__).parent
    kb_path = base_path / "rag" / "knowledge_base"
    output_path = base_path / "rag" / "knowledge_vectors.json"
    catalog_path = base_path / "sources.yaml"

    kb_path.mkdir(parents=True, exist_ok=True)

    # 1) Carga de PDFs disponibles en la carpeta
    pdf_files = sorted(kb_path.glob("*.pdf"))

    st.subheader("Munición disponible (PDFs de normativa)")
    st.write(f"Carpeta de entrada: `{kb_path}`")
    st.write(f"PDFs detectados: **{len(pdf_files)}**")

    if pdf_files:
        with st.expander("Ver lista de PDFs cargados"):
            for p in pdf_files:
                st.write(f"- {p.name}")
    else:
        st.info(
            "No se han encontrado documentos en `rag/knowledge_base`.\n\n"
            "Sube aquí los Reglamentos, Directivas y demás PDFs que quieras indexar."
        )

    # 2) Carga del catálogo de fuentes (sources.yaml), si existe
    catalog = load_sources_catalog(catalog_path)

    if catalog is not None:
        coverage_rows = check_sources_coverage(catalog, kb_path)
        total_defined = len(coverage_rows)
        total_present = sum(1 for r in coverage_rows if r["exists"] == "✅")

        st.subheader("Cobertura de fuentes normativas (sources.yaml)")
        st.write(
            f"Fuentes definidas en catálogo: **{total_defined}** · "
            f"Fuentes presentes en `rag/knowledge_base`: **{total_present}**"
        )

        with st.expander("Detalle de cobertura de fuentes"):
            if coverage_rows:
                st.dataframe(coverage_rows, use_container_width=True)
            else:
                st.write("No se han encontrado entradas en `sources.yaml`.")
    else:
        st.warning(
            "No se ha encontrado `sources.yaml` en la raíz del proyecto o no se ha podido leer.\n\n"
            "Puedes crear este archivo para documentar y auditar las fuentes normativas "
            "que deberían estar cargadas en `rag/knowledge_base`."
        )

    # 3) Comprobación del cliente de OpenAI
    client = get_openai_client()
    if client is None:
        st.warning(
            "No se ha encontrado `OPENAI_API_KEY` ni en `st.secrets` ni en variables de entorno.\n"
            "Configura la clave antes de ejecutar la indexación."
        )

    st.markdown("---")

    # 4) Botón principal de indexación
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


