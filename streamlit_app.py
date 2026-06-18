import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Sistema Inteligente de Inventarios Farmacéuticos",
    page_icon="🏥",
    layout="wide"
)

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(archivo_excel, sheet_name="Maestro_SKU")
ventas = pd.read_excel(archivo_excel, sheet_name="Ventas_Historicas")
inventario = pd.read_excel(archivo_excel, sheet_name="Inventario_Lotes")
leadtimes = pd.read_excel(archivo_excel, sheet_name="LeadTimes")

st.sidebar.title("🏥 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    ["Dashboard", "Ventas", "Inventario", "Lead Times", "Vencimientos"]
)

if pagina == "Dashboard":

    st.title("🏥 Sistema Inteligente de Inventarios Farmacéuticos")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("SKUs", maestro["SKU"].nunique())
    col2.metric("Lotes", inventario["Lote"].nunique())
    col3.metric("Stock Total", f"{inventario['Stock_Lote'].sum():,.0f}")
    col4.metric("Lead Time Prom.", round(leadtimes["LeadTime_Dias"].mean(), 1))

    st.divider()
    st.subheader("Inventario por lote")
    st.dataframe(inventario.head(20), use_container_width=True)

elif pagina == "Ventas":

    st.title("📈 Ventas Históricas")
    st.dataframe(ventas.head(100), use_container_width=True)

elif pagina == "Inventario":

    st.title("📦 Inventario por Lote")
    st.dataframe(inventario, use_container_width=True)

elif pagina == "Lead Times":

    st.title("🚚 Lead Times")
    st.dataframe(leadtimes, use_container_width=True)

elif pagina == "Vencimientos":

    st.title("⚠️ Riesgo de Vencimiento por Lote")

    venc = inventario.copy()

    venc["Fecha_Vencimiento"] = pd.to_datetime(
        venc["Fecha_Vencimiento"],
        errors="coerce"
    )

    hoy = pd.Timestamp.today()

    venc["Meses_Restantes"] = (
        (venc["Fecha_Vencimiento"] - hoy).dt.days / 30
    ).round(1)

    def clasificar_riesgo(meses):
        if pd.isna(meses):
            return "Sin fecha"
        elif meses <= 3:
            return "🔴 Alto"
        elif meses <= 6:
            return "🟡 Medio"
        else:
            return "🟢 Bajo"

    venc["Riesgo"] = venc["Meses_Restantes"].apply(clasificar_riesgo)

    st.subheader("Tabla de vencimientos calculada")

    st.dataframe(
        venc[[
            "SKU",
            "Lote",
            "Stock_Lote",
            "Fecha_Vencimiento",
            "Meses_Restantes",
            "Almacen",
            "Estado",
            "Riesgo"
        ]],
        use_container_width=True
    )

    st.subheader("Stock por nivel de riesgo")

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()

    st.bar_chart(
        resumen,
        x="Riesgo",
        y="Stock_Lote"
    )
