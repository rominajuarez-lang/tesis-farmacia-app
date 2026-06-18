import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Pharma Inventory Control",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #0f172a, #020617 55%);
    color: #e5e7eb;
}
[data-testid="stSidebar"] {
    background: #020617;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #f8fafc;
}
.card {
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid rgba(56,189,248,0.35);
    border-radius: 20px;
    padding: 22px;
    box-shadow: 0 0 24px rgba(56,189,248,0.13);
}
.kpi-title {
    color: #94a3b8;
    font-size: 13px;
    letter-spacing: 1px;
}
.kpi-value {
    color: #f8fafc;
    font-size: 32px;
    font-weight: 800;
}
.kpi-sub {
    color: #38bdf8;
    font-size: 13px;
}
.section-card {
    background: rgba(15,23,42,0.72);
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 18px;
    padding: 18px;
    margin-top: 18px;
}
</style>
""", unsafe_allow_html=True)

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(archivo_excel, sheet_name="Maestro_SKU")
ventas = pd.read_excel(archivo_excel, sheet_name="Ventas_Historicas")
inventario = pd.read_excel(archivo_excel, sheet_name="Inventario_Lotes")
leadtimes = pd.read_excel(archivo_excel, sheet_name="LeadTimes")

ventas["Fecha"] = pd.to_datetime(ventas["Fecha"], errors="coerce")
inventario["Fecha_Vencimiento"] = pd.to_datetime(inventario["Fecha_Vencimiento"], errors="coerce")

st.sidebar.markdown("## ⚙️ CONTROL TOWER")
pagina = st.sidebar.radio(
    "Módulo",
    [
        "📊 Dashboard Ejecutivo",
        "📈 Ventas",
        "📦 Inventario",
        "🚚 Lead Times",
        "⚠️ Vencimientos"
    ]
)

st.markdown("# 🏥 SMART PHARMA INVENTORY CONTROL")
st.markdown("#### Forecasting · Inventory · Expiration Risk · Supply Chain Intelligence")

def dark_fig(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.75)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=50, b=20),
        height=360
    )
    return fig

if pagina == "📊 Dashboard Ejecutivo":

    total_skus = maestro["SKU"].nunique()
    total_lotes = inventario["Lote"].nunique()
    stock_total = inventario["Stock_Lote"].sum()
    lead_prom = round(leadtimes["LeadTime_Dias"].mean(), 1)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">TOTAL SKUs</div>
            <div class="kpi-value">{total_skus}</div>
            <div class="kpi-sub">Productos monitoreados</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">LOTES</div>
            <div class="kpi-value">{total_lotes}</div>
            <div class="kpi-sub">Trazabilidad por lote</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">STOCK TOTAL</div>
            <div class="kpi-value">{stock_total:,.0f}</div>
            <div class="kpi-sub">Unidades registradas</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">LEAD TIME PROM.</div>
            <div class="kpi-value">{lead_prom}</div>
            <div class="kpi-sub">Días promedio</div>
        </div>
        """, unsafe_allow_html=True)

    colA, colB = st.columns(2)

    with colA:
        inv_almacen = inventario.groupby("Almacen", as_index=False)["Stock_Lote"].sum()
        fig = px.bar(inv_almacen, x="Almacen", y="Stock_Lote", title="Stock por almacén")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    with colB:
        lt_pais = leadtimes.groupby("Pais", as_index=False)["LeadTime_Dias"].mean()
        fig = px.bar(lt_pais, x="Pais", y="LeadTime_Dias", title="Lead time promedio por país")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📦 Vista rápida de inventario")
    st.dataframe(inventario.head(20), use_container_width=True, height=320)
    st.markdown('</div>', unsafe_allow_html=True)

elif pagina == "📈 Ventas":

    st.subheader("📈 Análisis de ventas históricas")

    sku = st.selectbox("Seleccionar SKU", sorted(ventas["SKU"].unique()))

    df = ventas[ventas["SKU"] == sku].sort_values("Fecha")

    fig = px.line(df, x="Fecha", y="Ventas", title=f"Ventas históricas - {sku}", markers=True)
    st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True, height=320)

elif pagina == "📦 Inventario":

    st.subheader("📦 Inventario por lote")

    col1, col2 = st.columns(2)

    with col1:
        filtro_almacen = st.selectbox("Filtrar por almacén", ["Todos"] + sorted(inventario["Almacen"].dropna().unique()))

    with col2:
        filtro_estado = st.selectbox("Filtrar por estado", ["Todos"] + sorted(inventario["Estado"].dropna().unique()))

    inv = inventario.copy()

    if filtro_almacen != "Todos":
        inv = inv[inv["Almacen"] == filtro_almacen]

    if filtro_estado != "Todos":
        inv = inv[inv["Estado"] == filtro_estado]

    fig = px.treemap(
        inv,
        path=["Almacen", "Estado", "SKU"],
        values="Stock_Lote",
        title="Mapa de concentración de inventario"
    )
    st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.dataframe(inv, use_container_width=True, height=420)

elif pagina == "🚚 Lead Times":

    st.subheader("🚚 Análisis de lead times")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.box(leadtimes, x="Pais", y="LeadTime_Dias", title="Distribución de lead time por país")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    with col2:
        fig = px.scatter(
            leadtimes,
            x="LeadTime_Dias",
            y="Proveedor",
            color="Pais",
            title="Lead time por proveedor"
        )
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.dataframe(leadtimes, use_container_width=True, height=380)

elif pagina == "⚠️ Vencimientos":

    st.subheader("⚠️ Riesgo de vencimiento por lote")

    venc = inventario.copy()
    venc["Meses_Restantes"] = ((venc["Fecha_Vencimiento"] - pd.Timestamp.today()).dt.days / 30).round(1)

    def riesgo(meses):
        if pd.isna(meses):
            return "Sin fecha"
        elif meses <= 3:
            return "🔴 Alto"
        elif meses <= 6:
            return "🟡 Medio"
        else:
            return "🟢 Bajo"

    venc["Riesgo"] = venc["Meses_Restantes"].apply(riesgo)

    c1, c2, c3 = st.columns(3)

    alto = venc[venc["Riesgo"] == "🔴 Alto"]["Stock_Lote"].sum()
    medio = venc[venc["Riesgo"] == "🟡 Medio"]["Stock_Lote"].sum()
    bajo = venc[venc["Riesgo"] == "🟢 Bajo"]["Stock_Lote"].sum()

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">RIESGO ALTO</div>
            <div class="kpi-value">{alto:,.0f}</div>
            <div class="kpi-sub">Unidades críticas</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">RIESGO MEDIO</div>
            <div class="kpi-value">{medio:,.0f}</div>
            <div class="kpi-sub">Unidades en observación</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">RIESGO BAJO</div>
            <div class="kpi-value">{bajo:,.0f}</div>
            <div class="kpi-sub">Unidades saludables</div>
        </div>
        """, unsafe_allow_html=True)

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()

    colA, colB = st.columns(2)

    with colA:
        fig = px.bar(resumen, x="Riesgo", y="Stock_Lote", title="Stock por nivel de riesgo")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    with colB:
        fig = px.pie(resumen, names="Riesgo", values="Stock_Lote", title="Participación por riesgo")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Detalle de lotes")
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
        use_container_width=True,
        height=420
    )
    st.markdown('</div>', unsafe_allow_html=True)
