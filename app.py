import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v3.6")
st.write("Cálculo integrado de fôrmas e cubagem para paredes e lajes concretadas simultaneamente.")

# Inicializa a lista de cômodos na sessão
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Sala Principal", "largura": 4.00, "comprimento": 3.50, "carga": 1.5}
    ]

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros do Módulo")

with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    pe_direito = st.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🚪 Adicionar Novo Cômodo")
    nome_c = st.text_input("Nome do Cômodo", value="Quarto")
    larg_c = st.number_input("Largura Interna (m)", min_value=1.0, max_value=15.0, value=3.20, step=0.1)
    comp_c = st.number_input("Comprimento Interno (m)", min_value=1.0, max_value=15.0, value=3.00, step=0.1)
    
    botao_calcular = st.form_submit_button("🚀 CALCULAR MÓDULO MONOLÍTICO")

if botao_calcular:
    if not any(c['nome'] == nome_c and c['largura'] == larg_c for c in st.session_state.comodos):
        st.session_state.comodos.append({"nome": nome_c, "largura": larg_c, "comprimento": comp_c, "carga": 1.5})

if st.sidebar.button("🧹 Limpar Tudo"):
    st.session_state.comodos = []
    st.rerun()

if not st.session_state.comodos:
    st.warning("Adicione um cômodo para processar.")
    st.stop()

# --- CÁLCULOS VOLUMÉTRICOS DO MÉTODO MODULAR ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0

comodo_foco = st.session_state.comodos[-1]
L = comodo_foco["largura"]
C = comodo_foco["comprimento"]

for c in st.session_state.comodos:
    w = c["largura"]
    h = c["comprimento"]
    perimetro_centro = 2 * ((w + espessura_parede) + (h + espessura_parede))
    vol_parede = perimetro_centro * espessura_parede * pe_direito
    total_concreto_paredes += vol_parede
    vol_laje = (w * h) * espessura_laje
    total_concreto_lajes += vol_laje
    forma_interna = 2 * (w + h) * pe_direito
    forma_externa = 2 * ((w + 2*espessura_parede) + (h + 2*espessura_parede)) * pe_direito
    total_forma_paredes += (forma_interna + forma_externa)
    total_forma_lajes += (w * h)

concreto_global = total_concreto_paredes + total_concreto_lajes
forma_global = total_forma_paredes + total_forma_lajes

# --- INTERFACE POR ABAS ---
tabs = st.tabs(["📊 Quantitativos Modulares", "🧱 Visualização das Paredes Maciças 3D"])

# CORREÇÃO DA SINTAXE DAS ABAS AQUI:
with tabs[0]:
    st.subheader("📋 Painel de Controle de Concretagem Monolítica")
    st.dataframe(st.session_state.comodos, use_container_width=True)
    
    st.subheader("🛒 Consumo Real de Insumos para a Concretagem Única")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Total de Concreto", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Laje: {total_concreto_lajes:.2f}m³")
    with col2:
        st.metric(label="Área Total de Fôrma Modular", value=f"{forma_global:.2f} m²")
        st.caption(f"Paredes (Dupla Face): {total_forma_paredes:.2f}m² | Fundo de Laje: {total_forma_lajes:.2f}m²")
    with col3:
        escoras = int(np.ceil(total_forma_lajes * 1.2))
        st.metric(label="Torres / Escoras de Laje", value=f"{escoras} unid")
        st.caption("Alinhadores de fôrma de parede inclusos na paginação técnica")

with tabs[1]:
    st.subheader(f"🧱 Maquete Estrutural Monolítica 3D: {comodo_foco['nome']}")
    st.write("Use o mouse para girar o modelo e verificar as paredes maciças integradas à laje.")
    
    fig_3d = go.Figure()
    
    # Definição dos vértices das paredes (Caixa Sólida)
    x_v = [0, L, L, 0, 0, L, L, 0]
    y_v = [0, 0, C, C, 0, 0, C, C]
    z_v = [0, 0, 0, 0, pe_direito, pe_direito, pe_direito, pe_direito]
    
    # Triângulos que fecham as faces verticais das paredes
    i_v = [0, 0, 1, 1, 2, 2, 3, 3]
    j_v = [1, 4, 2, 5, 3, 6, 0, 7]
    k_v = [4, 5, 5, 6, 6, 7, 7, 4]
    
    # Desenha as paredes de concreto fechadas
    fig_3d.add_trace(go.Mesh3d(
        x=x_v, y=y_v, z=z_v,
        i=i_v, j=j_v, k=k_v,
        color='rgb(120, 125, 130)',
        opacity=0.90,
        flatshading=True,
        name="Paredes de Concreto"
    ))
    
    # Desenha a laje superior
    fig_3d.add_trace(go.Mesh3d(
        x=[0, L, L, 0], y=[0, 0, C, C], 
        z=[pe_direito, pe_direito, pe_direito, pe_direito],
        color='rgb(160, 165, 170)', 
        opacity=0.95,
        name="Laje Maciça"
    ))
    
    # Linhas de contorno estrutural
    linhas = [
        ([0, L, L, 0, 0], [0, 0, C, C, 0], [0, 0, 0, 0, 0]), 
        ([0, L, L, 0, 0], [0, 0, C, C, 0], [pe_direito, pe_direito, pe_direito, pe_direito, pe_direito]), 
        ([0, 0], [0, 0], [0, pe_direito]),
        ([L, L], [0, 0], [0, pe_direito]),
        ([L, L], [C, C], [0, pe_direito]),
        ([0, 0], [C, C], [0, pe_direito])
    ]
    for lx, ly, lz in linhas:
        fig_3d.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz, mode='lines', 
            line=dict(color='black', width=3), showlegend=False
        ))

    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title='Largura (m)', range=[-0.5, L+1], backgroundcolor="rgb(30, 30, 30)", gridcolor="gray"),
            yaxis=dict(title='Comprimento (m)', range=[-0.5, C+1], backgroundcolor="rgb(30, 30, 30)", gridcolor="gray"),
            zaxis=dict(title='Altura (m)', range=[0, pe_direito+0.8], backgroundcolor="rgb(30, 30, 30)", gridcolor="gray"),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=600,
        showlegend=False
    )
    st.plotly_chart(fig_3d, use_container_width=True)
