import streamlit as st

def main():
    st.set_page_config(
        page_title="GICES ORQUESTA - SALA DE MANDO",
        page_icon="⚜️",
        layout="wide"
    )

    st.title("⚜️ GICES-ORQUESTA: SALA DE MANDO Y TRAZABILIDAD COGNITIVA")
    st.markdown("---")
    st.header("Pipeline de Auditoría CSRD (ESRS E4) para ECOACSA")
    st.markdown(
        """
        Esta Orquesta demuestra el control total sobre el proceso de auditoría cognitiva, separando cada fase crítica en un componente.
        El objetivo es lograr la **máxima transparencia** y el **test de coincidencia** entre el juicio de la Máquina y el Auditor Humano.
        
        **INICIAR AUDITORÍA:** Utilice el menú de navegación lateral para seguir el flujo en orden, empezando por el **(01)**.
        """
    )
    
    st.subheader("Flujo de Trazabilidad:")
    
    st.info("**01. INGESTA (La Munición):** Carga los reglamentos y genera el Cerebro Vectorial (la Memoria de la IA).")
    st.warning("**03. AUDITORÍA ECOACSA (Prueba de Fuego):** Cruza el Dato de Campo E4 con la Ley y genera el veredicto de RIESGO (clave para ECOACSA).")
    st.success("**04. EVIDENCIA FORENSE (El Sello):** Genera la firma criptográfica (Merkle Root) para certificar la inalterabilidad de la evidencia.")

if __name__ == "__main__":
    main()
