import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_drawable_canvas import st_canvas

# Configuração da página web
st.set_page_config(page_title="Configurador Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v8.1")
st.write("Mesa de Desenho Interativa: Desenhe os cômodos com o mouse no grid para erguer a estrutura em 3D.")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Globais do Molde")
espessura_parede = st.sidebar.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
pe_direito = st.sidebar.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
espessura_laje = st.sidebar.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Como usar a Mesa de Desenho:**\n1. Selecione a ferramenta de Retângulo (ícone quadrado na barra do desenho).\n2. Clique e arraste no grid para desenhar um cômodo.\n3. Cada quadrado grande do grid equivale a **1,0 metro** na obra.\n4. Mude para a aba do 3D para inspecionar o modelo erguido!")

# --- INTERFACE POR ABAS (CORREÇÃO DE DECLARAÇÃO ESTRETA) ---
tab0, tab1, tab2 = st.tabs(["✏️ Mesa de Desenho da Planta", "📊 Lista de Materiais Calculada", "🧱 Projeto Estrutural 3D"])

# Fator de conversão: 40 pixels no canvas = 1.0 metro na vida real
PIXELS_POR_METRO = 40.0

comodos_detectados = []

# ABA 0: MESA DE DESENHO
with tab0:
    st.subheader("✏️ Desenhe a Planta Baixa do Imóvel")
    st.caption("Use o mouse para traçar os ambientes sobre a grade modular. Os materiais e o 3D serão gerados na hora.")
    
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
        key="mesa_desenho_modular",
    )

    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for idx, obj in enumerate(objects):
            if obj["type"] == "rect":
                left = obj["left"]
                top = obj["top"]
                width = obj["width"]
                height = obj["height"]
                
                px_real = left / PIXELS_POR_METRO
                py_real = top / PIXELS_POR_METRO
                largura_real = width / PIXELS_POR_METRO
                comprimento_real = height / PIXELS_POR_METRO
                
                comodos_detectados.append({
                    "id": idx + 1,
                    "nome": f"Ambiente {idx + 1}",
                    "largura": largura_real,
                    "comprimento": comprimento_real,
                    "pos_x": px_real,
                    "pos_y": py_real
                })

    if comodos_detectados:
        st.success(f"✔️ {len(comodos_detectados)} ambiente(s) mapeado(s) com sucesso pelo mouse!")
    else:
        st.warning("⚠️ Nenhum cômodo desenhado ainda. Use o mouse para traçar um retângulo no quadro acima.")

# Se não houver cômodos, interrompe antes de tentar calcular as abas seguintes
if not comodos_detectados:
    st.stop()

# --- CÁLCULOS VOLUMÉTRICOS BASEADOS NO DESENHO DO MOUSE ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0
total_telas_aço = 0.0

area_porta_gabarito = 0.80 * 2.10  
area_janela_gabarito = 1.20 * 1.00 

for c in comodos_detectados:
    w = c["largura"]
    h = c["comprimento"]
    
    perimetro_centro = 2 * ((w + espessura_parede) + (h + espessura_parede))
    area_parede_bruta = perimetro_centro * pe_direito
    area_descontos = area_porta_gabarito + area_janela_gabarito
    area_parede_liquida = area_parede_bruta - area_descontos
    
    total_concreto_paredes += (area_parede_liquida * espessura_parede)
    total_concreto_lajes += ((w * h) * espessura_laje)
    
    forma_interna_bruta = 2 * (w + h) * pe_direito
    forma_externa_bruta = 2 * ((w + 2*espessura_parede) + (h + 2*espessura_parede)) * pe_direito
    total_forma_paredes += (forma_interna_bruta + forma_externa_bruta) - (area_descontos * 2)
    total_forma_lajes += (w * h)
    
    total_telas_aço += area_parede_bruta * 1.15 

concreto_global = total_concreto_paredes + total_concreto_lajes
forma_global = total_forma_paredes + total_forma_lajes

