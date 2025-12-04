import streamlit as st
import time
# Importamos gices_brain para la lógica de embeddings
try:
    import modules.gices_brain as gices_brain 
except ImportError:
    st.error("❌ Error CRÍTICO: No se encuentra 'modules.gices_brain'.")
    gices_brain = None

# Importamos las rutas y utilidades compartidas
try:
    import modules.shared_helpers as sh
except ImportError:
    st.error("❌ Error CRÍTICO: No se encuentra 'modules.shared_helpers'.")
    sh = None

# --- APP PRINCIPAL (01_Ingesta_y_Contexto.py) ---
def main():
    st.set_page_config(
        page_title="GICES ORQUESTA - 01. INGESTA Y PREPARACIÓN",
        page_icon="📚",
        layout="wide"
    )

    st.title("🎓 GICES ORQUESTA - 01. INGESTA Y PREPARACIÓN DE DATOS")
    st.caption("Paso 1 del Pipeline: Carga de Normativa (Munición) y Generación de Inteligencia Vectorial (ESRS E4)")

    if not sh or not gices_brain:
        return

    col_files, col_data_sample = st.columns([1, 2])

    # --- COLUMNA IZQUIERDA: CONTROL DE MUNICIÓN (NORMATIVA) ---
    with col_files:
        st.subheader("1. Biblioteca Normativa (Munición)")
        st.markdown("**La información que entra son los PDFs de Leyes y Normas (Pluralidad de Fuentes).**")
        
        pdf_files = []
        if sh.KB_PATH.exists():
            pdf_files = list(sh.KB_PATH.glob("*.pdf"))
            if pdf_files:
                for f in pdf_files: 
                    st.success(f"📘 {f.name[:35]}...")
            else:
                st.warning("⚠️ No se encontraron PDFs en rag/knowledge_base.")
        else: 
            st.error("❌ Falta directorio rag/knowledge_base")
        
        st.divider()
        
        if st.button("🔄 Indexar PDFs y Crear Vectores", type="primary"):
            start_time = time.time()
            total_fragments = 0
            
            # Protocolo de Transparencia: Usamos st.status para el log visible
            with st.status("⚙️ **Fase 1: Preparación del Motor Vectorial...**", expanded=True) as status:
                
                # 1. Crear la barra de progreso (Telemetría)
                progress_bar = st.empty()
                
                def update_ui(percent, message):
                    progress_bar.progress(percent, text=message)

                status.write(f"Inicio de Operación: {time.ctime()} (Transparencia Activa)")
                status.write("Proceso: Conectando a la API de Embeddings de OpenAI...")

                if pdf_files:
                    try:
                        knowledge_base = gices_brain.ingest_pdfs(str(sh.KB_PATH), progress_callback=update_ui)
                        total_fragments = len(knowledge_base)

                        status.update(label="✅ **Fase 1: Motor Vectorial Completado**", state="complete", expanded=True)
                        
                        # 3. Diagnóstico Final
                        end_time = time.time()
                        
                        st.expander("🔬 **Diagnóstico del Motor Vectorial**", expanded=True).json({
                            "Estado": "Operativo. Base de Conocimiento Creada.",
                            "Archivos Procesados (Pluralidad)": len(pdf_files),
                            "Fragmentos Vectorizados": total_fragments,
                            "Ruta de Persistencia (Memoria Cache)": str(sh.ROOT_DIR / "rag" / "knowledge_vectors.json"),
                            "Tiempo Total de Ejecución": f"{end_time - start_time:.2f} segundos"
                        })
                        
                        progress_bar.empty()
                    except Exception as e:
                        status.update(label="❌ **Fallo Crítico en Ingesta**", state="error", expanded=True)
                        st.error(f"Error: {e}")
                else:
                    status.update(label="❌ **Fallo: Requisitos no cumplidos**", state="error", expanded=True)
        else:
            if (sh.ROOT_DIR / "rag" / "knowledge_vectors.json").exists():
                st.success("🧠 Memoria Vectorial cargada y persistida. Lista para el razonamiento.")
            else:
                st.info("Pulsa el botón para crear la memoria vectorial (embeddings).")

    # --- COLUMNA DERECHA: CONTEXTO DE AUDITORÍA (DATO DE CAMPO) ---
    with col_data_sample:
        st.subheader("2. Dato de Campo (Reporte de la Empresa)")
        st.caption("Esta información **NO** se procesa aquí. Solo se muestra como contexto.")
        
        data_to_audit = sh.load_sample_data("biodiversity_2024.json")
        st.json(data_to_audit)
        
        st.markdown("---")
        st.subheader("Ruta Crítica del Dato (Flujo de Auditoría)")
        st.markdown(
            """
            - **Función de este Componente (App 01):** Crear la **Memoria ($KB$)** con la Ley.
            - **Punto de Entrada al Pipeline (App 03):** El Dato de Campo entra en la **App 03**, donde se lanza como una pregunta contra la Memoria ($KB$) que usted acaba de crear.
            """
        )

if __name__ == "__main__":
    main()
