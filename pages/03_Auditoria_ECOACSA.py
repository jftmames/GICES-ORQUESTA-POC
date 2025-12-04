import streamlit as st
import json

# Importamos el cerebro y utilidades compartidas
try:
    import modules.gices_brain as gices_brain
    import modules.shared_helpers as sh
except ImportError:
    st.error("❌ Error CRÍTICO: Módulos no disponibles. Revise gices_brain.py y shared_helpers.py.")
    gices_brain = None
    sh = None

# --- DATOS DE SIMULACIÓN REALISTA (E4 - Biodiversidad) ---
SIMULATED_DATA = {
    "project_id": "MRN-2024-003",
    "esrs_data_point": "E4-5 (Area de Ecosistema Restaurada)",
    "ecosystem_type": "Bosque de Kelp (Marina)",
    "permanence_guarantee_years": 15,
}
RAG_QUERY = "¿Cuáles son los requisitos de permanencia y adicionalidad para créditos de naturaleza marina según la Hoja de Ruta 2025 y el Reglamento de Restauración?"


# --- APP PRINCIPAL (03_Auditoria_ECOACSA.py) ---
def main():
    st.set_page_config(
        page_title="GICES ORQUESTA - 03. AUDITORÍA ECOACSA",
        page_icon="🛡️",
        layout="wide"
    )

    st.title("🛡️ GICES ORQUESTA - 03. TEST DE COINCIDENCIA ECOACSA")
    st.caption("Paso 3 del Pipeline: Auditoría E4 (Biodiversidad) y Validación de Integridad (Máquina vs. Humano).")

    if not gices_brain or not sh:
        return

    # --- 1. INPUTS DE DATOS Y VEREDICTO HUMANO ---
    st.subheader("1. Dato de Campo y Veredicto Humano (Entrada)")
    
    col_human, col_data_input = st.columns([1, 2])
    
    with col_human:
        human_verdict = st.selectbox(
            "Veredicto Humano Esperado:",
            options=['RIESGO', 'CUMPLE', 'NO CUMPLE', 'RIESGO MEDIO'],
            index=0, 
            key="human_verdict_input"
        )
        human_gap = st.text_area(
            "Brecha Principal Identificada por Humano:",
            value="La garantía de permanencia de 15 años incumple el criterio de Alta Integridad de la Hoja de Ruta UE.",
            key="human_gap_input"
        )

    with col_data_input:
        real_data_input = st.text_area(
            "Pegar Dato Crudo E4 Real (JSON):",
            value=json.dumps(SIMULATED_DATA, indent=2),
            height=250,
            key="real_data_input"
        )
    
    st.divider()

    # --- 2. LÓGICA DE EJECUCIÓN (CON TRANSPARENCIA) ---
    if st.button("🛡️ Ejecutar Test de Coincidencia", type="primary", use_container_width=True):
        
        with st.status("🔍 **Fase 2: Ejecutando RAG y Deliberación Cognitiva...**", expanded=True) as status:
            try:
                # A. Determinar datos a auditar
                try:
                    test_data = json.loads(real_data_input)
                except json.JSONDecodeError:
                    status.write("Advertencia: JSON inválido. Usando simulación de respaldo.")
                    test_data = SIMULATED_DATA

                # B. RAG Semántico (Recuperación de Contexto)
                status.write("Paso B: **Búsqueda Vectorial (RAG)** de la normativa relevante.")
                with st.expander("🔎 **Query RAG Enviado al Cerebro Vectorial**", expanded=False):
                    st.code(RAG_QUERY, language="text")
                    
                context_chunks = gices_brain.retrieve_context(RAG_QUERY, k=4)
                
                # Protocolo de Transparencia: Evidencia recuperada
                with st.expander("📄 **Evidencia Normativa Recuperada**", expanded=False):
                    if context_chunks:
                        for c in context_chunks:
                            st.markdown(f"**Fuente:** {c['source']} (Pág. {c['page']}) | Score: {c.get('score', 0):.2f}")
                            st.caption(f"...{c['content'][:400]}...")
                            st.divider()
                    else:
                        st.error("❌ No se encontró evidencia relevante. La base vectorial puede estar vacía.")

                # C. Análisis Deliberativo (GPT-4o)
                status.write("Paso C: **Deliberación** - Cruzando el Dato vs. Normativa.")
                
                # Para transparencia, necesitamos el prompt. Simularemos el retorno del prompt
                if hasattr(gices_brain.deliberative_analysis, '__code__') and 'return_prompt' in gices_brain.deliberative_analysis.__code__.co_varnames:
                    temp_result = gices_brain.deliberative_analysis(test_data, context_chunks, mode="ECOACSA Biodiversity Integrity", return_prompt=True)
                    prompt_to_gpt = temp_result["prompt"]
                    machine_result = gices_brain.deliberative_analysis(test_data, context_chunks, mode="ECOACSA Biodiversity Integrity")
                else:
                    prompt_to_gpt = "Prompt no disponible por configuración de gices_brain.py."
                    machine_result = gices_brain.deliberative_analysis(test_data, context_chunks, mode="ECOACSA Biodiversity Integrity")

                # Protocolo de Transparencia: Prompt enviado
                with st.expander("🤖 **Prompt Enviado al Auditor GPT-4o**", expanded=False):
                    st.code(prompt_to_gpt, language="markdown")
                
                machine_check = machine_result.get("compliance_check", "UNKNOWN").upper().replace("RIESGO ALTO", "RIESGO").replace("RIESGO MEDIO", "RIESGO")
                status.update(label="✅ **Análisis de Deliberación Completo**", state="complete")

            except Exception as e:
                status.update(label="❌ **Error Crítico en el Proceso**", state="error")
                st.error(f"Error: {e}")
                return

        # --- 3. RESULTADOS Y COMPARACIÓN ---
        st.subheader("2. Resultados del Análisis")
        col_ai, col_human_output = st.columns(2)
        
        # Columna de la IA
        with col_ai:
            st.markdown("#### Veredicto de la Máquina (GICES-RAGA)")
            if "RIESGO" in machine_check: st.error(f"⚠️ VEREDICTO: {machine_check}")
            elif "CUMPLE" in machine_check: st.success(f"✅ VEREDICTO: {machine_check}")
            else: st.info(f"❓ VEREDICTO: {machine_check}")

            st.write(f"**Justificación:** {machine_result.get('narrative', 'N/A')}")
            st.code(json.dumps(machine_result, indent=2), language="json")

        # Columna del Humano
        with col_human_output:
            st.markdown("#### Veredicto Humano Declarado")
            human_check = human_verdict.upper().replace("RIESGO ALTO", "RIESGO").replace("RIESGO MEDIO", "RIESGO")
            if "RIESGO" in human_check: st.warning(f"⚠️ VEREDICTO: {human_verdict}")
            elif "CUMPLE" in human_check: st.success(f"✅ VEREDICTO: {human_verdict}")
            else: st.info(f"❓ VEREDICTO: {human_verdict}")
            st.write(f"**Brecha:** {human_gap}")
            st.markdown("---")
            
        st.subheader("3. Conclusión: Análisis de Coincidencia")
        
        # Comparación
        if machine_check == human_check.strip():
            st.balloons()
            st.success(f"🎯 COINCIDENCIA PERFECTA (Kappa Score: 1.0) | Ambos veredictos coinciden en: **{machine_check}**.")
            st.markdown("**VALIDACIÓN TOTAL:** El motor de IA replica la lógica de auditoría experta. **Máxima Integridad y Trazabilidad.**")
        else:
            st.error(f"❌ NO COINCIDENCIA | Máquina: **{machine_check}** vs. Humano: **{human_verdict}**.")
            st.warning("⚠️ **ALERTA:** Esto activa un protocolo de Calibración Humano-en-el-Bucle (HITL) para investigar la divergencia.")

if __name__ == "__main__":
    main()
