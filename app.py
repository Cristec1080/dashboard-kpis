%%writefile app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard Amigable 📊",
    page_icon="📈",
    layout="wide"
)

# --- Título Principal ---
st.title("Dashboard Interactivo 📊")
st.write("Sube tu archivo Excel o CSV en la barra lateral para ver tus datos.")

# --- BARRA LATERAL (Sidebar) ---
st.sidebar.header("Configuración")
uploaded_file = st.sidebar.file_uploader(
    "Sube tu archivo (.xlsx o .csv)",
    type=["xlsx", "csv"]
)

# Si no hay archivo, mostrar mensaje de bienvenida
if uploaded_file is None:
    st.info("👋 ¡Bienvenido! Por favor, sube un archivo en la barra lateral izquierda para comenzar.")
    st.stop()

# Si hay archivo, leerlo
try:
    if uploaded_file.name.endswith('.csv'):
        df_original = pd.read_csv(uploaded_file)
    else:
        df_original = pd.read_excel(uploaded_file, engine='openpyxl')
except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
    st.stop()

# --- BARRA LATERAL: Buscador y Filtros ---
st.sidebar.header("🔍 Buscador y Filtros")

# 1. El Buscador
search_query = st.sidebar.text_input("Buscar en la tabla (cualquier palabra):")

# 2. Los Filtros Dinámicos
df_filtered = df_original.copy()

# Aplicar el buscador primero
if search_query:
    mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
    df_filtered = df_filtered[mask]

# Crear filtros automáticos para columnas de texto (categóricas)
categorical_cols = df_filtered.select_dtypes(include=['object', 'category']).columns.tolist()

for col in categorical_cols:
    if df_filtered[col].nunique() < 50 and df_filtered[col].nunique() > 1:
        options = df_filtered[col].unique().tolist()
        selected = st.sidebar.multiselect(f"Filtrar por {col}:", options, default=options)
        
        df_filtered = df_filtered[df_filtered[col].isin(selected)]


# --- PÁGINA PRINCIPAL: El Dashboard ---

st.header("Resumen Rápido (KPIs)")
st.write("Estos números cambian según tus filtros.")

# Identificar columnas numéricas y TODAS las columnas
numeric_cols = df_filtered.select_dtypes(include=['number']).columns.tolist()
all_cols = df_filtered.columns.tolist() # Lista de todas las columnas

# Crear 3 métricas (KPIs) en columnas
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

col_kpi1.metric("Filas Encontradas", f"{len(df_filtered)}")
col_kpi2.metric("Columnas Totales", f"{len(df_filtered.columns)}")

# KPI para sumar una columna numérica
if numeric_cols:
    col_to_sum = st.selectbox(
        "Elige una columna para sumar:",
        numeric_cols
    )
    suma_total = df_filtered[col_to_sum].sum()
    col_kpi3.metric(f"Suma de '{col_to_sum}'", f"{suma_total:,.2f}")
else:
    col_kpi3.info("No se encontraron columnas numéricas para sumar.")

st.markdown("---")

# --- Gráficos Interactivos ---
st.header("Gráficos Interactivos")
st.write("Estos gráficos también se actualizan con tus filtros.")

if not numeric_cols or not categorical_cols:
    st.warning("Necesitas al menos una columna de texto (categórica) y una columna numérica para mostrar los gráficos. Si solo tienes números, usa la opción 'Columna para sumar' de arriba.")
else:
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Gráfico de Barras")
        x_bar = st.selectbox("Eje X (Categoría):", categorical_cols, key='bar_x')
        y_bar = st.selectbox("Eje Y (Valor):", numeric_cols, key='bar_y')
        
        try:
            df_grouped = df_filtered.groupby(x_bar)[y_bar].sum().reset_index()
            fig_bar = px.bar(df_grouped, x=x_bar, y=y_bar, title=f"{y_bar} por {x_bar}")
            st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo crear el gráfico de barras: {e}")

    with col_graf2:
        st.subheader("Gráfico de Torta (Pie) 🥧")
        
        # CAMBIO CLAVE: Usamos all_cols para permitir cualquier columna en los nombres de las rebanadas
        col_pie_names = st.selectbox("Elige la columna para las Rebanadas (Nombres):", all_cols, key='pie_names')
        # Usamos numeric_cols para el tamaño
        col_pie_values = st.selectbox("Elige la columna para el Tamaño (Valor):", numeric_cols, key='pie_values')
        
        try:
            # Agrupar los datos y sumar para obtener el tamaño de cada rebanada
            df_pie_grouped = df_filtered.groupby(col_pie_names)[col_pie_values].sum().reset_index()

            fig_pie = px.pie(
                df_pie_grouped, 
                names=col_pie_names, 
                values=col_pie_values, 
                title=f"Distribución de {col_pie_values} por {col_pie_names}"
            )
            fig_pie.update_layout(height=600)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        except Exception as e:
            st.error(f"No se pudo crear el gráfico de torta. Error: {e}")
            st.warning("Asegúrate de que la columna de Valor sea numérica.")

st.markdown("---")

# --- Tabla de Datos ---
st.header("Tu Información (Filtrada)")
st.write(f"Mostrando {len(df_filtered)} filas de las {len(df_original)} originales.")
st.dataframe(df_filtered)