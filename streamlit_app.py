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
    "⚠️ Vencimientos",
    "🧠 Forecast 2025"
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

elif pagina == "🧠 Forecast 2025":

    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA

    forecast_comercial = pd.read_excel(
        archivo_excel,
        sheet_name="Forecast_Comercial"
    )

    forecast_comercial["Mes"] = pd.to_datetime(
        forecast_comercial["Mes"],
        errors="coerce"
    )

    st.subheader("🧠 Evaluación de modelos de pronóstico - Validación 2025")

    st.info(
        "Los modelos se entrenan con ventas reales 2024 y se validan contra ventas reales 2025. "
        "Luego se compara el mejor modelo propuesto contra el Forecast Comercial 2025."
    )

    sku = st.selectbox(
        "Seleccionar SKU",
        sorted(ventas["SKU"].unique())
    )

    df_sku = ventas[ventas["SKU"] == sku].copy()
    df_sku = df_sku.sort_values("Fecha")
    df_sku = df_sku.groupby("Fecha", as_index=False)["Ventas"].sum()

    train = df_sku[df_sku["Fecha"].dt.year == 2024].copy()
    test = df_sku[df_sku["Fecha"].dt.year == 2025].copy()

    if len(train) == 0 or len(test) == 0:
        st.warning(
            "Este SKU necesita ventas reales de 2024 para entrenar y ventas reales de 2025 para validar."
        )
        st.dataframe(df_sku, use_container_width=True)

    else:
        y_train = train["Ventas"].astype(float).reset_index(drop=True)
        y_test = test["Ventas"].astype(float).reset_index(drop=True)
        fechas_test = test["Fecha"].reset_index(drop=True)
        n = len(y_test)

        modelos = {}

        fc_sku = forecast_comercial[
            (forecast_comercial["SKU"] == sku) &
            (forecast_comercial["Mes"].dt.year == 2025)
        ].sort_values("Mes")

        if len(fc_sku) >= n:
            modelos["Forecast comercial"] = fc_sku["Forecast_Comercial"].values[:n]

        modelos["Promedio móvil"] = np.repeat(y_train.tail(3).mean(), n)

        try:
            x_train = np.arange(len(y_train)).reshape(-1, 1)
            x_test = np.arange(len(y_train), len(y_train) + n).reshape(-1, 1)
            reg = LinearRegression()
            reg.fit(x_train, y_train)
            modelos["Regresión lineal"] = reg.predict(x_test)
        except Exception:
            pass

        try:
            ses = SimpleExpSmoothing(y_train).fit()
            modelos["Suavizamiento exponencial simple"] = ses.forecast(n).values
        except Exception:
            pass

        try:
            holt = Holt(y_train).fit()
            modelos["Holt"] = holt.forecast(n).values
        except Exception:
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
        except Exception:
            pass

        try:
            arima = ARIMA(y_train, order=(1, 1, 1)).fit()
            modelos["ARIMA"] = arima.forecast(n).values
        except Exception:
            pass

        def calcular_mape(real, pred):
            real = np.array(real, dtype=float)
            pred = np.array(pred, dtype=float)
            return np.mean(
                np.abs((real - pred) / np.where(real == 0, 1, real))
            ) * 100

        resultados = []

        costo_unitario = maestro.loc[
            maestro["SKU"] == sku,
            "Costo_Unitario"
        ].iloc[0]

        costo_unitario = pd.to_numeric(
            costo_unitario,
            errors="coerce"
        )

        if pd.isna(costo_unitario):
            costo_unitario = 1

        for nombre, pred in modelos.items():

            pred = np.array(pred, dtype=float)
            pred = np.maximum(pred, 0)

            mae = mean_absolute_error(y_test, pred)
            rmse = np.sqrt(mean_squared_error(y_test, pred))
            mape = calcular_mape(y_test, pred)
            bias = np.mean(pred - y_test)

            sobrestock = np.maximum(pred - y_test, 0)
            perdida = np.sum(sobrestock * costo_unitario)

            resultados.append({
                "Modelo": nombre,
                "MAE": round(mae, 2),
                "RMSE": round(rmse, 2),
                "MAPE (%)": round(mape, 2),
                "Bias": round(bias, 2),
                "Sobrestock estimado": round(sobrestock.sum(), 0),
                "Pérdida estimada S/": round(perdida, 2)
            })

        tabla = pd.DataFrame(resultados).sort_values("MAPE (%)")

        mejor_modelo = tabla.iloc[0]["Modelo"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-title">MEJOR MODELO</div>
                <div class="kpi-value">{mejor_modelo}</div>
                <div class="kpi-sub">Según menor MAPE</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            mejor_mape = tabla.iloc[0]["MAPE (%)"]
            st.markdown(f"""
            <div class="card">
                <div class="kpi-title">MAPE MODELO PROPUESTO</div>
                <div class="kpi-value">{mejor_mape}%</div>
                <div class="kpi-sub">Error porcentual medio</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            perdida_mejor = tabla.iloc[0]["Pérdida estimada S/"]
            st.markdown(f"""
            <div class="card">
                <div class="kpi-title">PÉRDIDA PROPUESTA</div>
                <div class="kpi-value">S/ {perdida_mejor:,.0f}</div>
                <div class="kpi-sub">Sobrestock valorizado</div>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("📊 Comparación individual de modelos")

        for nombre, pred in modelos.items():
            pred = np.maximum(np.array(pred, dtype=float), 0)

            graf = pd.DataFrame({
                "Fecha": fechas_test,
                "Ventas reales 2025": y_test,
                nombre: pred
            })

            fig = px.line(
                graf,
                x="Fecha",
                y=["Ventas reales 2025", nombre],
                title=f"{nombre} vs ventas reales 2025",
                markers=True
            )

            st.plotly_chart(
                dark_fig(fig),
                use_container_width=True
            )

        st.subheader("📋 Tabla comparativa de modelos")
        st.dataframe(
            tabla,
            use_container_width=True,
            height=320
        )

        if "Forecast comercial" in modelos:

            perdida_comercial = tabla.loc[
                tabla["Modelo"] == "Forecast comercial",
                "Pérdida estimada S/"
            ].iloc[0]

            perdida_mejor = tabla.loc[
                tabla["Modelo"] == mejor_modelo,
                "Pérdida estimada S/"
            ].iloc[0]

            diferencia = perdida_comercial - perdida_mejor

            reduccion = (
                diferencia / perdida_comercial * 100
                if perdida_comercial > 0
                else 0
            )

            st.subheader("💰 Impacto económico estimado")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(f"""
                <div class="card">
                    <div class="kpi-title">PÉRDIDA FORECAST COMERCIAL</div>
                    <div class="kpi-value">S/ {perdida_comercial:,.0f}</div>
                    <div class="kpi-sub">Escenario actual</div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown(f"""
                <div class="card">
                    <div class="kpi-title">PÉRDIDA MODELO PROPUESTO</div>
                    <div class="kpi-value">S/ {perdida_mejor:,.0f}</div>
                    <div class="kpi-sub">Escenario propuesto</div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                st.markdown(f"""
                <div class="card">
                    <div class="kpi-title">REDUCCIÓN ESTIMADA</div>
                    <div class="kpi-value">{reduccion:.1f}%</div>
                    <div class="kpi-sub">Ahorro potencial</div>
                </div>
                """, unsafe_allow_html=True)

            comparacion = pd.DataFrame({
                "Fecha": fechas_test,
                "Ventas reales 2025": y_test,
                "Forecast comercial": np.maximum(modelos["Forecast comercial"], 0),
                f"Mejor modelo: {mejor_modelo}": np.maximum(modelos[mejor_modelo], 0)
            })

            fig = px.line(
                comparacion,
                x="Fecha",
                y=[
                    "Ventas reales 2025",
                    "Forecast comercial",
                    f"Mejor modelo: {mejor_modelo}"
                ],
                title="Comparación final: ventas reales vs forecast comercial vs modelo propuesto",
                markers=True
            )

            st.plotly_chart(
                dark_fig(fig),
                use_container_width=True
            )

            st.dataframe(
                comparacion,
                use_container_width=True,
                height=320
            )

            st.info(
                f"Si la empresa hubiera usado el modelo propuesto ({mejor_modelo}) "
                f"en lugar del Forecast Comercial durante 2025, la pérdida estimada por sobrestock "
                f"se habría reducido aproximadamente en S/ {diferencia:,.2f}."
            )
