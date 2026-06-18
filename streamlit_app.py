import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error

st.set_page_config(page_title="Sistema Inteligente de Inventarios Farmacéuticos", page_icon="🏥", layout="wide")

archivo_excel = "Base_Ficticia_Farmaceutica_Tesis.xlsx"

maestro = pd.read_excel(archivo_excel, sheet_name="Maestro_SKU")
ventas = pd.read_excel(archivo_excel, sheet_name="Ventas_Historicas")
inventario = pd.read_excel(archivo_excel, sheet_name="Inventario_Lotes")
leadtimes = pd.read_excel(archivo_excel, sheet_name="LeadTimes")
forecast_comercial = pd.read_excel(archivo_excel, sheet_name="Forecast_Comercial")

ventas["Fecha"] = pd.to_datetime(ventas["Fecha"])
forecast_comercial["Mes"] = pd.to_datetime(forecast_comercial["Mes"])

st.sidebar.title("🏥 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    ["Dashboard", "Ventas", "Inventario", "Lead Times", "Vencimientos", "Forecast"]
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
    st.dataframe(inventario.head(30), use_container_width=True)

elif pagina == "Ventas":

    st.title("📈 Ventas Históricas")
    st.dataframe(ventas.head(200), use_container_width=True)

elif pagina == "Inventario":

    st.title("📦 Inventario por Lote")
    st.dataframe(inventario, use_container_width=True)

elif pagina == "Lead Times":

    st.title("🚚 Lead Times")
    st.dataframe(leadtimes, use_container_width=True)

elif pagina == "Vencimientos":

    st.title("⚠️ Riesgo de Vencimiento por Lote")

    venc = inventario.copy()
    venc["Fecha_Vencimiento"] = pd.to_datetime(venc["Fecha_Vencimiento"], errors="coerce")

    hoy = pd.Timestamp.today()

    venc["Meses_Restantes"] = ((venc["Fecha_Vencimiento"] - hoy).dt.days / 30).round(1)

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

    st.dataframe(
        venc[[
            "SKU", "Lote", "Stock_Lote", "Fecha_Vencimiento",
            "Meses_Restantes", "Almacen", "Estado", "Riesgo"
        ]],
        use_container_width=True
    )

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()

    st.subheader("Stock por nivel de riesgo")
    st.bar_chart(resumen, x="Riesgo", y="Stock_Lote")

elif pagina == "Forecast":

    st.title("📈 Forecast Inteligente por SKU")

    sku = st.selectbox("Seleccionar SKU", sorted(ventas["SKU"].unique()))

    df_sku = ventas[ventas["SKU"] == sku].copy()
    df_sku = df_sku.sort_values("Fecha")
    df_sku = df_sku.groupby("Fecha", as_index=False)["Ventas"].sum()

    st.subheader(f"Ventas históricas - {sku}")
    st.line_chart(df_sku, x="Fecha", y="Ventas")

    serie = df_sku["Ventas"].astype(float).reset_index(drop=True)

    if len(serie) < 12:
        st.warning("Este SKU no tiene suficientes datos para comparar modelos.")
    else:
        test_size = 6
        train = serie[:-test_size]
        test = serie[-test_size:]
        fechas_test = df_sku["Fecha"].iloc[-test_size:].reset_index(drop=True)

        resultados = []
        graficos_modelos = {}

        # Modelo 1: Promedio móvil
        pred_ma = [train.tail(3).mean()] * test_size
        resultados.append(["Promedio móvil", mean_absolute_error(test, pred_ma),
                           np.sqrt(mean_squared_error(test, pred_ma)),
                           np.mean(np.abs((test - pred_ma) / test)) * 100])
        graficos_modelos["Promedio móvil"] = pred_ma

        # Modelo 2: Suavización exponencial simple
        try:
            modelo_ses = SimpleExpSmoothing(train).fit()
            pred_ses = modelo_ses.forecast(test_size)
            resultados.append(["Suavización exponencial", mean_absolute_error(test, pred_ses),
                               np.sqrt(mean_squared_error(test, pred_ses)),
                               np.mean(np.abs((test - pred_ses) / test)) * 100])
            graficos_modelos["Suavización exponencial"] = pred_ses
        except:
            pass

        # Modelo 3: Holt
        try:
            modelo_holt = Holt(train).fit()
            pred_holt = modelo_holt.forecast(test_size)
            resultados.append(["Holt", mean_absolute_error(test, pred_holt),
                               np.sqrt(mean_squared_error(test, pred_holt)),
                               np.mean(np.abs((test - pred_holt) / test)) * 100])
            graficos_modelos["Holt"] = pred_holt
        except:
            pass

        # Modelo 4: Holt-Winters
        try:
            modelo_hw = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=12
            ).fit()
            pred_hw = modelo_hw.forecast(test_size)
            resultados.append(["Holt-Winters", mean_absolute_error(test, pred_hw),
                               np.sqrt(mean_squared_error(test, pred_hw)),
                               np.mean(np.abs((test - pred_hw) / test)) * 100])
            graficos_modelos["Holt-Winters"] = pred_hw
        except:
            pass

        st.subheader("Comparación gráfica de modelos")

        for nombre_modelo, pred in graficos_modelos.items():
            df_graf = pd.DataFrame({
                "Fecha": fechas_test,
                "Ventas reales": test.values,
                nombre_modelo: np.array(pred)
            })

            st.write(f"### Modelo: {nombre_modelo}")
            st.line_chart(df_graf, x="Fecha", y=["Ventas reales", nombre_modelo])

        tabla_resultados = pd.DataFrame(
            resultados,
            columns=["Modelo", "MAE", "RMSE", "MAPE (%)"]
        )

        tabla_resultados = tabla_resultados.sort_values("MAPE (%)")

        st.subheader("Tabla comparativa de modelos")
        st.dataframe(tabla_resultados, use_container_width=True)

        mejor_modelo = tabla_resultados.iloc[0]["Modelo"]

        st.success(f"🏆 El mejor modelo para el SKU {sku} es: {mejor_modelo}")

        st.subheader("Comparación: Forecast comercial vs mejor modelo propuesto")

        pred_mejor = graficos_modelos[mejor_modelo]

        fc_sku = forecast_comercial[forecast_comercial["SKU"] == sku].copy()
        fc_sku = fc_sku.sort_values("Mes").head(test_size)

        comparacion = pd.DataFrame({
            "Fecha": fechas_test,
            "Ventas reales": test.values,
            "Mejor forecast propuesto": np.array(pred_mejor)
        })

        if len(fc_sku) >= test_size:
            comparacion["Forecast comercial"] = fc_sku["Forecast_Comercial"].values[:test_size]
            st.line_chart(
                comparacion,
                x="Fecha",
                y=["Ventas reales", "Mejor forecast propuesto", "Forecast comercial"]
            )
        else:
            st.warning("No hay suficientes datos de forecast comercial para este SKU.")
            st.line_chart(
                comparacion,
                x="Fecha",
                y=["Ventas reales", "Mejor forecast propuesto"]
            )

        st.dataframe(comparacion, use_container_width=True)
