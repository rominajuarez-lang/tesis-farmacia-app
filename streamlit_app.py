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

    stock_total = inventario["Stock_Lote"].sum()

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

elif pagina == "Vencimientos":

    st.title("⚠️ Riesgo de Vencimiento por Lote")

    venc = inventario.copy()

    venc["Fecha_Vencimiento"] = pd.to_datetime(venc["Fecha_Vencimiento"])

    hoy = pd.Timestamp.today()

    venc["Meses_Restantes"] = (
        (venc["Fecha_Vencimiento"] - hoy).dt.days / 30
    ).round(1)

    def clasificar_riesgo(meses):
        if meses <= 3:
            return "🔴 Alto"
        elif meses <= 6:
            return "🟡 Medio"
        else:
            return "🟢 Bajo"

    venc["Riesgo"] = venc["Meses_Restantes"].apply(clasificar_riesgo)

    st.dataframe(
        venc[
            [
                "SKU",
                "Lote",
                "Stock_Lote",
                "Fecha_Vencimiento",
                "Meses_Restantes",
                "Almacen",
                "Estado",
                "Riesgo"
            ]
        ],
        use_container_width=True
    )

    resumen = venc.groupby("Riesgo")["Stock_Lote"].sum().reset_index()

    st.subheader("Stock por nivel de riesgo")

    st.bar_chart(
        resumen,
        x="Riesgo",
        y="Stock_Lote"
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
