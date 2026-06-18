import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

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
}
.card {
    background: linear-gradient(135deg, #0f172a, #111827);
    border: 1px solid rgba(56,189,248,0.35);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 0 24px rgba(56,189,248,0.13);
}
.kpi-title {
    color: #94a3b8;
    font-size: 13px;
    letter-spacing: 1px;
}
.kpi-value {
    color: #f8fafc;
    font-size: 30px;
    font-weight: 800;
}
.kpi-sub {
    color: #38bdf8;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(archivo_excel, sheet_name="Maestro_SKU")
ventas = pd.read_excel(archivo_excel, sheet_name="Ventas_Historicas")
inventario = pd.read_excel(archivo_excel, sheet_name="Inventario_Lotes")
leadtimes = pd.read_excel(archivo_excel, sheet_name="LeadTimes")
forecast_comercial = pd.read_excel(archivo_excel, sheet_name="Forecast_Comercial")

ventas["Fecha"] = pd.to_datetime(ventas["Fecha"], errors="coerce")
forecast_comercial["Mes"] = pd.to_datetime(forecast_comercial["Mes"], errors="coerce")
inventario["Fecha_Vencimiento"] = pd.to_datetime(inventario["Fecha_Vencimiento"], errors="coerce")

def dark_fig(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.7)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=50, b=20),
        height=360
    )
    return fig

def wmape(real, pred):
    real = np.array(real, dtype=float)
    pred = np.array(pred, dtype=float)
    return np.sum(np.abs(real - pred)) / max(np.sum(np.abs(real)), 1) * 100

def bias_pct(real, pred):
    real = np.array(real, dtype=float)
    pred = np.array(pred, dtype=float)
    return np.sum(pred - real) / max(np.sum(real), 1) * 100

def evaluar_modelos_sku(sku):
    df = ventas[ventas["SKU"] == sku].copy()
    df = df.groupby("Fecha", as_index=False)["Ventas"].sum().sort_values("Fecha")

    train = df[df["Fecha"].dt.year == 2024]
    test = df[df["Fecha"].dt.year == 2025]

    if len(train) == 0 or len(test) == 0:
        return None

    y_train = train["Ventas"].astype(float).reset_index(drop=True)
    y_test = test["Ventas"].astype(float).reset_index(drop=True)
    fechas_test = test["Fecha"].reset_index(drop=True)
    n = len(y_test)

    modelos = {}

    fc = forecast_comercial[
        (forecast_comercial["SKU"] == sku) &
        (forecast_comercial["Mes"].dt.year == 2025)
    ].sort_values("Mes")

    if len(fc) >= n:
        modelos["Forecast comercial"] = fc["Forecast_Comercial"].values[:n]

    modelos["Promedio móvil"] = np.repeat(y_train.tail(3).mean(), n)

    try:
        x_train = np.arange(len(y_train)).reshape(-1, 1)
        x_test = np.arange(len(y_train), len(y_train) + n).reshape(-1, 1)
        reg = LinearRegression()
        reg.fit(x_train, y_train)
        modelos["Regresión lineal"] = reg.predict(x_test)
    except:
        pass

    try:
        ses = SimpleExpSmoothing(y_train).fit()
        modelos["Suavizamiento exponencial simple"] = ses.forecast(n).values
    except:
        pass

    try:
        holt = Holt(y_train).fit()
        modelos["Holt"] = holt.forecast(n).values
    except:
        pass

    try:
        if len(y_train) >= 12:
            hw = ExponentialSmoothing(
                y_train,
                trend="add",
                seasonal="add",
                seasonal_periods=12
            ).fit()
            modelos["Holt-Winters"] = hw.forecast(n).values
    except:
        pass

    try:
        arima = ARIMA(y_train, order=(1, 1, 1)).fit()
        modelos["ARIMA"] = arima.forecast(n).values
    except:
        pass

    costo = maestro.loc[maestro["SKU"] == sku, "Costo_Unitario"].iloc[0]
    costo = pd.to_numeric(costo, errors="coerce")
    if pd.isna(costo):
        costo = 1

    resultados = []

    for modelo, pred in modelos.items():
        pred = np.maximum(np.array(pred, dtype=float), 0)

        error_abs = np.abs(pred - y_test)
        perdida = np.sum(error_abs * costo)

        exceso = np.maximum(pred - y_test, 0).sum()
        faltante = np.maximum(y_test - pred, 0).sum()

        resultados.append({
            "SKU": sku,
            "Modelo": modelo,
            "wMAPE (%)": wmape(y_test, pred),
            "Bias (%)": bias_pct(y_test, pred),
            "Exceso und": exceso,
            "Faltante und": faltante,
            "Pérdida estimada S/": perdida
        })

    tabla = pd.DataFrame(resultados)

    if "Forecast comercial" not in tabla["Modelo"].values:
        return None

    propuestos = tabla[tabla["Modelo"] != "Forecast comercial"].copy()
    if propuestos.empty:
        return None

    mejor = propuestos.sort_values("wMAPE (%)").iloc[0]

    empresa = tabla[tabla["Modelo"] == "Forecast comercial"].iloc[0]

    return {
        "sku": sku,
        "fechas": fechas_test,
        "real": y_test,
        "modelos": modelos,
        "tabla": tabla,
        "mejor_modelo": mejor["Modelo"],
        "perdida_empresa": empresa["Pérdida estimada S/"],
        "perdida_propuesta": mejor["Pérdida estimada S/"],
        "ahorro": empresa["Pérdida estimada S/"] - mejor["Pérdida estimada S/"],
        "wmape_empresa": empresa["wMAPE (%)"],
        "wmape_propuesto": mejor["wMAPE (%)"],
        "bias_empresa": empresa["Bias (%)"],
        "bias_propuesto": mejor["Bias (%)"]
    }

