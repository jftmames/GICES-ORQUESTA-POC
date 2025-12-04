import streamlit as st
import json
from pathlib import Path
import time

# Importamos utilidades compartidas
try:
    import modules.shared_helpers as sh
except ImportError:
    st.error("❌ Error CRÍTICO: No se encuentra 'modules.shared_helpers'.")
    sh = None

# --- APP PRINCIPAL (04_Evidencia_Forense.py) ---
def main():
    st.set_page_config(
        page_title="GICES ORQUESTA - 04. EVIDENCIA FORENSE",
        page_icon="🔒",
        layout="wide"
    )

    st.title("🔒 GICES ORQUESTA - 04. SELLO FORENSE Y TRAZABILIDAD")
    st.caption("Paso 4 del Pipeline: Generación del Paquete de Auditoría Inmutable (Garantía de No Repudio).")
    
    if not sh:
        return

    # Estado del ZIP para que persista
    if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
    if 'manifest_data' not in st.session_state: st.session_state.manifest_data = None

    st.markdown("""
    Esta sección sella criptográficamente el análisis de la auditoría. Garantizamos la **Cadena de Custodia** de los datos y la inalterabilidad del veredicto.
    """)

    if st.button("🔒 Generar Paquete Sellado (ZIP)", type="primary", use_container_width=True):
        try:
            # Protocolo de Transparencia: Usamos st.status para desglosar el proceso
            with st.status("⚙️ **Fase 3: Proceso de Sellado Criptográfico (SteelTrace)**", expanded=True) as status:
                
                # 1. Recopilación y Hashing
                status.write("1. Recopilando Artefactos (JSONs) y calculando hashes SHA-256...")
                time.sleep(0.5)
                
                # La función generate_secure_package realiza todos los cálculos internos
                zip_path, manifest = sh.generate_secure_package()
                
                # 2. Merkle Root
                status.write("2. Calculando Merkle Root de la Cadena de Custodia (Firma de Integridad)...")
                time.sleep(0.5)
                
                # 3. Empaquetado y Finalización
                status.write("3. Empaquetando ZIP de Evidencia y Firmando Manifiesto...")
                time.sleep(0.5)
                
                st.session_state.zip_ready = str(zip_path)
                st.session_state.manifest_data = manifest
                
                status.update(label=f"✅ **Paquete Generado Exitosamente:** {zip_path.name}", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Error crítico generando auditoría: {e}")

    # --- SECCIÓN DE DESCARGA Y VERIFICACIÓN ---
    st.divider()
    col_dl, col_verify = st.columns(2)
    
    with col_dl:
        st.subheader("Descarga de Evidencia")
        if st.session_state.zip_ready and Path(st.session_state.zip_ready).exists():
            zip_path = Path(st.session_state.zip_ready)
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Paquete Forense (.zip)",
                    data=f,
                    file_name=zip_path.name,
                    mime="application/zip",
                    key="dl_btn_audit"
                )
        else:
            st.info("Genera el paquete para habilitar la descarga.")

    with col_verify:
        st.subheader("Manifiesto de Trazabilidad")
        if st.session_state.manifest_data:
            manifest_data = st.session_state.manifest_data
            st.code(json.dumps(manifest_data, indent=2), language="json")
            if "merkle_root" in manifest_data:
                st.caption(f"Merkle Root: {manifest_data['merkle_root']}")
            st.info("Este manifiesto prueba la integridad y origen de los datos usados en el análisis.")
        else:
            st.warning("⚠️ Manifiesto no disponible. Ejecuta la generación.")

if __name__ == "__main__":
    main()
