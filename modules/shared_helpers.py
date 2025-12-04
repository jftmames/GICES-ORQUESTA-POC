import streamlit as st
import json
import plotly.graph_objects as go
import graphviz
import hashlib
import time
from pathlib import Path
from datetime import datetime
import zipfile
import subprocess
import sys

# --- CONFIGURACIÓN DE RUTAS (Ajustadas para ser importadas desde modules/) ---
# sube un nivel (..), luego resuelve la ruta base del proyecto
ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
KB_PATH = ROOT_DIR / "rag" / "knowledge_base"


# --- 1. DATOS DE RESPALDO Y SIMULACIÓN (MOCK_DATA) ---
MOCK_DATA = {
    "narrative": "El análisis del crédito 'Amazonia Restoration #001' (150ha) revela una alineación parcial con la taxonomía de la UE. Carece de métricas de permanencia a largo plazo exigidas por la Hoja de Ruta de Créditos de Naturaleza (2025).",
    "compliance": "RIESGO MEDIO",
    "eee_metrics": {'Profundidad': 0.9, 'Pluralidad': 0.85, 'Trazabilidad': 1.0, 'Evidencia': 0.9, 'Ética': 0.8},
    "reasoning_trace": [
        "1. INGESTA: Dato E4-5 (150ha, Active Restoration)",
        "2. NORMATIVA: Reglamento UE Restauración (Art. 4)",
        "3. CRITERIO: Nature Credits Roadmap (Definición de Integridad)",
        "4. CRUCE: ¿Garantiza permanencia > 30 años?",
        "5. HALLAZGO: Falta evidencia de seguro de permanencia",
        "6. VEREDICTO: Cumplimiento Parcial (Riesgo Financiero)"
    ],
    "evidence_used": [
        {"source": "Reglamento UE Restauración.pdf", "content": "Artículo 4: Los Estados miembros establecerán medidas de restauración que cubran al menos el 20%..."},
        {"source": "2025_7_7_EC_NATURE CREDITS_ENG.pdf", "content": "Nature credits must demonstrate high integrity... ensuring additionality, permanence, and avoiding double counting."}
    ]
}

# --- 2. MOTOR DE AUDITORÍA FORENSE (Reutilizado para App 04) ---
def calculate_file_hash(filepath):
    """Calcula SHA-256 de un archivo físico."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except:
        return None

def generate_secure_package():
    """
    Genera el paquete de auditoría con integridad criptográfica.
    Retorna la ruta del ZIP y el Manifiesto de Datos.
    """
    audit_dir = OUTPUT_PATH / "release" / "audit"
    evidence_dir = OUTPUT_PATH / "evidence"
    raga_dir = OUTPUT_PATH / "raga"
    
    for d in [audit_dir, evidence_dir, raga_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Artefactos que se sellarán
    artifacts = {
        "kpis.json": raga_dir / "kpis.json",
        "explain.json": raga_dir / "explain.json",
        "source_data.json": DATA_PATH / "biodiversity_2024.json"
    }

    # Asegurar existencia de archivos para sellar (crea MOCKs si no existen)
    for name, path in artifacts.items():
        if not path.exists():
            if name == "explain.json":
                path.write_text(json.dumps(MOCK_DATA, indent=2))
            else:
                path.write_text(json.dumps({"status": "generated_for_audit"}, indent=2))
    
    manifest_entries = []
    hash_list = []
    
    for name, path in artifacts.items():
        if path.exists():
            f_hash = calculate_file_hash(path)
            if f_hash:
                hash_list.append(f_hash)
                manifest_entries.append({
                    "file": name,
                    "sha256": f_hash,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
    
    # Agregar hash de la normativa clave (ESRS E4)
    pdf_evidence = KB_PATH / "2025_7_7_EC_NATURE CREDITS_SPA.pdf"
    if pdf_evidence.exists():
         pdf_hash = calculate_file_hash(pdf_evidence)
         if pdf_hash:
             manifest_entries.append({"file": pdf_evidence.name, "sha256": pdf_hash, "type": "NORMATIVA_BASE"})

    # Calcular Merkle Root (Hash de los hashes)
    combined_hash = "".join(sorted(hash_list))
    merkle_root = hashlib.sha256(combined_hash.encode('utf-8')).hexdigest()
    
    manifest_data = {
        "run_id": f"GICES-{int(time.time())}",
        "status": "SEALED",
        "merkle_root": f"SHA256:{merkle_root}",
        "artifacts": manifest_entries,
        "signature_algorithm": "RSA-SHA256 (Simulated)"
    }
    
    manifest_path = evidence_dir / "evidence_manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2))
    
    zip_name = f"GICES_AUDIT_{manifest_data['run_id']}.zip"
    zip_path = audit_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for name, path in artifacts.items():
            if path.exists():
                zipf.write(path, arcname=name)
        zipf.write(manifest_path, arcname="evidence_manifest.json")
        
    return zip_path, manifest_data 

# --- 3. FUNCIONES DE VISUALIZACIÓN (Para App 02) ---
def plot_eee_radar(metrics):
    """Genera el gráfico de radar para las métricas EEE."""
    categories = list(metrics.keys())
    values = list(metrics.values())
    values += [values[0]]
    categories += [categories[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself', name='EEE Score',
        line=dict(color='#00CC96', width=2), fillcolor='rgba(0, 204, 150, 0.2)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False, height=300, margin=dict(t=30, b=30, l=40, r=40)
    )
    return fig

def render_inquiry_tree(steps):
    """Genera el árbol de indagación con Graphviz."""
    dot = graphviz.Digraph()
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
    dot.node('ROOT', "❓ PREGUNTA RAÍZ:\n¿Es válido el Crédito de Naturaleza?", 
             fillcolor='#FFDDC1', color='#E67E22', penwidth='2')
    last = 'ROOT'
    for i, step in enumerate(steps):
        node_id = f"S{i}"
        color = '#D1F2EB' if "NORMATIVA" in step or "EVIDENCIA" in step else '#E8F6F3'
        if "VEREDICTO" in step: color = '#FCF3CF'
        dot.node(node_id, step, fillcolor=color, color='#AED6F1')
        dot.edge(last, node_id)
        last = node_id
    return dot

# --- 4. EJECUCIÓN DE SCRIPTS (Para App 02) ---
def run_script(script_name, desc):
    """Ejecuta scripts externos con Protocolo de Transparencia (stdout visible)."""
    path = ROOT_DIR / "scripts" / script_name
    # Usamos st.status para la transparencia en App 02
    with st.status(f"⚙️ {desc}...", expanded=True) as s:
        time.sleep(0.5)
        if path.exists():
            try:
                res = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=60)
                st.code(res.stdout)
                s.update(label="✅ Completado", state="complete", expanded=False)
                return True
            except Exception as e:
                s.update(label="❌ Error", state="error")
                st.error(str(e))
        else:
            st.warning(f"Simulando {script_name} (Archivo no encontrado)")
            s.update(label="⚠️ Simulado", state="complete", expanded=False)
            return True
    return False

# --- 5. CARGA DE DATOS (Para Apps 01 y 03) ---
def load_sample_data(filename):
    """Carga datos de muestra de la carpeta data/samples."""
    path = DATA_PATH / filename
    if path.exists():
        try:
            # Usamos encoding explícito por seguridad
            return json.loads(path.read_text(encoding="utf-8")) 
        except:
            return {"error": "JSON no válido"}
    return {"status": f"No se encontró el archivo de datos: {filename}"}