# ABA 1: LISTA DE MATERIAIS (INDEXADA CORRETAMENTE)
with tab1:
    st.subheader("📋 Lista de Materiais Consolidada do Desenho")
    st.dataframe(comodos_detectados, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Geral de Concreto Usinado", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Lajes: {total_concreto_lajes:.2f}m³")
    with col2:
        st.metric(label="Área de Fôrma Modular (Dupla Face)", value=f"{forma_global:.2f} m²")
        st.caption("Calculado automaticamente com desconto de vãos padrão")
    with col3:
        st.metric(label="Área Metálica de Tela Soldada Q092", value=f"{total_telas_aço:.2f} m²")
        st.caption("Armadura de aço centralizada nas paredes maciças")

# ABA 2: MAQUETE 3D (INDEXADA CORRETAMENTE)
with tab2:
    st.subheader("🧱 Planta Baixa Transposta em 3D")
    st.write("Gire o modelo abaixo para analisar os módulos nas posições exatas em que foram desenhados com o mouse.")
    
    fig_3d = go.Figure()
    max_x, max_y = 0.0, 0.0
    
    for c in comodos_detectados:
        w = c["largura"]
        h = c["comprimento"]
        px = c["pos_x"]
        py = c["pos_y"]
        nome = c["nome"]
        
        if (px + w) > max_x: max_x = (px + w)
        if (py + h) > max_y: max_y = (py + h)
            
        fig_3d.add_trace(go.Mesh3d(
            x=[px, px+w, px+w, px, px, px+w, px+w, px],
            y=[py, py, py+h, py+h, py, py, py+h, py+h],
            z=[0, 0, 0, 0, pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(140, 145, 150)', opacity=0.65, flatshading=True, name=nome
        ))
        
        b = 0.25  
        fig_3d.add_trace(go.Mesh3d(
            x=[px-b, px+w+b, px+w+b, px-b],
            y=[py-b, py-b, py+h+b, py+h+b],
            z=[pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(175, 180, 185)', opacity=0.85, name=f"Laje {nome}"
        ))
        
        linhas_c = [
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py], [pe_direito]*5),
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py],*5),
            ([px, px], [py, py], [0, pe_direito]),
            ([px+w, px+w], [py, py], [0, pe_direito]),
            ([px+w, px+w], [py+h, py+h], [0, pe_direito]),
            ([px, px], [py+h, py+h], [0, pe_direito])
        ]
        for lx, ly, lz in linhas_c:
            fig_3d.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=3), showlegend=False))
            
        fig_3d.add_trace(go.Scatter3d(
            x=[px + w/2], y=[py + h/2], z=[pe_direito + 0.3],
            mode="text", text=[nome], textfont=dict(color="cyan", size=11, family="Arial Black")
        ))
        
        fig_3d.add_trace(go.Scatter3d(x=[px + w/2], y=[py - 0.2], z=[0.05], mode="text", text=[f"{w:.2f}m"], textfont=dict(color="red", size=11)))
        fig_3d.add_trace(go.Scatter3d(x=[px + w + 0.2], y=[py + h/2], z=[0.05], mode="text", text=[f"{h:.2f}m"], textfont=dict(color="red", size=11)))

    fig_3d.add_trace(go.Scatter3d(x=[max_x/2], y=[-0.8], z=[0.1], mode="text", text=[f"LARGURA MÁXIMA DA CASA = {max_x:.2f} m"], textfont=dict(color="orange", size=13, family="Arial Black")))
    fig_3d.add_trace(go.Scatter3d(x=[max_x + 0.8], y=[max_y/2], z=[0.1], mode="text", text=[f"COMPRIMENTO MÁXIMO DA CASA = {max_y:.2f} m"], textfont=dict(color="orange", size=13, family="Arial Black")))

    fig_3d.update_layout(
        dragmode='orbit',
        scene=dict(
            xaxis=dict(title='Eixo Largura X (m)', range=[-1, max_x+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            yaxis=dict(title='Eixo Comprimento Y (m)', range=[-1, max_y+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            zaxis=dict(title='Altura Z (m)', range=[0, pe_direito+0.8], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.4)), aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=700, showlegend=False
    )
    st.plotly_chart(fig_3d, use_container_width=True)
