import streamlit as st
import json
import time
from pathlib import Path

# Importamos utilidades compartidas
try:
    import modules.shared_helpers as sh
except ImportError:
    st.error("❌ Error CRÍTICO: No se encuentra 'modules.shared_helpers'.")
    sh = None

# --- APP PRINCIPAL (02_RAGA_Deliberacion.py) ---
def main():
    st.set_page_config(
        page_title="GICES ORQUESTA - 02. DELIBERACIÓN RAGA",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 GICES ORQUESTA - 02. MOTOR DE RAZONAMIENTO (RAGA)")
    st.caption("Paso 2 del Pipeline: Ejecución del Análisis y Generación del Veredicto Ético/Jurídico.")
    
    if not sh:
        return
        
    if 'run_done' not in st.session_state: st.session_state.run_done = False

    # Protocolo de Transparencia: Envolvemos la ejecución en logs visibles
    if st.button("▶️ EJECUTAR ANÁLISIS INTEGRAL", type="primary", use_container_width=True):
        st.session_state.run_done = False

        st.subheader("Log de Ejecución de Scripts (Trazabilidad de Scripts)")
        st.info("A continuación se simula la validación de estructura y la deliberación ética mediante scripts.")
        
        # sh.run_script ya usa st.status y muestra el stdout
        sh.run_script("mcp_ingest.py", "Validación Estructural (Data Contracts)")
        sh.run_script("raga_compute.py", "Deliberación Ética (Generación de Acta)")
        st.session_state.run_done = True
        time.sleep(0.5)

    st.divider()
    
    # --- VISUALIZACIÓN DEL RESULTADO (Acta de Razonamiento) ---
    data = sh.MOCK_DATA # Usamos los datos de simulación como demo
    
    if data and st.session_state.run_done:
        st.success("✅ Acta de Razonamiento Generada")
        
        with st.container(border=True):
            st.subheader("1. Veredicto")
            st.write(data.get('narrative'))
            c1, c2, c3 = st.columns(3)
            c1.metric("Cumplimiento", data.get('compliance', 'N/A'))
            c2.metric("Riesgo", "MEDIO")
            c3.metric("EEE Score", "0.92")

        c_tree, c_radar = st.columns([3, 2])
        with c_tree:
            st.subheader("2. Árbol de Indagación")
            trace = data.get('reasoning_trace', sh.MOCK_DATA['reasoning_trace'])
            st.graphviz_chart(sh.render_inquiry_tree(trace)) 
        with c_radar:
            st.subheader("3. Calidad (EEE Score)")
            metrics = data.get('eee_metrics', sh.MOCK_DATA['eee_metrics'])
            st.plotly_chart(sh.plot_eee_radar(metrics), use_container_width=True) 

        st.subheader("4. Evidencia Académica")
        evs = data.get('evidence_used', sh.MOCK_DATA['evidence_used'])
        for i, e in enumerate(evs):
            src = e.get('source', 'Fuente GICES')
            txt = e.get('content', str(e))
            with st.expander(f"📖 Cita {i+1}: {src}", expanded=True):
                st.info(f"...{txt[:300]}...")
    elif not st.session_state.run_done:
        st.info("Esperando ejecución. Pulse 'EJECUTAR ANÁLISIS INTEGRAL' para iniciar el proceso.")

if __name__ == "__main__":
    main()
