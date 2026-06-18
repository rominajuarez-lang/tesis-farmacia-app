import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sistema Inteligente de Inventarios Farmacéuticos",
    page_icon="🏥",
    layout="wide"
)

st.sidebar.title("📋 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    ["Dashboard", "Forecast", "Vencimientos", "Recomendaciones"]
)

if pagina == "Dashboard":

    st.title("🏥 Sistema Inteligente de Inventarios Farmacéuticos")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("SKUs", "250")
    col2.metric("Inventario", "S/ 12.5 MM")
    col3.metric("Riesgo", "S/ 1.8 MM")
    col4.metric("Accuracy", "89%")

    st.divider()

    st.subheader("⚠️ Productos Críticos")

    datos = pd.DataFrame({
        "SKU": ["MET001", "AMO001", "ENO001", "CEF001"],
        "Producto": ["Metformina", "Amoxicilina", "Enoxaparina", "Ceftriaxona"],
        "Stock": [5000, 12000, 3000, 7000],
        "Riesgo": ["🔴 Alto", "🟡 Medio", "🟢 Bajo", "🔴 Alto"]
    })

    st.dataframe(datos, use_container_width=True)

    st.subheader("Distribución de riesgo")

    grafico = pd.DataFrame({
        "Riesgo": ["Alto", "Medio", "Bajo"],
        "Cantidad de SKUs": [40, 25, 15]
    })

    st.bar_chart(grafico, x="Riesgo", y="Cantidad de SKUs")

elif pagina == "Forecast":

    st.title("📈 Forecast Inteligente")

    sku = st.selectbox("Seleccionar SKU", ["MET001", "AMO001", "ENO001"])

    resultados = pd.DataFrame({
        "Modelo": ["Moving Average", "Holt", "Holt-Winters", "ARIMA", "Prophet"],
        "MAPE (%)": [18, 15, 11, 13, 9]
    })

    st.write(f"SKU seleccionado: **{sku}**")
    st.dataframe(resultados, use_container_width=True)
    st.success("🏆 Modelo recomendado: Prophet")

elif pagina == "Vencimientos":

    st.title("⚠️ Riesgo de Vencimiento")

    vencimientos = pd.DataFrame({
        "SKU": ["MET001", "MET001", "AMO001", "CEF001"],
        "Lote": ["L001", "L002", "L003", "L004"],
        "Stock": [5000, 8000, 3000, 7000],
        "Vence en": ["3 meses", "12 meses", "2 meses", "5 meses"],
        "Riesgo": ["🔴 Alto", "🟢 Bajo", "🟡 Medio", "🔴 Alto"]
    })

    st.dataframe(vencimientos, use_container_width=True)

elif pagina == "Recomendaciones":

    st.title("🛒 Recomendaciones de Compra")

    recomendaciones = pd.DataFrame({
        "SKU": ["MET001", "AMO001", "ENO001"],
        "Forecast mensual": [4000, 1000, 2500],
        "Stock actual": [2000, 20000, 3000],
        "Lead time días": [120, 60, 180],
        "Acción sugerida": ["🔴 Comprar 15000", "🟢 No comprar", "🟡 Revisar compra"]
    })

    st.dataframe(recomendaciones, use_container_width=True)
