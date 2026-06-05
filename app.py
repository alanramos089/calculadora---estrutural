import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v7.0")
st.write("Projeto Automatizado: Insira a planta baixa por coordenadas e o sistema ergue o modelo 3D estrutural na hora.")

# Inicialização padrão com uma Sala e um Quarto posicionados lado a lado (Planta Livre)
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Sala Principal", "largura": 3.20, "comprimento": 4.00, "pos_x": 0.0, "pos_y": 0.0, "portas": 1, "janelas": 1},
        {"nome": "Dormitório 1", "largura": 3.00, "comprimento": 3.00, "pos_x": 3.20, "pos_y": 0.0, "portas": 1, "janelas": 1}
    ]

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Globais da Edificação")

with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.sidebar.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    pe_direito = st.sidebar.slider("Altura do Pé-Direito / Paredes (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.sidebar.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🗺️ Locação do Cômodo na Planta Baixa")
    nome_c = st.text_input("Nome do Ambiente", value="Cozinha")
    larg_c = st.number_input("Largura do Cômodo (Eixo X) (m)", min_value=1.0, max_value=15.0, value=3.20, step=0.1)
    comp_c = st.number_input("Comprimento do Cômodo (Eixo Y) (m)", min_value=1.0, max_value=15.0, value=3.50, step=0.1)
    
    st.info("💡 Escolha onde este cômodo vai iniciar em relação ao ponto zero do terreno:")
    start_x = st.number_input("Distância do Canto Esquerdo (X inicial)", value=0.0, step=0.1)
    start_y = st.number_input("Distância do Canto Inferior (Y inicial)", value=4.0, step=0.1)
    
    portas_c = st.number_input("Quantidade de Portas", min_value=0, max_value=4, value=1, step=1)
    janelas_c = st.number_input("Quantidade de Janelas", min_value=0, max_value=4, value=1, step=1)
    
    botao_calcular = st.form_submit_button("🧱 LANÇAR CÔMODO NA PLANTA")

if botao_calcular:
    st.session_state.comodos.append({
        "nome": nome_c, "largura": float(larg_c), "comprimento": float(comp_c), 
        "pos_x": float(start_x), "pos_y": float(start_y),
        "portas": int(portas_c), "janelas": int(janelas_c)
    })
    st.rerun()

# --- GERENCIADOR DE EXCLUSÃO ---
if st.session_state.comodos:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗑️ Modificar Planta Baixa")
    opcoes_exclusao = [f"{i} - {c['nome']} (X:{c['pos_x']} | Y:{c['pos_y']})" for i, c in enumerate(st.session_state.comodos)]
    comodo_para_deletar = st.sidebar.selectbox("Selecione qual deseja remover", opcoes_exclusao)
    
    if st.sidebar.button("❌ Remover do Projeto"):
        idx_deletar = int(comodo_para_deletar.split(" - ")[0])
        st.session_state.comodos.pop(idx_deletar)
        st.toast("Módulo removido da planta!")
        st.rerun()

if st.sidebar.button("🧹 Resetar Terreno / Planta"):
    st.session_state.comodos = []
    st.rerun()

if not st.session_state.comodos:
    st.warning("Adicione o primeiro cômodo para mapear a planta baixa do imóvel.")
    st.stop()

# --- CÁLCULOS VOLUMÉTRICOS ACUMULADOS ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0
total_telas_aço = 0.0
total_portas = 0
total_janelas = 0

area_porta_gabarito = 0.80 * 2.10  
area_janela_gabarito = 1.20 * 1.00 

for c in st.session_state.comodos:
    w = c["largura"]
    h = c["comprimento"]
    n_portas = c.get("portas", 0)
    n_janelas = c.get("janelas", 0)
    
    total_portas += n_portas
    total_janelas += n_janelas
    
    perimetro_centro = 2 * ((w + espessura_parede) + (h + espessura_parede))
    area_parede_bruta = perimetro_centro * pe_direito
    area_descontos = (n_portas * area_porta_gabarito) + (n_janelas * area_janela_gabarito)
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

# --- INTERFACE POR ABAS ---
tab0, tab1 = st.tabs(["📊 Lista de Materiais da Planta", "🧱 Planta Baixa Transposta em 3D"])

