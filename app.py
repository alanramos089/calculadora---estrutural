import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v6.0")
st.write("Configurador de Planta Baixa 3D: União automática de módulos em série com quantitativos integrados.")

# Inicialização padrão baseada na prancha técnica (2 ambientes iniciais para mostrar a união)
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Sala Principal", "largura": 3.20, "comprimento": 4.00, "portas": 1, "janelas": 1},
        {"nome": "Dormitório", "largura": 3.20, "comprimento": 3.70, "portas": 1, "janelas": 1}
    ]

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Globais da Obra")

with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.sidebar.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    pe_direito = st.sidebar.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.sidebar.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🚪 Encaixar Próximo Módulo")
    nome_c = st.text_input("Nome do Ambiente", value="Banheiro")
    larg_c = st.number_input("Largura Interna (m)", min_value=1.0, max_value=15.0, value=3.20, step=0.1)
    comp_c = st.number_input("Comprimento Interno (m)", min_value=1.0, max_value=15.0, value=2.00, step=0.1)
    
    portas_c = st.number_input("Quantidade de Portas", min_value=0, max_value=4, value=1, step=1)
    janelas_c = st.number_input("Quantidade de Janelas", min_value=0, max_value=4, value=1, step=1)
    
    botao_calcular = st.form_submit_button("🧱 ENCAIXAR MÓDULO NA PLANTA")

if botao_calcular:
    st.session_state.comodos.append({
        "nome": nome_c, "largura": float(larg_c), "comprimento": float(comp_c), 
        "portas": int(portas_c), "janelas": int(janelas_c)
    })
    st.rerun()

# --- GERENCIADOR DE EXCLUSÃO ---
if st.session_state.comodos:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗑️ Remover Módulo da Planta")
    opcoes_exclusao = [f"{i} - {c['nome']} ({c['largura']}x{c['comprimento']})" for i, c in enumerate(st.session_state.comodos)]
    comodo_para_deletar = st.sidebar.selectbox("Selecione qual deseja remover", opcoes_exclusao)
    
    if st.sidebar.button("❌ Excluir Módulo Selecionado"):
        idx_deletar = int(comodo_para_deletar.split(" - "))
        st.session_state.comodos.pop(idx_deletar)
        st.toast("Módulo removido da planta!")
        st.rerun()

if st.sidebar.button("🧹 Limpar Planta Inteira"):
    st.session_state.comodos = []
    st.rerun()

if not st.session_state.comodos:
    st.warning("Adicione um módulo na barra lateral para montar a planta baixa.")
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
tab0, tab1 = st.tabs(["📊 Quantitativos Consolidados da Casa", "🧱 Planta Baixa Estrutural 3D"])

with tab0:
    st.subheader("📋 Sequência de Montagem dos Módulos")
    st.dataframe(st.session_state.comodos, use_container_width=True)
    
    st.subheader("🛒 Consumo Total de Materiais para Concretagem Monolítica")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Geral de Concreto", value=f"{concreto_global:.2f} m³")
        st.caption(f"Paredes: {total_concreto_paredes:.2f}m³ | Lajes: {total_concreto_lajes:.2f}m³")
    with col2:
        st.metric(label="Área Geral de Fôrmas Modulares", value=f"{forma_global:.2f} m²")
        st.caption(f"Inclui dupla face das divisórias e fundos de laje")
    with col3:
        st.metric(label="Total de Tela Soldada Q092", value=f"{total_telas_aço:.2f} m²")
        st.caption(f"Malha calculada para cobrir todas as paredes fechadas")

