import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de página obligatoria en la primera línea
st.set_page_config(page_title="Dashboard Planta", layout="wide")

# --- 1. ESTILOS CORPORATIVOS PREMIUM (BOTÓN VISIBLE PERMANENTE) ---
st.markdown("""
    <style>
    .stApp { background-color: #FAF8F5 !important; font-family: sans-serif !important; }
    section[data-testid="stSidebar"] { background-color: #111B24 !important; min-width: 270px !important; }
    section[data-testid="stSidebar"] h2 { color: #E6C280 !important; font-family: serif !important; letter-spacing: 2px !important; text-align: center !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { color: #FFFFFF !important; }
    
    /* Menú lateral e indicadores de selección */
    div[data-testid="stRadio"] div[role="radiogroup"] label p { color: #FFFFFF !important; font-size: 0.95rem !important; font-weight: 600 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] label p { color: #E6C280 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label { background-color: transparent !important; padding: 12px 15px !important; display: flex !important; border-left: 4px solid transparent !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover, div[data-testid="stRadio"] div[role="radiogroup"] [data-checked="true"] label { background-color: #1B2A36 !important; border-left: 4px solid #E6C280 !important; }
    
    /* Tarjetas métricas KPI */
    div[data-testid="stMetric"] { background-color: #FFFFFF !important; border: 1px solid #EAE6DF !important; border-top: 4px solid #C29B68 !important; border-radius: 12px !important; padding: 20px 15px !important; }
    div[data-testid="stMetricLabel"] p { font-size: 0.75rem !important; text-transform: uppercase !important; color: #8C857B !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] div { font-size: 1.9rem !important; font-weight: 700 !important; color: #1A365D !important; }
    
    /* BLINDAJE DE CONTRASTE: Botón "Cerrar Sesión" 100% visible siempre con texto dorado */
    .sidebar-bottom-container { position: fixed; bottom: 20px; width: 230px; background-color: #111B24; padding-top: 10px; border-top: 1px solid #1B2A36; z-index: 999; }
    .sidebar-bottom-container button, section[data-testid="stSidebar"] button { 
        background-color: #1B2A36 !important; 
        color: #E6C280 !important; 
        border: 1px solid #E6C280 !important; 
        width: 100% !important; 
        font-weight: 700 !important; 
    }
    .sidebar-bottom-container button:hover, section[data-testid="stSidebar"] button:hover { 
        background-color: #E6C280 !important; 
        color: #111B24 !important; 
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICACIÓN NATIVO ---
if "sesion_activa" not in st.session_state:
    st.session_state["sesion_activa"] = False

if not st.session_state["sesion_activa"]:
    st.markdown("<br><br><h2 style='text-align: center; color: #1A365D;'>🔒 ERP Gerencial Planta - Inicio de Sesión</h2>", unsafe_allow_html=True)
    
    # CORRECCIÓN: Se agrega estrictamente el argumento (3) para evitar el TypeError
    c_izq, c_cen, c_der = st.columns(3)
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

    # fin caja 1


    # --- INICIO DEL CUERPO DEL ERP ---
st.sidebar.markdown("<h2 style='margin-top:-10px;'>PLANTA</h2><p style='text-align:center; color:#E6C280; font-size:0.75rem; letter-spacing:3px; margin-top:-10px; margin-bottom:25px;'>MANAGEMENT ERP</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state['usuario_actual']}")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

@st.cache_data
def cargar_datos_sistema():
    # 1. Intenta leer el Parquet generado por la web
    if os.path.exists("planta_historico.parquet"):
        try: return pd.read_parquet("planta_historico.parquet")
        except: pass
        
    # 2. Si la app acaba de encender y el parquet local no se ha registrado en caché, lee directo el TXT local
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

# Desbloqueo inteligente del menú basado en la existencia de datos locales o Parquet
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

if opcion_menu == "📊 Resumen Ceo Diario" and not df.empty:
    st.title("📊 Resumen Ceo Diario")
    ano_sistema = pd.Timestamp.now().year
    meses_espanol = {1:'ENERO', 2:'FEBRERO', 3:'MARZO', 4:'ABRIL', 5:'MAYO', 6:'JUNIO', 7:'JULIO', 8:'AGOSTO', 9:'SEPTIEMBRE', 10:'OCTUBRE', 11:'NOVIEMBRE', 12:'DICIEMBRE'}
    mes_sistema = meses_espanol.get(pd.Timestamp.now().month, 'ENERO')
    
    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    meses_unicos = [str(x) for x in df['MES'].unique() if pd.notna(x)]
    lista_meses = ["Todos los meses"] + sorted(meses_unicos, key=lambda m: orden_meses.get(m.upper(), 99))
    lista_familias = ["Todas las familias"] + sorted([str(x) for x in df['FAMILIA'].unique() if pd.notna(x)])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: s_tienda = st.selectbox("Tienda", options=lista_tiendas)
    with c2: s_ano = st.selectbox("Año", options=lista_anos, index=lista_anos.index(str(ano_sistema)) if str(ano_sistema) in lista_anos else 0)
    with c3: s_mes = st.selectbox("Mes", options=lista_meses, index=lista_meses.index(mes_sistema) if mes_sistema in lista_meses else 0)
    with c4: s_familia = st.selectbox("Familia", options=lista_familias)
        
    df_filtrado = df.copy()
    if s_tienda != "Todas las tiendas": df_filtrado = df_filtrado[df_filtrado['NOMBRE TIENDA'] == s_tienda]
    if s_ano != "Todos los años": df_filtrado = df_filtrado[df_filtrado['AÑO'] == int(s_ano)]
    if s_mes != "Todos los meses": df_filtrado = df_filtrado[df_filtrado['MES'] == s_mes]
    if s_familia != "Todas las familias": df_filtrado = df_filtrado[df_filtrado['FAMILIA'] == s_familia]
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    total_req = df_filtrado['VALOR'].sum()
    total_env = df_filtrado['VALOR-ENVIADO'].sum()
    fr = (total_env / total_req * 100) if total_req > 0 else 0
    col1.metric("Total Requerido", f"Q{total_req:,.2f}")
    col2.metric("Total Enviado", f"Q{total_env:,.2f}")
    col3.metric("Fill Rate %", f"{fr:.2f}%")
    
    df_dia_x_dia = df_filtrado.groupby('NODIA').agg({'VALOR-ENVIADO': 'sum', 'VALOR': 'sum'}).reset_index()
    df_dia_x_dia['FILL_RATE'] = (df_dia_x_dia['VALOR-ENVIADO'] / df_dia_x_dia['VALOR'] * 100).fillna(0)
    fig_diario = go.Figure()
    fig_diario.add_trace(go.Bar(x=df_dia_x_dia['NODIA'], y=df_dia_x_dia['VALOR-ENVIADO'], name="Valor Enviado", marker_color='#1f77b4', hovertemplate="<b>Día %{x}</b><br>Valor: Q%{y:,.1s}<extra></extra>"))
    fig_diario.add_trace(go.Scatter(x=df_dia_x_dia['NODIA'], y=df_dia_x_dia['FILL_RATE'], name="Fill Rate %", yaxis="y2", mode="lines+markers", line=dict(color="orange", width=3), hovertemplate="<b>Día %{x}</b><br>FR: %{y:.1f}%<extra></extra>"))
    fig_diario.update_layout(yaxis=dict(title="Enviado (Q)", tickformat=",.1s"), yaxis2=dict(title="FR (%)", overlaying="y", side="right", tickformat=".1f"), legend=dict(x=0, y=1.1, orientation="h"), hovermode="x unified")
    st.plotly_chart(fig_diario, use_container_width=True)
    
    st.write("---")
    df_pie = df_filtrado.groupby('FAMILIA')['VALOR-ENVIADO'].sum().reset_index()
    fig_pie = px.pie(df_pie, values='VALOR-ENVIADO', names='FAMILIA', hole=0.4, title="🍕 Distribución por Familia")
    st.plotly_chart(fig_pie, use_container_width=True)
    
    df_tienda_bar = df_filtrado.groupby('NOMBRE TIENDA')['VALOR-ENVIADO'].sum().reset_index().sort_values(by='VALOR-ENVIADO', ascending=True)
    top_sel = st.radio("Mostrar en gráfico:", options=["Top 10 Tiendas", "Top 20 Tiendas", "Todas"], index=1, horizontal=True)
    df_t_graf = df_tienda_bar.tail(10) if top_sel == "Top 10 Tiendas" else (df_tienda_bar.tail(20) if top_sel == "Top 20 Tiendas" else df_tienda_bar)
    fig_t = px.bar(df_t_graf, x='VALOR-ENVIADO', y='NOMBRE TIENDA', orientation='h', color='VALOR-ENVIADO', color_continuous_scale='Blues', text_auto=',.1s', title="🏪 Despacho por Tienda")
    fig_t.update_layout(xaxis=dict(tickformat=",.1s"), height=300+(len(df_t_graf)*20), coloraxis_showscale=False)
    st.plotly_chart(fig_t, use_container_width=True)

    # fin caja 2

elif opcion_menu == "📈 Resumen Ceo & Proyecciones" and not df.empty:
    st.title("📈 Resumen Ceo & Proyecciones")
    ano_actual_sis = str(pd.Timestamp.now().year)
    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    meses_unicos = [str(x) for x in df['MES'].unique() if pd.notna(x)]
    lista_meses = ["Todos los meses"] + sorted(meses_unicos, key=lambda m: orden_meses.get(m.upper(), 99))
    lista_familias = ["Todas las familias"] + sorted([str(x) for x in df['FAMILIA'].unique() if pd.notna(x)])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: s_tienda = st.selectbox("Tienda", options=lista_tiendas, key="p_t")
    with c2: s_ano = st.selectbox("Año", options=lista_anos, index=lista_anos.index(ano_actual_sis) if ano_actual_sis in lista_anos else 0, key="p_a")
    with c3: s_mes = st.selectbox("Mes", options=lista_meses, key="p_m")
    with c4: s_family = st.selectbox("Familia", options=lista_familias, key="p_f")
        
    df_filtrado = df.copy()
    if s_tienda != "Todas las tiendas": df_filtrado = df_filtrado[df_filtrado['NOMBRE TIENDA'] == s_tienda]
    if s_ano != "Todos los años": df_filtrado = df_filtrado[df_filtrado['AÑO'] == int(s_ano)]
    if s_mes != "Todos los meses": df_filtrado = df_filtrado[df_filtrado['MES'] == s_mes]
    if s_family != "Todas las familias": df_filtrado = df_filtrado[df_filtrado['FAMILIA'] == s_family]
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    total_req = df_filtrado['VALOR'].sum()
    total_env = df_filtrado['VALOR-ENVIADO'].sum()
    fr = (total_env / total_req * 100) if total_req > 0 else 0
    col1.metric("Total Requerido", f"Q{total_req:,.2f}")
    col2.metric("Total Enviado", f"Q{total_env:,.2f}")
    col3.metric("Fill Rate %", f"{fr:.2f}%")
    
    df_m = df_filtrado.groupby('MES').agg({'VALOR-ENVIADO': 'sum', 'VALOR': 'sum'}).reset_index()
    df_m['ORDEN'] = df_m['MES'].apply(lambda m: orden_meses.get(m.upper(), 99))
    df_m = df_m.sort_values(by='ORDEN')
    df_m['FILL_RATE'] = (df_m['VALOR-ENVIADO'] / df_m['VALOR'] * 100).fillna(0)
    
    fig_m = go.Figure()
    fig_m.add_trace(go.Bar(x=df_m['MES'], y=df_m['VALOR-ENVIADO'], name="Enviado", marker_color='#2ca02c', hovertemplate="<b>Mes: %{x}</b><br>Valor: Q%{y:,.1s}<extra></extra>"))
    fig_m.add_trace(go.Scatter(x=df_m['MES'], y=df_m['FILL_RATE'], name="FR %", yaxis="y2", mode="lines+markers", line=dict(color="red", width=3), hovertemplate="<b>Mes: %{x}</b><br>FR: %{y:.1f}%<extra></extra>"))
    fig_m.update_layout(yaxis=dict(title="Enviado (Q)", tickformat=",.1s"), yaxis2=dict(title="FR (%)", overlaying="y", side="right", tickformat=".1f"), legend=dict(x=0, y=1.1, orientation="h"), hovermode="x unified")
    st.plotly_chart(fig_m, use_container_width=True)

elif opcion_menu == "💰 Top Margen Real" and not df.empty:
    st.title("💰 Top Margen Real (Utilidad Neto)")
    ano_actual_sis = str(pd.Timestamp.now().year)
    lista_tiendas = ["Todas las tiendas"] + sorted([str(x) for x in df['NOMBRE TIENDA'].unique() if pd.notna(x)])
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    meses_unicos = [str(x) for x in df['MES'].unique() if pd.notna(x)]
    lista_meses = ["Todos los meses"] + sorted(meses_unicos, key=lambda m: orden_meses.get(m.upper(), 99))
    lista_familias = ["Todas las familias"] + sorted([str(x) for x in df['FAMILIA'].unique() if pd.notna(x)])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: s_tienda = st.selectbox("Tienda", options=lista_tiendas, key="m_t")
    with c2: s_ano = st.selectbox("Año", options=lista_anos, index=lista_anos.index(ano_actual_sis) if ano_actual_sis in lista_anos else 0, key="m_a")
    with c3: s_mes = st.selectbox("Mes", options=lista_meses, key="m_m")
    with c4: s_familia = st.selectbox("Familia", options=lista_familias, key="m_f")
        
    df_filtrado = df.copy()
    if s_tienda != "Todas las tiendas": df_filtrado = df_filtrado[df_filtrado['NOMBRE TIENDA'] == s_tienda]
    if s_ano != "Todos los años": df_filtrado = df_filtrado[df_filtrado['AÑO'] == int(s_ano)]
    if s_mes != "Todos los meses": df_filtrado = df_filtrado[df_filtrado['MES'] == s_mes]
    if s_familia != "Todas las familias": df_filtrado = df_filtrado[df_filtrado['FAMILIA'] == s_familia]
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    v_env = df_filtrado['VALOR-ENVIADO'].sum()
    c_bas = df_filtrado['COSTO'].sum()
    r_net = df_filtrado['RETORNO-NETO'].sum()
    t_req = df_filtrado['VALOR'].sum()
    fr = (v_env / t_req * 100) if t_req > 0 else 0
    
    col1.metric("Ventas (Enviado)", f"Q{v_env:,.2f}")
    col2.metric("Costo Base", f"Q{c_bas:,.2f}")
    col3.metric("🔥 Retorno Neto", f"Q{r_net:,.2f}")
    col4.metric("Fill Rate %", f"{fr:.2f}%")
    
    df_top_p = df_filtrado.groupby(['PRODUCTO', 'DESCRIPCION'])['RETORNO-NETO'].sum().reset_index().sort_values(by='RETORNO-NETO', ascending=False).head(15)
    fig_top = px.bar(df_top_p, x='RETORNO-NETO', y='DESCRIPCION', orientation='h', color='RETORNO-NETO', text_auto=',.2f', color_continuous_scale='Viridis', title="🏆 Top 15 mejores productos")
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)
    
    df_matriz = df_filtrado.groupby(['GRUPO', 'FAMILIA', 'PRODUCTO', 'DESCRIPCION']).agg({'CANTIDAD-ENV': 'sum', 'VALOR-ENVIADO': 'sum', 'COSTO': 'sum', 'RETORNO-NETO': 'sum'}).reset_index().sort_values(by='RETORNO-NETO', ascending=False)
    df_m_show = df_matriz.copy()
    for col in ['VALOR-ENVIADO', 'COSTO', 'RETORNO-NETO']: df_m_show[col] = df_m_show[col].map('Q{:,.2f}'.format)
    df_m_show['CANTIDAD-ENV'] = df_m_show['CANTIDAD-ENV'].map('{:,.0f}'.format)
    st.subheader("📋 Matriz de Auditoría de Margen")
    st.dataframe(df_m_show, use_container_width=True)

elif opcion_menu == "🏪 Por Tienda & Dias" and not df.empty:
    st.title("🏪 Rendimiento Por Tienda & Días")
    lista_anos = ["Todos los años"] + sorted([str(x) for x in df['AÑO'].unique() if x != 0])
    meses_unicos = [str(x) for x in df['MES'].unique() if pd.notna(x)]
    lista_meses = ["Todos los meses"] + sorted(meses_unicos, key=lambda m: orden_meses.get(m.upper(), 99))
    
    c1, c2 = st.columns(2)
    with c1: s_ano = st.selectbox("Año", options=lista_anos, index=lista_anos.index(str(pd.Timestamp.now().year)) if str(pd.Timestamp.now().year) in lista_anos else 0, key="td_a")
    with c2: s_mes = st.selectbox("Mes", options=lista_meses, key="td_m")
        
    df_filtrado = df.copy()
    if s_ano != "Todos los años": df_filtrado = df_filtrado[df_filtrado['AÑO'] == int(s_ano)]
    if s_mes != "Todos los meses": df_filtrado = df_filtrado[df_filtrado['MES'] == s_mes]
        
    st.subheader("📅 Distribución de Valor Enviado por Tienda y Día del Mes")
    df_pivot = df_filtrado.pivot_table(index='NOMBRE TIENDA', columns='NODIA', values='VALOR-ENVIADO', aggfunc='sum').fillna(0)
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
                    
                    # CORRECCIÓN: Tratamos DOCUMENTO como texto libre para evitar colapsos alfanuméricos
                    if 'DOCUMENTO' in df_txt.columns:
                        df_txt['DOCUMENTO'] = df_txt['DOCUMENTO'].astype(str).str.strip()
                        
                    # Conversión segura para el resto de enteros
                    for c in ['AÑO', 'DIA', 'NODIA']:
                        if c in df_txt.columns:
                            df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').fillna(0).astype(int)
                            
                    # Conversión segura para textos limpios
                    for c in ['NOMBRE TIENDA', 'MES', 'FAMILIA', 'GRUPO', 'DESCRIPCION']:
                        if c in df_txt.columns: 
                            df_txt[c] = df_txt[c].astype(str).fillna("No Especificado").str.strip()
                            
                    # Conversión segura para dinero y cantidades despachadas
                    for c in ['VALOR-ENVIADO', 'COSTO', 'VALOR', 'CANTIDAD-ENV', 'CANTIDAD-REQ']:
                        if c in df_txt.columns: 
                            df_txt[c] = pd.to_numeric(df_txt[c], errors='coerce').fillna(0)
                            
                    df_txt['RETORNO-NETO'] = df_txt['VALOR-ENVIADO'] - df_txt['COSTO']
                    df_txt.to_parquet("planta_historico.parquet", index=False)
                    
                    f_str = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                    msg = f"Última sincronización exitosa el {f_str} usando el origen '{arch_sub.name}'."
                    with open("planta_auditoria.txt", "w", encoding="utf-8") as f: f.write(msg)
                    st.success("✅ Archivo convertido a Parquet y auditoría registrada localmente. ¡Dale F5!")
                    st.balloons()
                except Exception as ex: st.error(f"Error en estructura: {ex}")
        with col_n:
            st.markdown("### ☁️ Sincronizar desde GitHub")
            if st.button("🗂️ Ejecutar Descarga desde GitHub", use_container_width=True):
                st.info("Espacio reservado: Listo para conectar el repositorio de la planta.")

    