@st.cache_data
def evaluar_todos_los_skus():
    lista = []
    detalles = {}

    for sku in sorted(ventas["SKU"].unique()):
        r = evaluar_modelos_sku(sku)
        if r is not None:
            detalles[sku] = r
            lista.append({
                "SKU": sku,
                "Mejor modelo": r["mejor_modelo"],
                "wMAPE empresa (%)": r["wmape_empresa"],
                "wMAPE propuesto (%)": r["wmape_propuesto"],
                "Bias empresa (%)": r["bias_empresa"],
                "Bias propuesto (%)": r["bias_propuesto"],
                "Pérdida empresa S/": r["perdida_empresa"],
                "Pérdida propuesta S/": r["perdida_propuesta"],
                "Ahorro potencial S/": r["ahorro"]
            })

    return pd.DataFrame(lista), detalles

st.sidebar.markdown("## ⚙️ CONTROL TOWER")
pagina = st.sidebar.radio(
    "Módulo",
    [
        "📊 Dashboard Ejecutivo",
        "📈 Ventas",
        "📦 Inventario",
        "🚚 Lead Times",
        "⚠️ Vencimientos",
        "🧠 Forecast 2025"
    ]
)

st.markdown("# 🏥 SMART PHARMA INVENTORY CONTROL")
st.markdown("#### Forecasting · Inventory · Expiration Risk · Economic Impact")

if pagina == "📊 Dashboard Ejecutivo":

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">TOTAL SKUs</div>
            <div class="kpi-value">{maestro["SKU"].nunique()}</div>
            <div class="kpi-sub">Productos monitoreados</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">LOTES</div>
            <div class="kpi-value">{inventario["Lote"].nunique()}</div>
            <div class="kpi-sub">Trazabilidad por lote</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">STOCK TOTAL</div>
            <div class="kpi-value">{inventario["Stock_Lote"].sum():,.0f}</div>
            <div class="kpi-sub">Unidades registradas</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">LEAD TIME PROM.</div>
            <div class="kpi-value">{round(leadtimes["LeadTime_Dias"].mean(),1)}</div>
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

elif pagina == "📈 Ventas":

    st.subheader("📈 Ventas históricas")
    sku = st.selectbox("Seleccionar SKU", sorted(ventas["SKU"].unique()))
    df = ventas[ventas["SKU"] == sku].sort_values("Fecha")
    fig = px.line(df, x="Fecha", y="Ventas", title=f"Ventas históricas - {sku}", markers=True)
    st.plotly_chart(dark_fig(fig), use_container_width=True)
    st.dataframe(df, use_container_width=True, height=320)

elif pagina == "📦 Inventario":

    st.subheader("📦 Inventario por lote")
    st.dataframe(inventario, use_container_width=True, height=500)

elif pagina == "🚚 Lead Times":

    st.subheader("🚚 Lead times")
    fig = px.box(leadtimes, x="Pais", y="LeadTime_Dias", title="Distribución de lead time por país")
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

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()

    colA, colB = st.columns(2)

    with colA:
        fig = px.bar(resumen, x="Riesgo", y="Stock_Lote", title="Stock por nivel de riesgo")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    with colB:
        fig = px.pie(resumen, names="Riesgo", values="Stock_Lote", title="Participación por riesgo")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

    st.dataframe(venc, use_container_width=True, height=420)

