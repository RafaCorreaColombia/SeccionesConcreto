import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(page_title="Criterio Estructural - Análisis P-M y Cortante", layout="wide")

def parse_area_acero(texto, b_mm):
    """
    Parsea texto como '2N6', '2n6+2n5', 'm188', o áreas directas en mm2.
    """
    texto = str(texto).upper().replace(" ", "")
    total_as = 0.0
    
    # Áreas de barras estándar (mm²)
    areas_barras = {'2': 31.6, '3': 71.2, '4': 129.0, '5': 199.0, '6': 285.0, '7': 387.1, '8': 510.0}
    
    # Buscar patrones como 2N6, 3#5, etc.
    matches = re.findall(r'(\d+)[N#](\d+)', texto)
    for cant, calibre in matches:
        if calibre in areas_barras:
            total_as += int(cant) * areas_barras[calibre]
            
    # Buscar patrones de malla, ej. M188 (188 mm2 por metro lineal)
    malla = re.search(r'M(\d+)', texto)
    if malla:
        area_por_metro = float(malla.group(1))
        total_as += area_por_metro * (b_mm / 1000.0)
        
    # Si no coincide con nomenclatura, intentar leerlo como número directo (mm²)
    if total_as == 0:
        try:
            total_as = float(texto)
        except ValueError:
            pass
            
    return total_as

# --- INTERFAZ DE USUARIO ---
st.title("🏗️ Diseño de Columnas: Diagrama P-M y Cortante")
st.markdown("Herramienta de validación estructural para secciones de concreto reforzado.")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Geometría y Materiales")
    b = st.number_input("Base, b (mm)", value=300.0, step=10.0)
    h = st.number_input("Altura, h (mm)", value=350.0, step=10.0)
    fc = st.number_input("f'c (MPa)", value=28.0, step=1.0)
    fy = st.number_input("fy (MPa)", value=420.0, step=10.0)
    Es = 200000.0

with col2:
    st.subheader("Cortante y Estribos")
    calibre_estribo = st.selectbox("Calibre Estribo", options=['3', '4', '5'], index=0)
    ramas = st.number_input("Número de ramas", value=2, step=1)
    s = st.number_input("Separación, s (mm)", value=150.0, step=10.0)
    
    area_estribo = ramas * {'3': 71.2, '4': 129.0, '5': 199.0}[calibre_estribo]

with col3:
    st.subheader("Distribución de Armadura")
    st.markdown("Agrega o elimina filas. Ingresa el acero como `3N6`, `2n6+2n5`, `M188` o el área en mm².")
    
    # Tabla interactiva para capas de acero
    df_inicial = pd.DataFrame({
        "d (mm)": [60.0, 175.0, 290.0],
        "Acero": ["3N6", "2N6", "3N6"]
    })
    
    df_aceros = st.data_editor(df_inicial, num_rows="dynamic", use_container_width=True)

# --- CÁLCULOS ESTRUCTURALES ---
beta1 = max(0.65, min(0.85, 0.85 - 0.05 * (fc - 28) / 7))
ey = fy / Es
ecu = 0.003

# Extraer y parsear capas
capas = []
As_total = 0.0
for _, row in df_aceros.iterrows():
    d_i = float(row["d (mm)"])
    As_i = parse_area_acero(row["Acero"], b)
    capas.append({"d": d_i, "As": As_i})
    As_total += As_i

d_max = max([capa["d"] for capa in capas]) if capas else h
cuantia = As_total / (b * h) if (b * h) > 0 else 0

# Generar puntos del diagrama P-M iterando el eje neutro (c)
c_vals = np.concatenate([
    np.array([10000.0]),                   # Compresión pura
    np.linspace(800, 1, 200),              # Barrido profundo
    np.linspace(0.99, 0.01, 50)            # Cercano a tracción pura
])

PM_data = []

