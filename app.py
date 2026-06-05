import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v3.7")
st.write("Cálculo integrado com desconto automático de vãos de portas e janelas nas fôrmas e cubagem.")

# Inicializa a lista de cômodos na sessão se não existir
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Sala Principal", "largura": 4.00, "comprimento": 3.50, "portas": 1, "janelas": 1}
    ]

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Globais do Molde")

with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    pe_direito = st.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🚪 Adicionar Novo Cômodo com Vãos")
    nome_c = st.text_input("Nome do Cômodo", value="Quarto")
    larg_c = st.number_input("Largura Interna (m)", min_value=1.0, max_value=15.0, value=3.20, step=0.1)
    comp_c = st.number_input("Comprimento Interno (m)", min_value=1.0, max_value=15.0, value=3.00, step=0.1)
    
    # NOVOS INPUTS DE VÃOS PEDIDOS
    portas_c = st.number_input("Quantidade de Portas (0.80x2.10m)", min_value=0, max_value=4, value=1, step=1)
    janelas_c = st.number_input("Quantidade de Janelas (1.20x1.00m)", min_value=0, max_value=4, value=1, step=1)
    
    botao_calcular = st.form_submit_button("🚀 CALCULAR MÓDULO COM VÃOS")

if botao_calcular:
    if not any(c['nome'] == nome_c and c['largura'] == larg_c for c in st.session_state.comodos):
        st.session_state.comodos.append({
            "nome": nome_c, "largura": larg_c, "comprimento": comp_c, 
            "portas": portas_c, "janelas": janelas_c
        })

if st.sidebar.button("🧹 Limpar Tudo"):
    st.session_state.comodos = []
    st.rerun()

if not st.session_state.comodos:
    st.warning("Adicione um cômodo para processar.")
    st.stop()

# --- CÁLCULOS VOLUMÉTRICOS COM DESCONTO DE VÃOS ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0
total_portas = 0
total_janelas = 0

comodo_foco = st.session_state.comodos[-1]
L = comodo_foco["largura"]
C = comodo_foco["comprimento"]

# Áreas padrão de vãos para desconto
area_porta_gabarito = 0.80 * 2.10  # 1.68 m²
area_janela_gabarito = 1.20 * 1.00 # 1.20 m²

for c in st.session_state.comodos:
    w = c["largura"]
    h = c["comprimento"]
    n_portas = c["portas"]
    n_janelas = c["janelas"]
    
    total_portas += n_portas
    total_janelas += n_janelas
    
    # Perímetro médio da parede maciça
    perimetro_centro = 2 * ((w + espessura_parede) + (h + espessura_parede))
    
    # Área bruta de todas as paredes deste cômodo
    area_parede_bruta = perimetro_centro * pe_direito
    
    # Desconto dos vãos de portas e janelas na área de parede
    area_descontos = (n_portas * area_porta_gabarito) + (n_janelas * area_janela_gabarito)
    area_parede_liquida = area_parede_bruta - area_descontos
    
    # Cubagem de concreto correta (Apenas onde há parede física)
    vol_parede = area_parede_liquida * espessura_parede
    total_concreto_paredes += vol_parede
    
    # Volume de concreto da laje maciça
    vol_laje = (w * h) * espessura_laje
    total_concreto_lajes += vol_laje
    
    # Fôrmas modulares das paredes (Face Interna + Face Externa) descontando os vãos abertos
    forma_interna_bruta = 2 * (w + h) * pe_direito
    forma_externa_bruta = 2 * ((w + 2*espessura_parede) + (h + 2*espessura_parede)) * pe_direito
    
    # Multiplica por 2 porque abre o vão na fôrma da frente e na fôrma de trás
    total_forma_paredes += (forma_interna_bruta + forma_externa_bruta) - (area_descontos * 2)
    total_forma_lajes += (w * h)

concreto_global = total_concreto_paredes + total_concreto_lajes
forma_global = total_forma_paredes + total_forma_lajes

# --- INTERFACE POR ABAS ---
tabs = st.tabs(["📊 Quantitativos Realistas", "🧱 Maquete 3D Prédio/Cômodo"])

with tabs[0]:
    st.subheader("📋 Painel Construtivo (Paredes de Concreto)")
    st.dataframe(st.session_state.comodos, use_container_width=True)
    
    st.subheader("🛒 Consumo de Materiais Líquidos (Já descontando Portas e Janelas)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Real de Concreto", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Laje: {total_concreto_lajes:.2f}m³")
    with col2:
        st.metric(label="Área de Fôrma de Alumínio/Aço", value=f"{forma_global:.2f} m²")
        st.caption(f"Descontados {total_portas} port. e {total_janelas} jan. da paginação")
    with col3:
        escoras = int(np.ceil(total_forma_lajes * 1.2))
        st.metric(label="Gabaritos / Kit Vão de Portas", value=f"{total_portas} jgs")
        st.caption(f"Necessário separar {total_portas} caixilhos estruturais para travar a concretagem")

with tabs[1]:
    st.subheader(f"🧱 Paredes Sólidas Verticais Prontas: {comodo_foco['nome']}")
    st.write("Verifique a geometria real das paredes retas de concreto moldadas in loco.")
    
    fig_3d = go.Figure()
    
    # CORREÇÃO GEOMÉTRICA DOS TRIÂNGULOS (PAREDES RETAS VERTICAIS)
    # 8 pontos de quina: 4 no chão (0 a 3) e 4 no topo (4 a 7)
    x_v = [0, L, L, 0,  0, L, L, 0]
    y_v = [0, 0, C, C,  0, 0, C, C]
    z_v = [0, 0, 0, 0,  pe_direito, pe_direito, pe_direito, pe_direito]
    
    # Ordem de triângulos correta para fechar caixas verticais sem distorção piramidal
    i_v = [0, 0, 1, 1, 2, 2, 3, 3]
    j_v = [1, 5, 2, 6, 3, 7, 0, 4]
    k_v = [5, 4, 6, 5, 7, 6, 4, 7]
    
    # Paredes verticais sólidas cinzas
    fig_3d.add_trace(go.Mesh3d(
        x=x_v, y=y_v, z=z_v, i=i_v, j=j_v, k=k_v,
        color='rgb(140, 145, 150)', opacity=0.95, flatshading=True, name="Paredes"
    ))
    
    # Teto / Laje plana superior
    fig_3d.add_trace(go.Mesh3d(
        x=[0, L, L, 0], y=[0, 0, C, C], z=[pe_direito, pe_direito, pe_direito, pe_direito],
        color='rgb(170, 175, 180)', opacity=0.9, name="Laje"
    ))
    
    # Linhas de quina pretas limpas para dar acabamento tridimensional
    linhas = [
        ([0, L, L, 0, 0], [0, 0, C, C, 0], [0, 0, 0, 0, 0]),
        ([0, L, L, 0, 0], [0, 0, C, C, 0], [pe_direito, pe_direito, pe_direito, pe_direito, pe_direito]),
        ([0, 0], [0, 0], [0, pe_direito]),
        ([L, L], [0, 0], [0, pe_direito]),
        ([L, L], [C, C], [0, pe_direito]),
        ([0, 0], [C, C], [0, pe_direito])
    ]
    for lx, ly, lz in linhas:
        fig_3d.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=4), showlegend=False))

    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title='Largura (m)', range=[-0.5, L+1], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            yaxis=dict(title='Comprimento (m)', range=[-0.5, C+1], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            zaxis=dict(title='Altura (m)', range=[0, pe_direito+0.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=600, showlegend=False
    )
    st.plotly_chart(fig_3d, use_container_width=True)
