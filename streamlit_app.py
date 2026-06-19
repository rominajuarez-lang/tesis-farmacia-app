import streamlit as st
import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

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
forecast_comercial = pd.read_excel(archivo_excel, sheet_name="Forecast_Comercial")

ventas["Fecha"] = pd.to_datetime(ventas["Fecha"], errors="coerce")
forecast_comercial["Mes"] = pd.to_datetime(forecast_comercial["Mes"], errors="coerce")

st.sidebar.title("🏥 Menú")

pagina = st.sidebar.radio(
    "Seleccionar módulo",
    ["Dashboard", "Ventas", "Inventario", "Lead Times", "Vencimientos", "Forecast 2025"]
)

def calcular_mape(real, pred):
    real = np.array(real, dtype=float)
    pred = np.array(pred, dtype=float)
    return np.mean(np.abs((real - pred) / np.where(real == 0, 1, real))) * 100

def calcular_metricas(real, pred):
    real = np.array(real, dtype=float)
    pred = np.array(pred, dtype=float)

    return {
        "MAE": mean_absolute_error(real, pred),
        "RMSE": np.sqrt(mean_squared_error(real, pred)),
        "MAPE (%)": calcular_mape(real, pred),
        "Bias": np.mean(pred - real)
    }

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
    st.dataframe(ventas.head(300), use_container_width=True)

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

    resumen = venc.groupby("Riesgo", as_index=False)["Stock_Lote"].sum()

    st.subheader("Stock por nivel de riesgo")
    st.bar_chart(resumen, x="Riesgo", y="Stock_Lote")