with tab1:
    st.subheader("🧱 Modelo Estrutural da Planta Baixa Unificada")
    st.write("Abaixo, veja todos os módulos acoplados em série formando o corpo completo da edificação.")
    
    fig_3d = go.Figure()
    
    # Coordenador de deslocamento linear (acumulador de comprimento no eixo Y)
    deslocamento_y = 0.0
    max_largura_projeto = 0.0
    
    for c in st.session_state.comodos:
        w = c["largura"]
        h = c["comprimento"]
        nome = c["nome"]
        
        if w > max_largura_projeto:
            max_largura_projeto = w
            
        # Posições locais do bloco deslocadas pelo acumulador (deslocamento_y)
        # 1. Desenha o volume translúcido das paredes do módulo atual
        fig_3d.add_trace(go.Mesh3d(
            x=[0, w, w, 0, 0, w, w, 0],
            y=[deslocamento_y, deslocamento_y, deslocamento_y+h, deslocamento_y+h, deslocamento_y, deslocamento_y, deslocamento_y+h, deslocamento_y+h],
            z=[0, 0, 0, 0, pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(140, 145, 150)', opacity=0.6, flatshading=True, name=nome
        ))
        
        # 2. Desenha a laje de cobertura individual com beiral de 30cm
        beiral = 0.30
        fig_3d.add_trace(go.Mesh3d(
            x=[-beiral, w+beiral, w+beiral, -beiral],
            y=[deslocamento_y-beiral, deslocamento_y-beiral, deslocamento_y+h+beiral, deslocamento_y+h+beiral],
            z=[pe_direito, pe_direito, pe_direito, pe_direito],
            color='rgb(170, 175, 180)', opacity=0.85, name=f"Laje {nome}"
        ))
        
        # 3. Linhas pretas de contorno para destacar as divisões deste módulo
        linhas_modulo = [
            ([0, w, w, 0, 0], [deslocamento_y, deslocamento_y, deslocamento_y+h, deslocamento_y+h, deslocamento_y], [pe_direito]*5),
            ([0, 0], [deslocamento_y, deslocamento_y+h], [0, 0]),
            ([w, w], [deslocamento_y, deslocamento_y+h], [0, 0]),
            ([0, 0], [deslocamento_y, deslocamento_y], [0, pe_direito]),
            ([w, w], [deslocamento_y, deslocamento_y], [0, pe_direito]),
            ([0, 0], [deslocamento_y+h, deslocamento_y+h], [0, pe_direito]),
            ([w, w], [deslocamento_y+h, deslocamento_y+h], [0, pe_direito])
        ]
        for lx, ly, lz in linhas_modulo:
            fig_3d.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=3), showlegend=False))
            
        # 4. Texto identificador flutuando no centro de cada módulo
        fig_3d.add_trace(go.Scatter3d(
            x=[w/2], y=[deslocamento_y + h/2], z=[pe_direito + 0.4],
            mode="text", text=[nome], textfont=dict(color="cyan", size=12, family="Arial Black")
        ))
        
        # Avança o marcador para colar o próximo cômodo exatamente na frente deste
        deslocamento_y += h

    # 5. DIAGRAMA DIMENSIONAL GLOBAL (Cotas de limite total da casa em laranja)
    fig_3d.add_trace(go.Scatter3d(
        x=[max_largura_projeto/2], y=[-0.6], z=[0.1],
        mode="text", text=[f"LARGURA COMPATÍVEL = {max_largura_projeto:.2f} m"],
        textfont=dict(color="orange", size=13, family="Arial Black")
    ))
    fig_3d.add_trace(go.Scatter3d(
        x=[max_largura_projeto + 0.6], y=[deslocamento_y/2], z=[0.1],
        mode="text", text=[f"COMPRIMENTO TOTAL DA PLANTA = {deslocamento_y:.2f} m"],
        textfont=dict(color="orange", size=13, family="Arial Black")
    ))

    # Ajuste de escala e limites da cena baseados no tamanho total acumulado da casa
    fig_3d.update_layout(
        dragmode='orbit',
        scene=dict(
            xaxis=dict(title='Largura (m)', range=[-1, max_largura_projeto+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            yaxis=dict(title='Comprimento Total (m)', range=[-1, deslocamento_y+1.5], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            zaxis=dict(title='Altura (m)', range=[0, pe_direito+1.0], backgroundcolor="rgb(35, 35, 35)", gridcolor="gray"),
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.5)), aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=700, showlegend=False
    )
    st.plotly_chart(fig_3d, use_container_width=True)