with tab0:
    st.subheader("📋 Configuração Dimensional dos Módulos")
    st.dataframe(st.session_state.comodos, use_container_width=True)
    
    st.subheader("🛒 Insumos Totais Calculados da Planta")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Geral de Concreto Usinado", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Lajes: {total_concreto_lajes:.2f}m³")
    with col2:
        st.metric(label="Área de Fôrma Modular (Dupla Face)", value=f"{forma_global:.2f} m²")
        st.caption(f"Calculado com desconto de vãos de esquadrias")
    with col3:
        st.metric(label="Área Metálica de Tela Soldada Q092", value=f"{total_telas_aço:.2f} m²")
        st.caption(f"Armadura centralizada nas paredes monolíticas")

with tab1:
    st.subheader("🧱 Maquete Tridimensional da Planta Desenhada")
    st.write("Abaixo, os ambientes ganham altura de parede automaticamente baseados na locação da planta.")
    
    fig_3d = go.Figure()
    
    # Marcadores para as cotas dos limites externos máximos do terreno
    max_x, max_y = 0.0, 0.0
    
    for c in st.session_state.comodos:
        w = c["largura"]
        h = c["comprimento"]
        px = c["pos_x"]
        py = c["pos_y"]
        nome = c["nome"]
        
        # Monitora o tamanho total do imóvel para ajustar o zoom da câmera
        if (px + w) > max_x: max_x = (px + w)
        if (py + h) > max_y: max_y = (py + h)
            
        # 1. RENDERIZAÇÃO DAS PAREDES DO CÔMODO (Posicionado em sua coordenada X, Y livre)
        fig_3d.add_trace(go.Mesh3d(
            x=[px, px+w, px+w, px, px, px+w, px+w, px],
            y=[py, py, py+h, py+h, py, py, py+h, py+h],
            z=[0, 0, 0, 0, pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(140, 145, 150)', opacity=0.65, flatshading=True, name=nome
        ))
        
        # 2. RENDERIZAÇÃO DA LAJE SUPERIOR COM BEIRAL INDIVIDUAL
        b = 0.25  # Beiral técnico de 25cm
        fig_3d.add_trace(go.Mesh3d(
            x=[px-b, px+w+b, px+w+b, px-b],
            y=[py-b, py-b, py+h+b, py+h+b],
            z=[pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(175, 180, 185)', opacity=0.85, name=f"Laje {nome}"
        ))
        
        # 3. LINHAS DE CONTORNO PRETAS EM CADA MÓDULO PARA SEPARAÇÃO TÉCNICA
        linhas_c = [
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py], [pe_direito]*5),
            ([px, px+w, px+w, px, px], [py, py, py+h, py+h, py], [0]*5),
            (, [py, py], [0, pe_direito]),
            ([px+w, px+w], [py, py], [0, pe_direito]),
            ([px+w, px+w], [py+h, py+h], [0, pe_direito]),
            (, [py+h, py+h], [0, pe_direito])
        ]
        for lx, ly, lz in linhas_c:
            fig_3d.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=3), showlegend=False))
            
        # 4. TEXTO DE IDENTIFICAÇÃO DO AMBIENTE NO TOPO DO BLOCO
        fig_3d.add_trace(go.Scatter3d(
            x=[px + w/2], y=[py + h/2], z=[pe_direito + 0.3],
            mode="text", text=[nome], textfont=dict(color="cyan", size=11, family="Arial Black")
        ))
        
        # 5. COTAS DE CADA COMPARTIMENTO INDIVIDUAL
        fig_3d.add_trace(go.Scatter3d(x=[px + w/2], y=[py - 0.2], z=[0.05], mode="text", text=[f"{w:.2f}m"], textfont=dict(color="red", size=11)))
        fig_3d.add_trace(go.Scatter3d(x=[px + w + 0.2], y=[py + h/2], z=[0.05], mode="text", text=[f"{h:.2f}m"], textfont=dict(color="red", size=11)))

    # COTAS DO LIMITE EXTERNO DO GABARITO DA CASA (Linhas de divisa laranja)
    fig_3d.add_trace(go.Scatter3d(x=[max_x/2], y=[-0.8], z=[0.1], mode="text", text=[f"LARGURA MÁXIMA DA PLANTA = {max_x:.2f} m"], textfont=dict(color="orange", size=13, family="Arial Black")))
    fig_3d.add_trace(go.Scatter3d(x=[max_x + 0.8], y=[max_y/2], z=[0.1], mode="text", text=[f"COMPRIMENTO MÁXIMO DA PLANTA = {max_y:.2f} m"], textfont=dict(color="orange", size=13, family="Arial Black")))

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