elif pagina == "Forecast 2025":

    st.title("📊 Evaluación de Modelos de Pronóstico - Validación 2025")

    st.info(
        "Metodología: los modelos se entrenan con ventas reales del año 2024 "
        "y se validan contra ventas reales del año 2025. Luego se compara el mejor "
        "modelo propuesto contra el Forecast Comercial 2025."
    )

    sku = st.selectbox("Seleccionar SKU", sorted(ventas["SKU"].unique()))

    df_sku = ventas[ventas["SKU"] == sku].copy()
    df_sku = df_sku.sort_values("Fecha")
    df_sku = df_sku.groupby("Fecha", as_index=False)["Ventas"].sum()

    train = df_sku[df_sku["Fecha"].dt.year == 2024].copy()
    test = df_sku[df_sku["Fecha"].dt.year == 2025].copy()

    st.subheader(f"Ventas históricas del SKU {sku}")
    st.line_chart(df_sku, x="Fecha", y="Ventas")

    if len(train) == 0 or len(test) == 0:
        st.warning(
            "Este SKU no tiene datos suficientes. Se necesitan ventas reales de 2024 "
            "para entrenar y ventas reales de 2025 para validar."
        )
        st.dataframe(df_sku, use_container_width=True)

    else:
        y_train = train["Ventas"].astype(float).reset_index(drop=True)
        y_test = test["Ventas"].astype(float).reset_index(drop=True)
        fechas_test = test["Fecha"].reset_index(drop=True)
        n = len(y_test)

        modelos = {}

        # Forecast comercial 2025
        fc_sku = forecast_comercial[
            (forecast_comercial["SKU"] == sku) &
            (forecast_comercial["Mes"].dt.year == 2025)
        ].copy()

        fc_sku = fc_sku.sort_values("Mes")

        if len(fc_sku) >= n:
            modelos["Forecast comercial"] = fc_sku["Forecast_Comercial"].values[:n]

        # Promedio móvil de 3 meses
        modelos["Promedio móvil"] = np.repeat(y_train.tail(3).mean(), n)

        # Regresión lineal
        try:
            x_train = np.arange(len(y_train)).reshape(-1, 1)
            x_test = np.arange(len(y_train), len(y_train) + n).reshape(-1, 1)

            reg = LinearRegression()
            reg.fit(x_train, y_train)

            modelos["Regresión lineal"] = reg.predict(x_test)
        except Exception:
            pass

        # Suavizamiento exponencial simple
        try:
            ses = SimpleExpSmoothing(y_train).fit()
            modelos["Suavizamiento exponencial simple"] = ses.forecast(n).values
        except Exception:
            pass

        # Holt
        try:
            modelo_holt = Holt(y_train).fit()
            modelos["Holt"] = modelo_holt.forecast(n).values
        except Exception:
            pass

        # Holt-Winters
        try:
            if len(y_train) >= 12:
                modelo_hw = ExponentialSmoothing(
                    y_train,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=12
                ).fit()
                modelos["Holt-Winters"] = modelo_hw.forecast(n).values
        except Exception:
            pass

        # ARIMA
        try:
            modelo_arima = ARIMA(y_train, order=(1, 1, 1)).fit()
            modelos["ARIMA"] = modelo_arima.forecast(n).values
        except Exception:
            pass

        costo_unitario = maestro.loc[maestro["SKU"] == sku, "Costo_Unitario"].iloc[0]
        costo_unitario = pd.to_numeric(costo_unitario, errors="coerce")

        if pd.isna(costo_unitario):
            costo_unitario = 1

        resultados = []

        for nombre_modelo, pred in modelos.items():

            pred = np.array(pred, dtype=float)
            pred = np.maximum(pred, 0)

            met = calcular_metricas(y_test, pred)

            sobrestock = np.maximum(pred - y_test, 0)
            perdida_estimada = np.sum(sobrestock * costo_unitario)

            resultados.append(
                {
                    "Modelo": nombre_modelo,
                    "MAE": round(met["MAE"], 2),
                    "RMSE": round(met["RMSE"], 2),
                    "MAPE (%)": round(met["MAPE (%)"], 2),
                    "Bias": round(met["Bias"], 2),
                    "Sobrestock estimado (und)": round(sobrestock.sum(), 0),
                    "Pérdida estimada S/": round(perdida_estimada, 2)
                }
            )

        tabla_resultados = pd.DataFrame(resultados)

        if tabla_resultados.empty:
            st.error("No se pudo generar ningún modelo para este SKU.")
        else:
            tabla_resultados = tabla_resultados.sort_values("MAPE (%)")

            st.subheader("Gráficos individuales por modelo")

            for nombre_modelo, pred in modelos.items():
                pred = np.array(pred, dtype=float)
                pred = np.maximum(pred, 0)

                df_graf = pd.DataFrame(
                    {
                        "Fecha": fechas_test,
                        "Ventas reales 2025": y_test,
                        nombre_modelo: pred
                    }
                )

                st.write(f"### {nombre_modelo}")
                st.line_chart(
                    df_graf,
                    x="Fecha",
                    y=["Ventas reales 2025", nombre_modelo]
                )

            st.subheader("Tabla comparativa de modelos")
            st.dataframe(tabla_resultados, use_container_width=True)

            mejor_modelo = tabla_resultados.iloc[0]["Modelo"]

            st.success(f"🏆 Mejor modelo según MAPE para el SKU {sku}: {mejor_modelo}")

            st.subheader("Comparación final: Forecast comercial vs mejor modelo propuesto")

            if "Forecast comercial" in modelos:

                perdida_comercial = tabla_resultados.loc[
                    tabla_resultados["Modelo"] == "Forecast comercial",
                    "Pérdida estimada S/"
                ].iloc[0]

                perdida_mejor = tabla_resultados.loc[
                    tabla_resultados["Modelo"] == mejor_modelo,
                    "Pérdida estimada S/"
                ].iloc[0]

                diferencia_perdida = perdida_comercial - perdida_mejor

                reduccion = (
                    diferencia_perdida / perdida_comercial * 100
                    if perdida_comercial > 0
                    else 0
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Pérdida Forecast Comercial",
                    f"S/ {perdida_comercial:,.2f}"
                )

                col2.metric(
                    "Pérdida Modelo Propuesto",
                    f"S/ {perdida_mejor:,.2f}"
                )

                col3.metric(
                    "Reducción estimada",
                    f"{reduccion:.2f}%"
                )

                comparacion_final = pd.DataFrame(
                    {
                        "Fecha": fechas_test,
                        "Ventas reales 2025": y_test,
                        "Forecast comercial": np.maximum(modelos["Forecast comercial"], 0),
                        f"Mejor modelo: {mejor_modelo}": np.maximum(modelos[mejor_modelo], 0)
                    }
                )

                st.line_chart(
                    comparacion_final,
                    x="Fecha",
                    y=[
                        "Ventas reales 2025",
                        "Forecast comercial",
                        f"Mejor modelo: {mejor_modelo}"
                    ]
                )

                st.dataframe(comparacion_final, use_container_width=True)

                st.info(
                    f"Interpretación: si la empresa hubiera usado el modelo propuesto "
                    f"({mejor_modelo}) en lugar del forecast comercial durante 2025, "
                    f"la pérdida estimada por sobrestock se habría reducido en "
                    f"aproximadamente S/ {diferencia_perdida:,.2f}."
                )

            else:
                st.warning(
                    "No se encontró Forecast Comercial 2025 para este SKU. "
                    "Se muestran solo los modelos propuestos."
                )
