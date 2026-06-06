import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_drawable_canvas import st_canvas

# Configuração da página web
st.set_page_config(page_title="Configurador Concreto Modular", layout="wide")
st.title("🏗️ Sistema Estrutural: Concreto Modular Armado Monolítico v9.1")
st.write("Mesa de Desenho e Verificação de Engenharia: Desenhe no grid e o sistema valida a estabilidade mecânica na hora.")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Técnicos de Engenharia")
espessura_parede = st.sidebar.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
pe_direito = st.sidebar.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
espessura_laje = st.sidebar.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("🔬 Propriedades dos Materiais")
fck = st.sidebar.selectbox("Resistência do Concreto (fck)", [20, 25, 30, 35, 40], index=1, help="Resistência característica à compressão em MPa")
sobrecarga_laje = st.sidebar.slider("Sobrecarga Atuante na Laje (kN/m²)", min_value=1.5, max_value=5.0, value=2.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Análise de Estabilidade:** O sistema calcula o peso próprio do concreto (25 kN/m³) + sobrecarga e realiza a verificação de esmagamento axial da parede.")

# --- INTERFACE POR ABAS ---
tab0, tab1, tab2 = st.tabs(["✏️ Mesa de Desenho", "📊 Análise Estrutural e Materiais", "🧱 Maquete 3D Técnica"])

PIXELS_POR_METRO = 40.0
comodos_detectados = []

# ABA 0: MESA DE DESENHO
with tab0:
    st.subheader("✏️ Desenhe a Planta Baixa do Imóvel")
    st.caption("Trace os cômodos no grid. As correções e verificações técnicas abrirão nas abas seguintes.")
    
    canvas_result = st_canvas(
        fill_color="rgba(135, 140, 145, 0.4)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#262730",
        update_streamlit=True,
        height=400,
        width=800,
        drawing_mode="rect",
        display_toolbar=True,
        key="mesa_desenho_tecnica_v91",
    )

    comodos_temporarios = []
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for idx, obj in enumerate(objects):
            if obj["type"] == "rect":
                larg_aprox = round((obj["width"] / PIXELS_POR_METRO) / 0.05) * 0.05
                comp_aprox = round((obj["height"] / PIXELS_POR_METRO) / 0.05) * 0.05
                x_aprox = round((obj["left"] / PIXELS_POR_METRO) / 0.05) * 0.05
                y_aprox = round((obj["top"] / PIXELS_POR_METRO) / 0.05) * 0.05
                
                comodos_temporarios.append({
                    "ID": idx + 1,
                    "Ambiente": f"Módulo {idx + 1}",
                    "Largura (m)": float(larg_aprox),
                    "Comprimento (m)": float(comp_aprox),
                    "Afastamento X (m)": float(x_aprox),
                    "Afastamento Y (m)": float(y_aprox)
                })

    if comodos_temporarios:
        st.markdown("---")
        st.markdown("### 📝 Ajuste Fino de Dimensões")
        dados_ajustados = st.data_editor(comodos_temporarios, use_container_width=True, num_rows="fixed", key="editor_v91")
        comodos_detectados = dados_ajustados
    else:
        st.warning("⚠️ Desenhe um retângulo com o mouse no quadro acima para iniciar.")
        st.stop()

# --- MOTOR DE CÁLCULO ESTRUTURAL ACUMULADO ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0
total_telas_aço = 0.0

gama_concreto = 1.4
gama_cargas = 1.4

for c in comodos_detectados:
    w = c["Largura (m)"]
    h = c["Comprimento (m)"]
    
    perimetro_centro = 2 * ((w + espessura_parede) + (h + espessura_parede))
    area_parede_bruta = perimetro_centro * pe_direito
    area_descontos = (0.80 * 2.10) + (1.20 * 1.00)
    area_parede_liquida = max(0.1, area_parede_bruta - area_descontos)
    
    total_concreto_paredes += area_parede_liquida * espessura_parede
    total_concreto_lajes += (w * h) * espessura_laje
    
    total_forma_paredes += (2 * perimetro_centro * pe_direito) - (area_descontos * 2)
    total_forma_lajes += (w * h)
    total_telas_aço += area_parede_bruta * 1.15

concreto_global = total_concreto_paredes + total_concreto_lajes
forma_global = total_forma_paredes + total_forma_lajes

# --- ANÁLISE MECÂNICA DA PAREDE MAIS CRÍTICA ---
comodo_critico = comodos_detectados[-1]
L_c = comodo_critico["Largura (m)"]
C_c = comodo_critico["Comprimento (m)"]

peso_proprio_laje = espessura_laje * 25.0  
carga_total_laje_projeto = (peso_proprio_laje + sobrecarga_laje) * gama_cargas
area_influencia_laje = (L_c * C_c)
carga_laje_na_parede = (carga_total_laje_projeto * area_influencia_laje) / max(0.1, (2 * (L_c + C_c)))
peso_proprio_parede_projeto = (pe_direito * espessura_parede * 25.0) * gama_concreto
carga_atuante_total = carga_laje_na_parede + peso_proprio_parede_projeto 

fck_design = (fck * 1000) / gama_concreto 
area_secao_metro = espessura_parede * 1.0  
esbeltez_fator = 1.0 - ((pe_direito) / (32 * espessura_parede))**2
esbeltez_fator = max(0.1, esbeltez_fator) 
capacidade_resistencia = 0.55 * 0.70 * fck_design * area_secao_metro * esbeltez_fator 

razao_esforco = carga_atuante_total / capacidade_resistencia

# ABA 1: ANÁLISE ESTRUTURAL TÉCNICA
with tab1:
    st.subheader("📊 Relatório de Verificação de Estabilidade (Paredes de Corte)")
    
    col_status, col_cap, col_at = st.columns(3)
    with col_status:
        if razao_esforco <= 1.0:
            st.success("🟢 ESTRUTURA APROVADA")
            st.metric(label="Taxa de Utilização Estrutural", value=f"{razao_esforco*100:.1f} %", delta="Seguro", delta_color="normal")
        else:
            st.error("🔴 ALERTA: RISCO DE ESBARRAMENTO")
            st.metric(label="Taxa de Utilização Estrutural", value=f"{razao_esforco*100:.1f} %", delta="Aumentar Espessura", delta_color="inverse")
            
    with col_cap:
        st.metric(label="Capacidade Última da Parede (kN/m)", value=f"{capacidade_resistencia:.1f} kN/m")
        st.caption("Limite físico de esmagamento do concreto modular")
    with col_at:
        st.metric(label="Carga de Projeto Atuante (kN/m)", value=f"{carga_atuante_total:.1f} kN/m")
        st.caption("Peso acumulado da estrutura + sobrecarga de norma")
        
    st.markdown("---")
    st.subheader("🛒 Cubagem e Lista de Materiais Líquidos")
    col_mat1, col_mat2, col_mat3 = st.columns(3)
    with col_mat1:
        st.metric(label="Volume Geral de Concreto Usinado", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Lajes: {total_concreto_lajes:.2f}m³")
    with col_mat2:
        st.metric(label="Área de Fôrma Modular (Dupla Face)", value=f"{forma_global:.2f} m²")
        st.caption("Descontados vãos automáticos de portas e janelas")
    with col_mat3:
        st.metric(label="Área Metálica de Tela Soldada Q092", value=f"{total_telas_aço:.2f} m²")
        st.caption("Armadura centralizada nas paredes maciças")

# ABA 2: MAQUETE 3D TÉCNICA (REPRESENTAÇÃO BLINDADA)
with tab2:
    st.subheader("🧱 Maquete Estrutural e Projeto Dimensional")
    fig_3d = go.Figure()
    max_x, max_y = 0.0, 0.0
    
    for c in comodos_detectados:
        w = c["Largura (m)"]
        h = c["Comprimento (m)"]
        px = c["Afastamento X (m)"]
        py = c["Afastamento Y (m)"]
        nome = c["Ambiente"]
        
        if (px + w) > max_x: max_x = (px + w)
        if (py + h) > max_y: max_y = (py + h)
            
        # Desenho blindado das 4 paredes fechadas por contornos de malha estrutural
        fig_3d.add_trace(go.Scatter3d(
            x=[px, px+w, px+w, px, px, px, px+w, px+w, px, px],
            y=[py, py, py+h, py+h, py, py, py, py+h, py+h, py],
            z=[0, 0, 0, 0, 0, pe_direito, pe_direito, pe_direito, pe_direito, pe_direito],
            mode='lines',
            line=dict(color='rgb(135, 140, 145)', width=8),
            name="Paredes Maciças"
        ))
        
        # Laje Superior com Beiral Técnico (25cm)
        b = 0.25  
        fig_3d.add_trace(go.Mesh3d(
            x=[px-b, px+w+b, px+w+b, px-b], y=[py-b, py-b, py+h+b, py+h+b], z=[pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(165, 170, 175)', opacity=0.95, name="Laje"
        ))
        
        # Linhas pretas de acabamento técnico
        linhas_c = [
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py], [pe_direito]*5),
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py], [0]*5),
            ([px, px], [py, py], [0, pe_direito]), ([px+w, px+w], [py, py], [0, pe_direito]),
            ([px+w, px+w], [py+h, py+h], [0, pe_direito]), ([px, px], [py+h, py+h], [0, pe_direito])
        ]
        for lx, ly, lz in linhas_c:
            fig_3d.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=3), showlegend=False))
            
        fig_3d.add_trace(go.Scatter3d(x=[px + w/2], y=[py + h/2], z=[pe_direito + 0.3], mode="text", text=[nome], textfont=dict(color="cyan", size=11, family="Arial Black")))
        fig_3d.add_trace(go.Scatter3d(x=[px + w/2], y=[py - 0.2], z=[0.05], mode="text", text=[f"L={w:.2f}m"], textfont=dict(color="red", size=11, family="Arial Black")))
        fig_3d.add_trace(go.Scatter3d(x=[px + w + 0.2], y=[py + h/2], z=[0.05], mode="text", text=[f"C={h:.2f}m"], textfont=dict(color="red", size=11, family="Arial Black")))

    fig_3d.update_layout(
        dragmode='orbit',
        scene=dict(
            xaxis=dict(title='Largura X (m)', range=[-1, max_x+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            yaxis=dict(title='Comprimento Y (m)', range=[-1, max_y+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