for c in c_vals:
    a = min(beta1 * c, h)
    
    # Concreto (Convención: Compresión Positiva para diagramas de columnas)
    Cc = 0.85 * fc * a * b / 1000.0 if a > 0 else 0.0
    Mn_c = Cc * (h / 2.0 - a / 2.0) / 1000.0
    
    Pn_s = 0.0
    Mn_s = 0.0
    et_max = -1.0 # Para buscar la fibra más traccionada
    
    for capa in capas:
        d_i = capa["d"]
        As_i = capa["As"]
        
        # Deformación (Compresión es positiva en esta fórmula adaptada)
        es_i = ecu * (c - d_i) / c
        fs_i = max(-fy, min(fy, es_i * Es))
        
        # Ajuste de fuerza en el acero si está dentro del bloque de compresión
        # (se resta el área desplazada de concreto)
        if d_i < a and fs_i > 0:
            F_si = As_i * (fs_i - 0.85 * fc) / 1000.0
        else:
            F_si = As_i * fs_i / 1000.0
            
        Pn_s += F_si
        Mn_s += F_si * (h / 2.0 - d_i) / 1000.0
        
        # Guardar deformación más traccionada (convención positiva para tracción)
        def_traccion = ecu * (d_i - c) / c
        if def_traccion > et_max:
            et_max = def_traccion

    Pn = Cc + Pn_s
    Mn = abs(Mn_c + Mn_s)
    
    # Factor phi
    if et_max >= 0.005:
        phi = 0.90
    elif et_max <= ey:
        phi = 0.65
    else:
        phi = 0.65 + 0.25 * (et_max - ey) / (0.005 - ey)
        
    PM_data.append({
        "c": c, "Pn": Pn, "Mn": Mn, 
        "phiPn": Pn * phi, "phiMn": Mn * phi, 
        "et": et_max, "phi": phi
    })

df_pm = pd.DataFrame(PM_data)

# --- DISEÑO A CORTANTE ---
phi_v = 0.75
Vc = 0.17 * np.sqrt(fc) * b * d_max / 1000.0
Vs = (area_estribo * fy * d_max / s) / 1000.0 if s > 0 else 0
Vs_max = 0.66 * np.sqrt(fc) * b * d_max / 1000.0
phi_Vn = phi_v * (Vc + min(Vs, Vs_max))
alerta_cortante = "⚠️ El acero a cortante supera el máximo permitido (Vs > Vs_max)." if Vs > Vs_max else "✅ Cumple límite de Vs_max."

# --- RENDERIZADO DE RESULTADOS ---
st.divider()

col_res1, col_res2 = st.columns([2, 1])

with col_res1:
    st.subheader("Diagrama de Interacción P-M")
    
    fig = go.Figure()
    # Curva Nominal
    fig.add_trace(go.Scatter(x=df_pm['Mn'], y=df_pm['Pn'], mode='lines', name='Nominal (Pn, Mn)', line=dict(color='gray', dash='dash')))
    # Curva de Diseño
    fig.add_trace(go.Scatter(x=df_pm['phiMn'], y=df_pm['phiPn'], mode='lines', name='Diseño (φPn, φMn)', line=dict(color='blue', width=2)))
    
    fig.update_layout(
        xaxis_title="Momento Flector (kN·m)",
        yaxis_title="Carga Axial (kN)",
        hovermode="x unified",
        template="plotly_white",
        height=500
    )
    # Marcar el (0,0)
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.add_vline(x=0, line_color="black", line_width=1)
    st.plotly_chart(fig, use_container_width=True)

with col_res2:
    st.subheader("Reporte de Sección")
    st.metric("Cuantía Longitudinal (ρ)", f"{cuantia*100:.2f} %")
    st.metric("Área de Acero Total", f"{As_total:.1f} mm²")
    
    st.markdown("---")
    st.subheader("Capacidad a Cortante")
    st.markdown(f"**φVc (Concreto):** {phi_v * Vc:.1f} kN")
    st.markdown(f"**φVs (Acero):** {phi_v * Vs:.1f} kN")
    st.markdown(f"**φVn (Capacidad Total):** **{phi_Vn:.1f} kN**")
    st.caption(f"Vs máximo permitido: {Vs_max:.1f} kN")
    st.markdown(alerta_cortante)
    
    st.markdown("---")
    st.subheader("Puntos Críticos P-M")
    # Extraer puntos notables
    idx_bal = (df_pm['et'] - ey).abs().idxmin()
    idx_flex = df_pm['Pn'].abs().idxmin()
    
    st.markdown(f"**Carga Axial Pura (φPn_max):** {df_pm.iloc[0]['phiPn']:.1f} kN")
    st.markdown(f"**Punto Balanceado (φMn, φPn):** {df_pm.iloc[idx_bal]['phiMn']:.1f} kN·m, {df_pm.iloc[idx_bal]['phiPn']:.1f} kN")
    st.markdown(f"**Flexión Pura (φMn):** {df_pm.iloc[idx_flex]['phiMn']:.1f} kN·m")