elif pagina == "🧠 Forecast 2025":

    st.subheader("🧠 Evaluación económica del forecast 2025")

    resumen_skus, detalles = evaluar_todos_los_skus()

    if resumen_skus.empty:
        st.warning("No se pudo evaluar ningún SKU. Verifica que existan ventas 2024, ventas 2025 y forecast comercial 2025.")
    else:
        perdida_empresa_total = resumen_skus["Pérdida empresa S/"].sum()
        perdida_propuesta_total = resumen_skus["Pérdida propuesta S/"].sum()
        ahorro_total = resumen_skus["Ahorro potencial S/"].sum()

        wmape_empresa_total = (
            resumen_skus["wMAPE empresa (%)"].mean()
        )
        wmape_propuesto_total = (
            resumen_skus["wMAPE propuesto (%)"].mean()
        )

        reduccion_error = (
            (wmape_empresa_total - wmape_propuesto_total) / wmape_empresa_total * 100
            if wmape_empresa_total > 0
            else 0
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-title">REDUCCIÓN DEL ERROR</div>
                <div class="kpi-value">{reduccion_error:.1f}%</div>
                <div class="kpi-sub">Promedio de wMAPE empresa vs propuesta</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-title">AHORRO POTENCIAL CON FORECAST PROPUESTO</div>
                <div class="kpi-value">S/ {ahorro_total:,.0f}</div>
                <div class="kpi-sub">Todos los SKUs evaluados</div>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("Resumen por SKU")
        st.dataframe(resumen_skus.sort_values("Ahorro potencial S/", ascending=False), use_container_width=True, height=300)

        modelos_count = resumen_skus["Mejor modelo"].value_counts().reset_index()
        modelos_count.columns = ["Modelo", "Cantidad de SKUs"]

        fig = px.pie(modelos_count, names="Modelo", values="Cantidad de SKUs", title="Distribución de modelos ganadores por SKU")
        st.plotly_chart(dark_fig(fig), use_container_width=True)

        st.divider()

        st.subheader("Análisis detallado por SKU")

        sku = st.selectbox("Seleccionar SKU", sorted(detalles.keys()))
        r = detalles[sku]

        st.markdown(f"### Mejor modelo propuesto para {sku}: **{r['mejor_modelo']}**")

        for modelo, pred in r["modelos"].items():
            if modelo == "Forecast comercial":
                continue

            col1, col2 = st.columns([2, 1])

            pred = np.maximum(np.array(pred, dtype=float), 0)

            df_graf = pd.DataFrame({
                "Fecha": r["fechas"],
                "Ventas reales 2025": r["real"],
                "Forecast empresa": np.maximum(r["modelos"]["Forecast comercial"], 0),
                f"Forecast propuesto: {modelo}": pred
            })

            with col1:
                fig = px.line(
                    df_graf,
                    x="Fecha",
                    y=["Ventas reales 2025", "Forecast empresa", f"Forecast propuesto: {modelo}"],
                    title=f"{modelo}: empresa vs propuesta vs ventas reales",
                    markers=True
                )
                st.plotly_chart(dark_fig(fig), use_container_width=True)

            with col2:
                tabla_modelo = r["tabla"][r["tabla"]["Modelo"].isin(["Forecast comercial", modelo])].copy()
                tabla_modelo = tabla_modelo[[
                    "Modelo",
                    "wMAPE (%)",
                    "Bias (%)",
                    "Exceso und",
                    "Faltante und",
                    "Pérdida estimada S/"
                ]]
                st.dataframe(tabla_modelo, use_container_width=True, height=250)

        st.divider()

        st.subheader("Comparación final con el mejor modelo")

        mejor = r["mejor_modelo"]

        df_final = pd.DataFrame({
            "Fecha": r["fechas"],
            "Ventas reales 2025": r["real"],
            "Forecast empresa": np.maximum(r["modelos"]["Forecast comercial"], 0),
            f"Mejor forecast propuesto: {mejor}": np.maximum(r["modelos"][mejor], 0)
        })

        fig = px.line(
            df_final,
            x="Fecha",
            y=["Ventas reales 2025", "Forecast empresa", f"Mejor forecast propuesto: {mejor}"],
            title="Ventas reales vs forecast empresa vs mejor forecast propuesto",
            markers=True
        )
        st.plotly_chart(dark_fig(fig), use_container_width=True)

        st.dataframe(df_final, use_container_width=True, height=320)
