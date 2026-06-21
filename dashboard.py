import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit_authenticator as stauth
import os, datetime, io, re, requests # <-- CORRECCIÓN: Librería requests reincorporada con éxito aquí
import numpy as np

# Configuración de página obligatoria en la primera línea de ejecución
st.set_page_config(page_title="Dashboard Planta", layout="wide")

# --- 1. ESTILOS CORPORATIVOS PREMIUM DE BRUSELAS (TEXTO VISIBLE BLANCO/DORADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #FAF8F5 !important; font-family: sans-serif !important; }
    section[data-testid="stSidebar"] { background-color: #111B24 !important; min-width: 270px !important; }
    section[data-testid="stSidebar"] h2 { color: #E6C280 !important; font-family: serif !important; letter-spacing: 2px !important; text-align: center !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { color: #FFFFFF !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label p { color: #FFFFFF !important; font-size: 0.95rem !important; font-weight: 600 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] label p { color: #E6C280 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label { background-color: transparent !important; padding: 12px 15px !important; display: flex; border-left: 4px solid transparent !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover, div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] label { background-color: #1B2A36 !important; border-left: 4px solid #E6C280 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-testid="stWidgetMarkdownInsideLabel"]::before { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] { display: none !important; }
    div[data-testid="stMetric"] { background-color: #FFFFFF !important; border: 1px solid #EAE6DF !important; border-top: 4px solid #C29B68 !important; border-radius: 12px !important; padding: 20px 15px !important; }
    div[data-testid="stMetricLabel"] p { font-size: 0.75rem !important; text-transform: uppercase !important; color: #8C857B !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] div { font-size: 1.9rem !important; font-weight: 700 !important; color: #1A365D !important; }
    .sidebar-bottom-container { position: fixed; bottom: 20px; width: 230px; background-color: #111B24; padding-top: 10px; border-top: 1px solid #1B2A36; z-index: 999; }
    .sidebar-bottom-container button, section[data-testid="stSidebar"] button { background-color: #1B2A36 !important; color: #E6C280 !important; border: 1px solid #E6C280 !important; width: 100% !important; font-weight: 700 !important; }
    .sidebar-bottom-container button:hover, section[data-testid="stSidebar"] button:hover { background-color: #E6C280 !important; color: #111B24 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE AUTENTICACIÓN NATIVO ---
if "sesion_activa" not in st.session_state:
    st.session_state["sesion_activa"] = False

if not st.session_state["sesion_activa"]:
    st.markdown("<br><br><h2 style='text-align: center; color: #1A365D;'>🔒 ERP Gerencial Planta - Inicio de Sesión</h2>", unsafe_allow_html=True)
    c_izq, c_cen, c_der = st.columns(3) # CORREGIDO: columns(3) evita errores de ejecución
    with c_cen:
        st.write("Introduce las credenciales para desbloquear los paneles del sistema:")
        usuario_inp = st.text_input("Usuario (admin o gerente):")
        clave_inp = st.text_input("Contraseña:", type="password")
        btn_entrar = st.button("Ingresar al Sistema ERP", use_container_width=True)
        if btn_entrar:
            if (usuario_inp == "admin" and clave_inp == "Password123") or (usuario_inp == "gerente" and clave_inp == "Planta2026"):
                st.session_state["sesion_activa"] = True
                st.session_state["usuario_actual"] = "Administrador" if usuario_inp == "admin" else "Gerente General"
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas. Intenta de nuevo.")
    st.stop()

# --- 3. CUERPO GENERAL Y MOTOR DE CARGA ---
st.sidebar.markdown("<h2 style='margin-top:-10px;'>PLANTA</h2><p style='text-align:center; color:#E6C280; font-size:0.75rem; letter-spacing:3px; margin-top:-10px; margin-bottom:25px;'>MANAGEMENT ERP</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state['usuario_actual']}")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

@st.cache_data
def cargar_datos_sistema():
    if os.path.exists("planta_historico.parquet"):
        try: return pd.read_parquet("planta_historico.parquet")
        except: pass
    if os.path.exists("DespBoard.txt"):
        try:
            df = pd.read_csv("DespBoard.txt", sep="\t", encoding="latin1")
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
            df['AÑO'] = pd.to_numeric(df['AÑO'], errors='coerce').fillna(0).astype(int)
            df['DIA'] = pd.to_numeric(df['DIA'], errors='coerce').fillna(0).astype(int)
            df['NODIA'] = pd.to_numeric(df['NODIA'], errors='coerce').fillna(0).astype(int)
            if 'DOCUMENTO' in df.columns: df['DOCUMENTO'] = df['DOCUMENTO'].astype(str).str.strip()
            for col in ['NOMBRE TIENDA', 'MES', 'FAMILIA', 'GRUPO', 'DESCRIPCION']:
                if col in df.columns: df[col] = df[col].astype(str).fillna("No Especificado").str.strip()
            for col in ['VALOR-ENVIADO', 'COSTO', 'VALOR', 'CANTIDAD-ENV', 'CANTIDAD-REQ']:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df['RETORNO-NETO'] = df['VALOR-ENVIADO'] - df['COSTO']
            return df
        except: pass
    return pd.DataFrame()

df = cargar_datos_sistema()

if df.empty:
    opcion_menu = "📥 Actualizar e Internet (GitHub)"
    st.sidebar.warning("⚠️ Base de datos vacía")
else:
    opcion_menu = st.sidebar.radio("MENÚ PRINCIPAL:", [
        "📊 Resumen Ceo Diario", "📈 Resumen Ceo & Proyecciones", 
        "💰 Top Margen Real", "🏪 Por Tienda & Dias", "💳 Cobros", "📥 Actualizar e Internet (GitHub)"
    ])

st.sidebar.markdown('<div class="sidebar-bottom-container">', unsafe_allow_html=True)
if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state["sesion_activa"] = False
    st.rerun()
st.sidebar.markdown('</div>', unsafe_allow_html=True)

orden_meses = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

# fin caja 1

# ==========================================
# LÓGICA DE FILTRADO Y REPORTE DIARIO
# ==========================================
def obtener_filtros(key_pref):
    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    lista_meses = ["Todos los meses"] + sorted([str(x) for x in df['MES'].unique() if pd.notna(x)], key=lambda m: orden_meses.get(m.upper(), 99))
    lista_familias = ["Todas las familias"] + sorted([str(x) for x in df['FAMILIA'].unique() if pd.notna(x)])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: t = st.selectbox("Tienda", options=lista_tiendas, key=f"t_{key_pref}")
    with c2: a = st.selectbox("Año", options=lista_anos, index=lista_anos.index(str(pd.Timestamp.now().year)) if str(pd.Timestamp.now().year) in lista_anos else 0, key=f"a_{key_pref}")
    with c3: m = st.selectbox("Mes", options=lista_meses, index=lista_meses.index({1:'ENERO', 2:'FEBRERO', 3:'MARZO', 4:'ABRIL', 5:'MAYO', 6:'JUNIO', 7:'JULIO', 8:'AGOSTO', 9:'SEPTIEMBRE', 10:'OCTUBRE', 11:'NOVIEMBRE', 12:'DICIEMBRE'}.get(pd.Timestamp.now().month, 'ENERO')) if {1:'ENERO', 2:'FEBRERO', 3:'MARZO', 4:'ABRIL', 5:'MAYO', 6:'JUNIO', 7:'JULIO', 8:'AGOSTO', 9:'SEPTIEMBRE', 10:'OCTUBRE', 11:'NOVIEMBRE', 12:'DICIEMBRE'}.get(pd.Timestamp.now().month, 'ENERO') in lista_meses else 0, key=f"m_{key_pref}")
    with c4: f = st.selectbox("Familia", options=lista_familias, key=f"f_{key_pref}")
    
    sub_df = df.copy()
    if t != "Todas las tiendas": sub_df = sub_df[sub_df['NOMBRE TIENDA'] == t]
    if a != "Todos los años": sub_df = sub_df[sub_df['AÑO'] == int(a)]
    if m != "Todos los meses": sub_df = sub_df[sub_df['MES'] == m]
    if f != "Todas las familias": sub_df = sub_df[sub_df['FAMILIA'] == f]
    return sub_df

if opcion_menu == "📊 Resumen Ceo Diario" and not df.empty:
    st.title("📊 Resumen Ceo Diario")
    df_f = obtener_filtros("diario")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requerido", f"Q{df_f['VALOR'].sum():,.2f}")
    col2.metric("Total Enviado", f"Q{df_f['VALOR-ENVIADO'].sum():,.2f}")
    col3.metric("Fill Rate %", f"{(df_f['VALOR-ENVIADO'].sum() / df_f['VALOR'].sum() * 100 if df_f['VALOR'].sum() > 0 else 0):.2f}%")
    
    df_d = df_f.groupby('NODIA').agg({'VALOR-ENVIADO':'sum', 'VALOR':'sum'}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_d['NODIA'], y=df_d['VALOR-ENVIADO'], name="Enviado", marker_color='#1f77b4', hovertemplate="Q%{y:,.1s}"))
    fig.add_trace(go.Scatter(x=df_d['NODIA'], y=(df_d['VALOR-ENVIADO']/df_d['VALOR']*100).fillna(0), name="FR %", yaxis="y2", mode="lines+markers", line=dict(color="orange", width=3), hovertemplate="%{y:.1f}%"))
    fig.update_layout(yaxis=dict(title="Q", tickformat=",.1s"), yaxis2=dict(title="%", overlaying="y", side="right", tickformat=".1f"), legend=dict(x=0, y=1.1, orientation="h"), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    st.plotly_chart(px.pie(df_f.groupby('FAMILIA')['VALOR-ENVIADO'].sum().reset_index(), values='VALOR-ENVIADO', names='FAMILIA', hole=0.4, title="🍕 Por Familia"), use_container_width=True)
    
    df_t = df_f.groupby('NOMBRE TIENDA')['VALOR-ENVIADO'].sum().reset_index().sort_values(by='VALOR-ENVIADO')
    top = st.radio("Mostrar:", ["Top 10 Tiendas", "Top 20 Tiendas", "Todas"], index=1, horizontal=True)
    df_g = df_t.tail(10) if top == "Top 10 Tiendas" else (df_t.tail(20) if top == "Top 20 Tiendas" else df_t)
    fig_t = px.bar(df_g, x='VALOR-ENVIADO', y='NOMBRE TIENDA', orientation='h', color='VALOR-ENVIADO', color_continuous_scale='Blues', text_auto=',.1s', title="🏪 Por Tienda")
    fig_t.update_layout(xaxis=dict(tickformat=",.1s"), height=300+(len(df_g)*20), coloraxis_showscale=False)
    st.plotly_chart(fig_t, use_container_width=True)

    # fin parte 1 caja 2

# ==========================================
# MÓDULO: 📈 RESUMEN CEO & PROYECCIONES (CORREGIDO)
# ==========================================
if opcion_menu == "📈 Resumen Ceo & Proyecciones":
    st.markdown("<h2 style='color: #1A365D; font-family: serif;'>📈 Resumen Ceo & Modelos de Proyección</h2>", unsafe_allow_html=True)

    # --- 1. FUNCIÓN DE FORMATEO CORPORATIVO (Q, M, K) ---
    def formatear_quetzales(valor):
        if abs(valor) >= 1_000_000:
            return f"Q {valor / 1_000_000:.2f} M"
        elif abs(valor) >= 1_000:
            return f"Q {valor / 1_000:.2f} K"
        else:
            return f"Q {valor:,.2f}"

    # --- 2. CONFIGURACIÓN DE FILTROS POR DEFECTO ---
    fecha_actual = pd.Timestamp.now()
    ano_actual_str = str(fecha_actual.year)

    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    lista_meses = ["Todos los meses"] + sorted([str(x) for x in df['MES'].unique() if pd.notna(x)], key=lambda m: orden_meses.get(m.upper(), 99))

    c1, c2, c3 = st.columns(3)
    with c1: 
        t_sel = st.selectbox("Tienda Destino", options=lista_tiendas, key="p_tienda")
    with c2: 
        idx_ano = lista_anos.index(ano_actual_str) if ano_actual_str in lista_anos else 0
        a_sel = st.selectbox("Año Fiscal", options=lista_anos, index=idx_ano, key="p_ano")
    with c3: 
        # CORRECCIÓN: Por defecto ahora selecciona "Todos los meses"
        idx_mes = lista_meses.index("Todos los meses") if "Todos los meses" in lista_meses else 0
        m_sel = st.selectbox("Mes Operativo", options=lista_meses, index=idx_mes, key="p_mes")

    # Aplicación de filtros sobre el DataFrame
    df_proyecciones = df.copy()
    if t_sel != "Todas las tiendas": 
        df_proyecciones = df_proyecciones[df_proyecciones['NOMBRE TIENDA'] == t_sel]
    if a_sel != "Todos los años": 
        df_proyecciones = df_proyecciones[df_proyecciones['AÑO'] == int(a_sel)]
    if m_sel != "Todos los meses": 
        df_proyecciones = df_proyecciones[df_proyecciones['MES'] == m_sel]

    if df_proyecciones.empty:
        st.warning("⚠️ No se encontraron registros de planta para los filtros seleccionados.")
        st.stop()

    # --- 3. CÁLCULO DE MÉTRICAS Y PROYECCIÓN MENSUAL ---
    # Agrupamos por mes histórico
    df_mensual = df_proyecciones.groupby('MES')['VALOR-ENVIADO'].sum().reset_index()
    df_mensual['ORDEN'] = df_mensual['MES'].str.upper().map(orden_meses)
    df_mensual = df_mensual.sort_values(by='ORDEN').reset_index(drop=True)
    
    monto_total_periodo = df_mensual['VALOR-ENVIADO'].sum()
    promedio_mensual = df_mensual['VALOR-ENVIADO'].mean() if not df_mensual.empty else 0
    
    # Determinar el último mes registrado para proyectar el siguiente
    if not df_mensual.empty:
        ultimo_mes_nombre = df_mensual.iloc[-1]['MES']
        ultimo_idx = orden_meses.get(ultimo_mes_nombre.upper(), 6)
        idx_siguiente = (ultimo_idx % 12) + 1
        mes_siguiente_nombre = [k for k, v in orden_meses.items() if v == idx_siguiente][0]
        
        monto_ultimo_mes = df_mensual.iloc[-1]['VALOR-ENVIADO']
        # Proyección del mes siguiente aplicando crecimiento inercial (+5%)
        monto_proyectado_mes_siguiente = monto_ultimo_mes * 1.05
    else:
        mes_siguiente_nombre = "SIGUIENTE"
        monto_ultimo_mes = 0
        monto_proyectado_mes_siguiente = 0

    # --- 4. FILA DE TARJETAS EJECUTIVAS PREMIUM (CON FORMATO Q, M, K) ---
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(
            label=f"Acumulado Real Seleccionado", 
            value=formatear_quetzales(monto_total_periodo), 
            delta=f"{df_mensual['MES'].nunique()} meses evaluados"
        )
    with k2:
        st.metric(
            label=f"Cierre Último Mes ({ultimo_mes_nombre if 'ultimo_mes_nombre' in locals() else 'N/A'})", 
            value=formatear_quetzales(monto_ultimo_mes), 
            delta=f"Promedio mensual: {formatear_quetzales(promedio_mensual)}",
            delta_color="normal"
        )
    with k3:
        st.metric(
            label=f"🔮 Proyección Objetivo ({mes_siguiente_nombre})", 
            value=formatear_quetzales(monto_proyectado_mes_siguiente), 
            delta="Objetivo de crecimiento: +5.0% vs Cierre",
            delta_color="inverse"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. 📈 GRÁFICA DE TENDENCIA MENSUAL CON PROYECCIÓN ---
    st.markdown(f"### 📊 Tendencia Histórica Mensual y Proyección {mes_siguiente_nombre}")
    
    # Construcción de la matriz de datos para el gráfico
    meses_grafica = df_mensual['MES'].tolist()
    valores_reales = df_mensual['VALOR-ENVIADO'].tolist()
    
    # Añadimos el mes siguiente a la línea de tiempo de la gráfica
    meses_totales = meses_grafica + [mes_siguiente_nombre]
    
    fig_proyecciones = go.Figure()

    # Histórico real
    fig_proyecciones.add_trace(go.Scatter(
        x=meses_grafica, 
        y=valores_reales,
        mode='lines+markers', 
        name='Histórico Real',
        line=dict(color='#1A365D', width=4),
        hovertemplate='Mes: %{x}<br>Real: Q %{y:,.2f}'
    ))

    # Proyección intermensual (conecta el último punto real con la meta del mes siguiente)
    x_proy = [meses_grafica[-1], mes_siguiente_nombre] if len(meses_grafica) > 0 else [mes_siguiente_nombre]
    y_proy = [valores_reales[-1], monto_proyectado_mes_siguiente] if len(valores_reales) > 0 else [monto_proyectado_mes_siguiente]
    
    fig_proyecciones.add_trace(go.Scatter(
        x=x_proy, 
        y=y_proy,
        mode='lines+markers', 
        name=f'🔮 Proyección {mes_siguiente_nombre}',
        line=dict(color='#C29B68', width=3, dash='dash'),
        marker=dict(size=10, symbol='diamond'),
        hovertemplate='Mes: %{x}<br>Proyección: Q %{y:,.2f}'
    ))

    # Estilos del layout gráfico
    fig_proyecciones.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Meses del Ejercicio", gridcolor='#EAE6DF'),
        yaxis=dict(title="Monto Facturado (Q)", gridcolor='#EAE6DF')
    )
    
    st.plotly_chart(fig_proyecciones, use_container_width=True)

    # fin caja 2 parte 2


# ==========================================
# MÓDULO: 💰 TOP MARGEN REAL (ACTUALIZADO)
# ==========================================
if opcion_menu == "💰 Top Margen Real":
    st.markdown("<h2 style='color: #1A365D; font-family: serif;'>💰 Análisis de Rentabilidad y Top Margen Real</h2>", unsafe_allow_html=True)

    # --- 1. FUNCIÓN DE FORMATEO CORPORATIVO (Q, M, K) ---
    def formatear_quetzales(valor):
        if abs(valor) >= 1_000_000:
            return f"Q {valor / 1_000_000:.2f} M"
        elif abs(valor) >= 1_000:
            return f"Q {valor / 1_000:.2f} K"
        else:
            return f"Q {valor:,.2f}"

    # --- 2. CONFIGURACIÓN DE FILTROS CORPORATIVOS ---
    fecha_actual = pd.Timestamp.now()
    ano_actual_str = str(fecha_actual.year)

    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    lista_meses = ["Todos los meses"] + sorted([str(x) for x in df['MES'].unique() if pd.notna(x)], key=lambda m: orden_meses.get(m.upper(), 99))

    c1, c2, c3 = st.columns(3)
    with c1: 
        t_sel = st.selectbox("Tienda Destino", options=lista_tiendas, key="m_tienda")
    with c2: 
        idx_ano = lista_anos.index(ano_actual_str) if ano_actual_str in lista_anos else 0
        a_sel = st.selectbox("Año Fiscal", options=lista_anos, index=idx_ano, key="m_ano")
    with c3: 
        idx_mes = lista_meses.index("Todos los meses") if "Todos los meses" in lista_meses else 0
        m_sel = st.selectbox("Mes Operativo", options=lista_meses, index=idx_mes, key="m_mes")

    # Aplicación de filtros
    df_margen = df.copy()
    if t_sel != "Todas las tiendas": 
        df_margen = df_margen[df_margen['NOMBRE TIENDA'] == t_sel]
    if a_sel != "Todos los años": 
        df_margen = df_margen[df_margen['AÑO'] == int(a_sel)]
    if m_sel != "Todos los meses": 
        df_margen = df_margen[df_margen['MES'] == m_sel]

    if df_margen.empty:
        st.warning("⚠️ No se encontraron registros de rentabilidad para los filtros seleccionados.")
        st.stop()

    # --- 3. CÁLCULOS MACRO ---
    enviado_total = df_margen['VALOR-ENVIADO'].sum()
    costo_total = df_margen['COSTO'].sum()
    margen_neto_total = df_margen['RETORNO-NETO'].sum()
    porcentaje_margen_global = (margen_neto_total / enviado_total * 100) if enviado_total > 0 else 0

    # --- 4. TARJETAS EJECUTIVAS BRUSELAS STYLE ---
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(label="Monto Total Enviado", value=formatear_quetzales(enviado_total), delta="Ingreso Bruto de Planta")
    with k2:
        st.metric(label="Costo de Producción Total", value=formatear_quetzales(costo_total), delta=f"Ratio de Costo: {(costo_total / enviado_total * 100) if enviado_total > 0 else 0:.1f}%", delta_color="inverse")
    with k3:
        st.metric(label="Margen Real Obtenido", value=formatear_quetzales(margen_neto_total), delta=f"Eficiencia: {porcentaje_margen_global:.1f}% del enviado", delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. FILA SUPERIOR DE GRÁFICOS: FAMILIAS Y GRUPOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### 🏆 Top 10 Familias por Margen Neto (Q)")
        df_fam_margen = df_margen.groupby('FAMILIA')['RETORNO-NETO'].sum().reset_index()
        df_fam_margen = df_fam_margen.sort_values(by='RETORNO-NETO', ascending=True).tail(10)
        
        fig_fam = px.bar(
            df_fam_margen, x='RETORNO-NETO', y='FAMILIA', orientation='h',
            color_discrete_sequence=['#1A365D'],
            labels={'RETORNO-NETO': 'Margen Neto (Q)', 'FAMILIA': 'Familia'}
        )
        fig_fam.update_traces(marker_line_color='#C29B68', marker_line_width=1, hovertemplate='Familia: %{y}<br>Margen: Q %{x:,.2f}')
        fig_fam.update_layout(margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(gridcolor='#EAE6DF'))
        st.plotly_chart(fig_fam, use_container_width=True)

    with g2:
        st.markdown("### 📉 Distribución de Rentabilidad Operativa por Grupo")
        df_grupo_margen = df_margen.groupby('GRUPO').agg({'VALOR-ENVIADO': 'sum', 'RETORNO-NETO': 'sum'}).reset_index()
        df_grupo_margen = df_grupo_margen.sort_values(by='RETORNO-NETO', ascending=False).head(15)

        fig_scat = go.Figure()
        fig_scat.add_trace(go.Bar(x=df_grupo_margen['GRUPO'], y=df_grupo_margen['VALOR-ENVIADO'], name='Valor Enviado', marker_color='#1A365D'))
        fig_scat.add_trace(go.Bar(x=df_grupo_margen['GRUPO'], y=df_grupo_margen['RETORNO-NETO'], name='Margen Real', marker_color='#C29B68'))
        fig_scat.update_layout(
            barmode='group', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#EAE6DF'), xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig_scat, use_container_width=True)

    # --- 6. FILA INFERIOR NUEVA: GRÁFICO DE TIENDAS CON SELECTOR DE RANGO DENTRO DE LA PÁGINA ---
    st.markdown("<hr style='border: 0.5px solid #EAE6DF;'>", unsafe_allow_html=True)
    
    # Encabezado con el selector dinámico al lado usando columnas
    c_tit, c_opt = st.columns([2, 1])
    with c_tit:
        st.markdown("### 🏪 Rendimiento de Margen Neto por Tienda Destino")
    with c_opt:
        top_tiendas_opcion = st.selectbox(
            "Visualizar rango:",
            options=["Top 10 mejores", "Top 20 mejores", "Todas las tiendas"],
            index=0,
            key="opt_top_tiendas"
        )

    # Procesamiento dinámico del Top de Tiendas según la opción elegida
    df_tiendas_margen = df_margen.groupby('NOMBRE TIENDA')['RETORNO-NETO'].sum().reset_index()
    
    if top_tiendas_opcion == "Top 10 mejores":
        df_tiendas_margen = df_tiendas_margen.sort_values(by='RETORNO-NETO', ascending=True).tail(10)
    elif top_tiendas_opcion == "Top 20 mejores":
        df_tiendas_margen = df_tiendas_margen.sort_values(by='RETORNO-NETO', ascending=True).tail(20)
    else: # Todas las tiendas
        df_tiendas_margen = df_tiendas_margen.sort_values(by='RETORNO-NETO', ascending=True)

    fig_tiendas = px.bar(
        df_tiendas_margen, x='RETORNO-NETO', y='NOMBRE TIENDA', orientation='h',
        color_discrete_sequence=['#C29B68'], # Dorado elegante para diferenciarlo de familias
        labels={'RETORNO-NETO': 'Margen Neto (Q)', 'NOMBRE TIENDA': 'Tienda'}
    )
    fig_tiendas.update_traces(marker_line_color='#1A365D', marker_line_width=1, hovertemplate='Tienda: %{y}<br>Margen: Q %{x:,.2f}')
    fig_tiendas.update_layout(
        margin=dict(l=20, r=20, t=10, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='#EAE6DF'), yaxis=dict(dtick=1)
    )
    st.plotly_chart(fig_tiendas, use_container_width=True)

    # --- 7. TABLA AUDITORÍA SKUS INFERIOR ---
    st.markdown("### 🔍 Auditoría de Margen Real por Descripción de Producto")
    df_sku = df_margen.groupby(['FAMILIA', 'DESCRIPCION']).agg({
        'CANTIDAD-ENV': 'sum', 'VALOR-ENVIADO': 'sum', 'COSTO': 'sum', 'RETORNO-NETO': 'sum'
    }).reset_index()
    df_sku['% Margen'] = (df_sku['RETORNO-NETO'] / df_sku['VALOR-ENVIADO'] * 100).fillna(0)
    df_sku = df_sku.sort_values(by='RETORNO-NETO', ascending=False).reset_index(drop=True)

    st.dataframe(
        df_sku.style.format({
            'CANTIDAD-ENV': '{:,.0f}', 'VALOR-ENVIADO': 'Q {:,.2f}', 'COSTO': 'Q {:,.2f}', 'RETORNO-NETO': 'Q {:,.2f}', '% Margen': '{:.1f}%'
        }),
        use_container_width=True, hide_index=True
    )

# ==========================================
# MÓDULO: 🏪 POR TIENDA & DIAS
# ==========================================
if opcion_menu == "🏪 Por Tienda & Dias":
    st.markdown("<h2 style='color: #1A365D; font-family: serif;'>🏪 Análisis Operativo por Tiendas y Días de Despacho</h2>", unsafe_allow_html=True)

    # --- 1. FUNCIÓN DE FORMATEO CORPORATIVO (Q, M, K) ---
    def formatear_quetzales(valor):
        if abs(valor) >= 1_000_000:
            return f"Q {valor / 1_000_000:.2f} M"
        elif abs(valor) >= 1_000:
            return f"Q {valor / 1_000:.2f} K"
        else:
            return f"Q {valor:,.2f}"

    # --- 2. CONFIGURACIÓN DE FILTROS CORPORATIVOS ---
    fecha_actual = pd.Timestamp.now()
    ano_actual_str = str(fecha_actual.year)

    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    lista_meses = ["Todos los meses"] + sorted([str(x) for x in df['MES'].unique() if pd.notna(x)], key=lambda m: orden_meses.get(m.upper(), 99))

    c1, c2, c3 = st.columns(3)
    with c1: 
        t_sel = st.selectbox("Tienda Destino", options=lista_tiendas, key="td_tienda")
    with c2: 
        idx_ano = lista_anos.index(ano_actual_str) if ano_actual_str in lista_anos else 0
        a_sel = st.selectbox("Año Fiscal", options=lista_anos, index=idx_ano, key="td_ano")
    with c3: 
        idx_mes = lista_meses.index("Todos los meses") if "Todos los meses" in lista_meses else 0
        m_sel = st.selectbox("Mes Operativo", options=lista_meses, index=idx_mes, key="td_mes")

    # Aplicación de filtros
    df_td = df.copy()
    if t_sel != "Todas las tiendas": 
        df_td = df_td[df_td['NOMBRE TIENDA'] == t_sel]
    if a_sel != "Todos los años": 
        df_td = df_td[df_td['AÑO'] == int(a_sel)]
    if m_sel != "Todos los meses": 
        df_td = df_td[df_td['MES'] == m_sel]

    if df_td.empty:
        st.warning("⚠️ No se encontraron registros para los filtros seleccionados.")
        st.stop()

    # --- 3. PROCESAMIENTO DE DÍAS DE LA SEMANA ---
    # Convertimos la columna FECHA para extraer el día de la semana si no viene calculado
    if 'FECHA' in df_td.columns:
        df_td['FECHA_DT'] = pd.to_datetime(df_td['FECHA'], errors='coerce')
        # Diccionario para mapear el nombre del día en español
        dias_semana_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        df_td['DIA_SEMANA'] = df_td['FECHA_DT'].dt.dayofweek.map(dias_semana_map)
    else:
        df_td['DIA_SEMANA'] = "No Especificado"

    # Orden lógico para la visualización semanal
    orden_dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    # --- 4. GRÁFICOS DE ALTA DENSIDAD OPERATIVA ---
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### 📅 Volumen de Envío por Día de la Semana")
        df_semana = df_td.groupby('DIA_SEMANA')['VALOR-ENVIADO'].sum().reset_index()
        
        # Reordenar de lunes a domingo de forma segura
        df_semana['DIA_SEMANA'] = pd.Categorical(df_semana['DIA_SEMANA'], categories=orden_dias_semana, ordered=True)
        df_semana = df_semana.sort_values('DIA_SEMANA')

        fig_sem = px.bar(
            df_semana, x='DIA_SEMANA', y='VALOR-ENVIADO',
            color_discrete_sequence=['#1A365D'],
            labels={'VALOR-ENVIADO': 'Total Enviado (Q)', 'DIA_SEMANA': 'Día de la Semana'}
        )
        fig_sem.update_traces(marker_line_color='#C29B68', marker_line_width=1, hovertemplate='%{x}<br>Enviado: Q %{y:,.2f}')
        fig_sem.update_layout(margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(gridcolor='#EAE6DF'))
        st.plotly_chart(fig_sem, use_container_width=True)

    with g2:
        st.markdown("### 📊 Comportamiento de Envíos a lo largo del Mes")
        
        # Clonamos el DataFrame filtrado para evitar advertencias de copia
        df_dia_calculado = df_td.copy()
        
        # Forzar que la columna FECHA sea de tipo datetime de forma correcta
        df_dia_calculado['FECHA_DT'] = pd.to_datetime(df_dia_calculado['FECHA'], errors='coerce')
        
        # REPARACIÓN: Extraemos el día real (1 al 31) directamente de la fecha válida
        df_dia_calculado['DIA_REAL'] = df_dia_calculado['FECHA_DT'].dt.day
        
        # Eliminamos cualquier registro que no tenga una fecha válida transaccional
        df_dia_calculado = df_dia_calculado[df_dia_calculado['DIA_REAL'].notna() & (df_dia_calculado['DIA_REAL'] > 0)]
        
        if not df_dia_calculado.empty:
            # Agrupación por el día real calculado por el sistema
            df_dia_mes = df_dia_calculado.groupby('DIA_REAL')['VALOR-ENVIADO'].sum().reset_index()
            df_dia_mes = df_dia_mes.sort_values(by='DIA_REAL')
            
            fig_dia_mes = go.Figure()
            fig_dia_mes.add_trace(go.Scatter(
                x=df_dia_mes['DIA_REAL'], 
                y=df_dia_mes['VALOR-ENVIADO'],
                mode='lines+markers', 
                name='Monto Despachado',
                line=dict(color='#C29B68', width=3),
                marker=dict(size=6, color='#1A365D'),
                hovertemplate='Día %{x}<br>Enviado: Q %{y:,.2f}'
            ))
            
            # Ajustes visuales premium del eje de tiempo
            fig_dia_mes.update_layout(
                margin=dict(l=20, r=20, t=20, b=20), 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title="Día del Mes", 
                    tickmode='linear', 
                    dtick=2,             # Muestra marcas en el eje cada 2 días
                    range=[1, 31],       # Obliga a mostrar la escala completa del mes
                    gridcolor='#EAE6DF'
                ),
                yaxis=dict(title="Monto (Q)", gridcolor='#EAE6DF'),
                hovermode="x unified"
            )
            st.plotly_chart(fig_dia_mes, use_container_width=True)
        else:
            st.info("ℹ️ Los registros seleccionados no contienen una columna de FECHA válida para graficar.")



   # --- 5. MATRIZ DE CALOR / ANALÍTICA INTERNA REPARADA (DIAS 1-31) ---
    st.markdown("### 🗺️ Matriz de Distribución Logística: Tiendas vs Días del Mes (Top 15 Tiendas)")
    
    # Clonamos el DataFrame filtrado para realizar la corrección de días sin alertas de copia
    df_pivot_rep = df_td.copy()
    
    # Aseguramos el tipado datetime y extraemos el día transaccional real de la fecha
    df_pivot_rep['FECHA_DT'] = pd.to_datetime(df_pivot_rep['FECHA'], errors='coerce')
    df_pivot_rep['DIA_REAL'] = df_pivot_rep['FECHA_DT'].dt.day
    
    # Filtramos para conservar únicamente los registros que tengan fechas válidas
    df_pivot_rep = df_pivot_rep[df_pivot_rep['DIA_REAL'].notna() & (df_pivot_rep['DIA_REAL'] > 0)]
    
    if not df_pivot_rep.empty:
        # Filtrar por las top 15 tiendas con mayor volumen enviado para el orden visual
        top_15_tiendas = df_pivot_rep.groupby('NOMBRE TIENDA')['VALOR-ENVIADO'].sum().nlargest(15).index
        df_pivot_data = df_pivot_rep[df_pivot_rep['NOMBRE TIENDA'].isin(top_15_tiendas)]
        
        # Crear la tabla pivote utilizando la columna corregida 'DIA_REAL'
        df_pivot = df_pivot_data.pivot_table(
            values='VALOR-ENVIADO', 
            index='NOMBRE TIENDA', 
            columns='DIA_REAL', 
            aggfunc='sum'
        ).fillna(0)
        
        # Renderizado premium con mapa de calor integrado (Matplotlib requerido en requirements.txt)
        
        # --- FUNCIÓN DE FORMATEO COMPACTO PARA LA MATRIZ ---
        def formato_matriz(valor):
            if valor == 0:
                return "-"  # Limpia la vista para días sin despachos
            elif abs(valor) >= 1_000_000:
                return f"{valor / 1_000_000:.1f}M"
            elif abs(valor) >= 1_000:
                return f"{valor / 1_000:.0f}K"
            else:
                return f"{valor:.0f}"

        # Renderizado premium con formato de texto compacto y mapa de calor
        st.dataframe(
            df_pivot.style.background_gradient(cmap='Blues').format(formato_matriz),
            use_container_width=True
        )
        
        st.caption("💡 Los valores de la matriz representan los montos totales enviados consolidados. Las columnas del 1 al 31 muestran la distribución real por día del mes.")
    else:
        st.info("ℹ️ No hay datos de fechas válidas disponibles para estructurar la matriz mensual.")


    


    # ==========================================
# CALENDARIOS, COBROS Y PANEL DE CONTROL HÍBRIDO
# ==========================================
elif opcion_menu == "🏪 Por Tienda & Dias" and not df.empty:
    st.title("🏪 Rendimiento Por Tienda & Días")
    df_f = obtener_filtros("td")
    st.subheader("📅 Distribución de Valor Enviado por Tienda y Día del Mes")
    df_pivot = df_f.pivot_table(index='NOMBRE TIENDA', columns='NODIA', values='VALOR-ENVIADO', aggfunc='sum').fillna(0)
    fig_hm = px.imshow(df_pivot, labels=dict(x="Día del Mes", y="Tienda", color="Monto (Q)"), x=df_pivot.columns, y=df_pivot.index, color_continuous_scale='Blues')
    fig_hm.update_layout(height=600)
    st.plotly_chart(fig_hm, use_container_width=True)

elif opcion_menu == "💳 Cobros" and not df.empty:
    st.title("💳 Cobros")
    st.info("Próximamente: Gráfica comparativa de Facturado vs Cobro.")

elif opcion_menu == "📥 Actualizar e Internet (GitHub)":
    st.markdown("## 📥 Panel de Control de Carga Híbrido")
    est_txt = "No hay sincronizaciones previas registradas."
    if os.path.exists("planta_auditoria.txt"):
        try:
            with open("planta_auditoria.txt", "r", encoding="utf-8") as f: est_txt = f.read()
        except: pass
    st.info(f"📋 **Estatus del ERP:** {est_txt}")
    
    col_m, col_n = st.columns(2)
    with col_m:
        st.markdown("### 💻 Carga manual desde PC")
        arch_sub = st.file_uploader("Upload", type=["txt"])
        if arch_sub is not None:
            try:
                df_txt = pd.read_csv(arch_sub, sep="\t", encoding="latin1")
                df_txt['FECHA'] = pd.to_datetime(df_txt['FECHA'], errors='coerce')
                if 'DOCUMENTO' in df_txt.columns: df_txt['DOCUMENTO'] = df_txt['DOCUMENTO'].astype(str).str.strip()
                for c in ['AÑO', 'DIA', 'NODIA']:
                    if c in df_txt.columns: df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').fillna(0).astype(int)
                for c in ['NOMBRE TIENDA', 'MES', 'FAMILIA', 'GRUPO', 'DESCRIPCION']:
                    if c in df_txt.columns: df_txt[c] = df_txt[c].astype(str).fillna("No Especificado").str.strip()
                for c in ['VALOR-ENVIADO', 'COSTO', 'VALOR', 'CANTIDAD-ENV', 'CANTIDAD-REQ']:
                    if c in df_txt.columns: df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').fillna(0)
                df_txt['RETORNO-NETO'] = df_txt['VALOR-ENVIADO'] - df_txt['COSTO']
                df_txt.to_parquet("planta_historico.parquet", index=False)
                f_str = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                msg = f"Última sincronización exitosa el {f_str} usando el origen '{arch_sub.name}'."
                with open("planta_auditoria.txt", "w", encoding="utf-8") as f: f.write(msg)
                st.success("✅ Archivo convertido a Parquet y auditoría registrada localmente. ¡Dale F5!")
                st.balloons()
            except Exception as ex: st.error(f"Error en estructura: {ex}")
    
    with col_n: # Usamos col_n que es la columna de tu layout de planta
        st.markdown("### ☁️ Inyección local y Envío a GitHub")
    if st.button("🔄 Procesar DespBoard y Subir a GitHub", type="primary", use_container_width=True):
        with st.spinner("Sincronizando matriz de datos interna de forma automática..."):
            try:
                # 1. Definir los nombres de archivos para el proyecto de Planta
                archivo_maestro_local = "DespBoard.txt"
                archivo_historico_parquet = "planta_historico.parquet"
                archivo_auditoria = "planta_auditoria.txt"
                
                # Si no está en la raíz, lo busca en la carpeta descargas del usuario de Windows
                if not os.path.exists(archivo_maestro_local):
                    ruta_usuario_win = os.path.expanduser("~")
                    archivo_maestro_local = os.path.join(ruta_usuario_win, "Downloads", "DespBoard.txt")
                
                if os.path.exists(archivo_maestro_local):
                    # 2. Cargar el archivo de texto plano tabulado
                    df_nuevo = pd.read_csv(archivo_maestro_local, sep="\t", encoding='latin1', low_memory=False, on_bad_lines='skip')
                    
                    # 3. Homologación y tipado de datos estricto de Planta (idéntico a tu motor de carga)
                    df_nuevo['FECHA'] = pd.to_datetime(df_nuevo['FECHA'], errors='coerce')
                    df_nuevo['AÑO'] = pd.to_numeric(df_nuevo['AÑO'], errors='coerce').fillna(0).astype(int)
                    df_nuevo['DIA'] = pd.to_numeric(df_nuevo['DIA'], errors='coerce').fillna(0).astype(int)
                    df_nuevo['NODIA'] = pd.to_numeric(df_nuevo['NODIA'], errors='coerce').fillna(0).astype(int)
                    
                    if 'DOCUMENTO' in df_nuevo.columns: 
                        df_nuevo['DOCUMENTO'] = df_nuevo['DOCUMENTO'].astype(str).str.strip()
                    
                    for col in ['NOMBRE TIENDA', 'MES', 'FAMILIA', 'GRUPO', 'DESCRIPCION']:
                        if col in df_nuevo.columns: 
                            df_nuevo[col] = df_nuevo[col].astype(str).fillna("No Especificado").str.strip()
                    
                    for col in ['VALOR-ENVIADO', 'COSTO', 'VALOR', 'CANTIDAD-ENV', 'CANTIDAD-REQ']:
                        if col in df_nuevo.columns: 
                            df_nuevo[col] = pd.to_numeric(df_nuevo[col], errors='coerce').fillna(0)
                    
                    df_nuevo['RETORNO-NETO'] = df_nuevo['VALOR-ENVIADO'] - df_nuevo['COSTO']
                    
                    # 4. Guardar localmente en formato Parquet optimizado
                    df_nuevo.to_parquet(archivo_historico_parquet, index=False)
                    
                    # Crear archivo de auditoría local
                    f_str = pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')
                    msg = f"Sincronización en la Nube exitosa el {f_str} desde GitHub Principal."
                    with open(archivo_auditoria, "w", encoding="utf-8") as f: 
                        f.write(msg)
                    
                    st.success(f"¡Matriz '{archivo_maestro_local}' procesada con éxito ({len(df_nuevo):,} filas)!")
                    
                    # 5. --- MOTOR DE AUTOMATIZACIÓN DE GITHUB EN LÍNEA ---
                    import subprocess
                    st.info("🚀 Iniciando despliegue automático a GitHub...")
                    
                    # Comandos de Git adaptados a los archivos de Planta
                    comandos_git = [
                        ["git", "add", archivo_historico_parquet, archivo_auditoria],
                        ["git", "commit", "-m", f"Inyeccion automatica planta_historico.parquet - {f_str}"],
                        ["git", "push", "origin", "main"]
                    ]
                    
                    error_detectado = False
                    for cmd in comandos_git:
                        resultado = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                        if resultado.returncode != 0 and "nothing to commit" not in resultado.stderr.lower():
                            st.error(f"Error en comando {' '.join(cmd)}: {resultado.stderr}")
                            error_detectado = True
                            break
                    
                    if not error_detectado:
                        st.success("¡Repositorio de GitHub actualizado con la nueva base transaccional de Planta!")
                    
                    # Limpiar caché de la app para que lea inmediatamente el nuevo Parquet
                    st.cache_data.clear()
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ No se detectó el archivo 'DespBoard.txt' en la carpeta del script ni en Descargas.")
            except Exception as e: 
                st.error(f"Error en la operación: {str(e)}")

















            


