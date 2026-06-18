import streamlit as st
import pandas as pd

# ==================================
# CONFIGURACIÓN
# ==================================

st.set_page_config(
    page_title="Sistema Inteligente de Inventarios Farmacéuticos",
    page_icon="🏥",
    layout="wide"
)

# ==================================
# LEER EXCEL
# ==================================

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(
    archivo_excel,
    sheet_name="Maestro_SKU"
)

ventas = pd.read_excel(
    archivo_excel,
    sheet_name="Ventas_Historicas"
)

inventario = pd.read_excel(
    archivo_excel,
    sheet_name="Inventario_Lotes"
)

leadtimes = pd.read_excel(
    archivo_excel,
    sheet_name="LeadTimes"
)

# ==================================
# MENU
# ==================================

st.sidebar.title("🏥 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    [
        "Dashboard",
        "Ventas",
        "Inventario",
        "Lead Times"
    ]
)

# ==================================
# DASHBOARD
# ==================================

if pagina == "Dashboard":

    st.title("🏥 Sistema Inteligente de Inventarios Farmacéuticos")

    total_skus = maestro["SKU"].nunique()

    total_lotes = inventario["Lote"].nunique()

    stock_total = inventario["Stock"].sum()

    leadtime_promedio = round(
        leadtimes["LeadTime_Dias"].mean(),
        1
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "SKUs",
        total_skus
    )

    col2.metric(
        "Lotes",
        total_lotes
    )

    col3.metric(
        "Stock Total",
        f"{stock_total:,.0f}"
    )

    col4.metric(
        "Lead Time Prom.",
        leadtime_promedio
    )

    st.divider()

    st.subheader("Inventario por lote")

    st.dataframe(
        inventario.head(20),
        use_container_width=True
    )

# ==================================
# VENTAS
# ==================================

elif pagina == "Ventas":

    st.title("📈 Ventas Históricas")

    st.dataframe(
        ventas.head(100),
        use_container_width=True
    )

# ==================================
# INVENTARIO
# ==================================

elif pagina == "Inventario":

    st.title("📦 Inventario")

    st.dataframe(
        inventario,
        use_container_width=True
    )

# ==================================
# LEAD TIMES
# ==================================

elif pagina == "Lead Times":

    st.title("🚚 Lead Times")

    st.dataframe(
        leadtimes,
        use_container_width=True
    )
