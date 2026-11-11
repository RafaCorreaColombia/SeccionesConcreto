# 🏗️ Criterio Estructural — Diagrama de Interacción P-M y Diseño a Cortante

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Normativa NSR-10 / ACI 318](https://img.shields.io/badge/Norma-NSR--10%20%2F%20ACI%20318-E67E22.svg)](#)

Aplicación web interactiva desarrollada en Python y Streamlit para el análisis y verificación de secciones rectangulares de concreto reforzado sometidas a flexocompresión axial y esfuerzo cortante.

---

## 🚀 Características Principales

- **Parser Inteligente de Armadura:** Interpretación automática de nomenclaturas combinadas de acero de refuerzo longitudinal y mallas electrosoldadas:
  - Barras estándar: `3N6`, `2N8`, `2N6 + 2N5`.
  - Mallas electrosoldadas: `M188` (conversión automática según el ancho $b$ de la sección).
  - Entrada numérica directa en $\text{mm}^2$.
- **Edición Dinámica de Capas:** Adición, modificación y eliminación de capas de refuerzo a cualquier profundidad $d_i$ en tiempo real mediante `st.data_editor`.
- **Diagrama de Interacción P-M Continuo:**
  - Barrido iterativo sobre la profundidad del eje neutro ($c$) desde compresión pura hasta tracción pura.
  - Generación gráfica interactiva con Plotly de las curvas Nominal $(P_n, M_n)$ y de Diseño $(\phi P_n, \phi M_n)$.
  - Transición automática del factor de reducción de resistencia $\phi$ (de 0.65 a 0.90) basado en la deformación neta a tracción $\epsilon_t$.
- **Diseño y Verificación a Cortante:**
  - Evaluación del aporte del concreto $\phi V_c$ y del acero de estribos $\phi V_s$.
  - Control normativo de cuantía máxima de cortante ($V_{s,\max} = 0.66 \sqrt{f'_c} b d$) y alertas de capacidad.

---

## 🛠️ Estructura del Repositorio

```text
.
├── .streamlit/
│   └── config.toml        # Personalización de colores y tema visual
├── app.py                 # Código principal de la aplicación Streamlit
├── requirements.txt       # Librerías de Python requeridas
├── .gitignore             # Filtro de archivos temporales de Git
└── README.md              # Documentación del proyecto
