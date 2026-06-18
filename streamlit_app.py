import streamlit as st

st.set_page_config(
    page_title="Sistema Inteligente de Inventarios Farmacéuticos",
    page_icon="🏥",
    layout="wide"
)

# Menú lateral
st.sidebar.title("📋 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    [
        "Dashboard",
        "Forecast",
        "Vencimientos",
        "Recomendaciones"
    ]
)

# DASHBOARD
if pagina == "Dashboard":

    st.title("🏥 Sistema Inteligente de Inventarios Farmacéuticos")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("SKUs", "250")
    col2.metric("Inventario", "S/ 12.5 MM")
    col3.metric("Riesgo", "S/ 1.8 MM")
    col4.metric("Accuracy", "89%")

    st.divider()

    st.subheader("Productos Críticos")

    datos = {
        "SKU": ["MET001", "AMO001", "ENO001", "CEF001"],
        "Producto": [
            "Metformina",
            "Amoxicilina",
            "Enoxaparina",
            "Ceftriaxona"
        ],
        "Riesgo": [
            "🔴 Alto",
            "🟡 Medio",
            "🟢 Bajo",
            "🔴 Alto"
        ]
    }

    st.table(datos)

    st.subheader("Distribución de Riesgo")

    chart_data = {
        "Categoría": ["Alto", "Medio", "Bajo"],
        "Cantidad": [40, 25, 15]
    }

    st.bar_chart(
        data=chart_data,
        x="Categoría",
        y="Cantidad"
    )

# FORECAST
elif pagina == "Forecast":

    st.title("📈 Forecast Inteligente")

    st.selectbox(
        "Seleccionar SKU",
        ["MET001", "AMO001", "ENO001"]
    )

    st.success("Modelo recomendado: Prophet")

# VENCIMIENTOS
elif pagina == "Vencimientos":

    st.title("⚠️ Riesgo de Vencimiento")

    st.write("Próximamente")

# RECOMENDACIONES
elif pagina == "Recomendaciones":

    st.title("🛒 Recomendaciones")

    st.write("Próximamente")
