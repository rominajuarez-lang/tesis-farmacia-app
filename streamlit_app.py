import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Smart Pharma Inventory Control",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #111827 100%);
    color: #e5e7eb;
}
[data-testid="stSidebar"] {
    background-color: #020617;
}
h1, h2, h3 {
    color: #38bdf8;
}
.metric-card {
    background: rgba(15, 23, 42, 0.95);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #1e40af;
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.18);
}
.metric-title {
    color: #94a3b8;
    font-size: 14px;
}
.metric-value {
    color: #f8fafc;
    font-size: 30px;
    font-weight: 700;
}
.metric-sub {
    color: #22c55e;
    font-size: 13px;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(archivo_excel, sheet_name="Maestro_SKU")
ventas = pd.read_excel(archivo_excel, sheet_name="Ventas_Historicas")
inventario = pd.read_excel(archivo_excel, sheet_name="Inventario_Lotes")
leadtimes = pd.read_excel(archivo_excel, sheet_name="LeadTimes")

st.sidebar.title("⚙️ CONTROL TOWER")
pagina = st.sidebar.radio(
    "Módulo",
    ["Dashboard", "Ventas", "Inventario", "Lead Times", "Vencimientos"]
)

st.markdown("# 🏥 SMART PHARMA INVENTORY CONTROL")
st.markdown("### Forecasting | Inventory | Expiration Risk | Supply Chain Intelligence")

if pagina == "Dashboard":

    total_skus = maestro["SKU"].nunique()
    total_lotes = inventario["Lote"].nunique()
    stock_total = inventario["Stock_Lote"].sum()
    lead_prom = round(leadtimes["LeadTime_Dias"].mean(), 1)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL SKUs</div>
            <div class="metric-value">{total_skus}</div>
            <div class="metric-sub">Productos activos</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">LOTES REGISTRADOS</div>
            <div class="metric-value">{total_lotes}</div>
            <div class="metric-sub">Trazabilidad operativa</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">STOCK TOTAL</div>
            <div class="metric-value">{stock_total:,.0f}</div>
            <div class="metric-sub">Unidades en inventario</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">LEAD TIME PROM.</div>
            <div class="metric-value">{lead_prom}</div>
            <div class="metric-sub">Días promedio</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📦 Inventario por lote")
    st.dataframe(inventario.head(30), use_container_width=True)

elif pagina == "Ventas":
    st.subheader("📈 Ventas históricas")
    st.dataframe(ventas.head(300), use_container_width=True)

elif pagina == "Inventario":
    st.subheader("📦 Inventario por lote")
    st.dataframe(inventario, use_container_width=True)

elif pagina == "Lead Times":
    st.subheader("🚚 Lead times")
    st.dataframe(leadtimes, use_container_width=True)

elif pagina == "Vencimientos":
    st.subheader("⚠️ Riesgo de vencimiento por lote")

    venc = inventario.copy()
    venc["Fecha_Vencimiento"] = pd.to_datetime(venc["Fecha_Vencimiento"], errors="coerce")
    venc["Meses_Restantes"] = ((venc["Fecha_Vencimiento"] - pd.Timestamp.today()).dt.days / 30).round(1)

    def riesgo(meses):
        if pd.isna(meses):
            return "Sin fecha"
        if meses <= 3:
            return "🔴 Alto"
        if meses <= 6:
            return "🟡 Medio"
        return "🟢 Bajo"

    venc["Riesgo"] = venc["Meses_Restantes"].apply(riesgo)

    st.dataframe(venc, use_container_width=True)

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()
    st.subheader("Stock por nivel de riesgo")
    st.bar_chart(resumen, x="Riesgo", y="Stock_Lote")
