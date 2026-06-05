import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Concreto Modular", layout="wide")
st.title("🏗️ Sistema Construtivo: Concreto Modular Armado Monolítico v3.9")
st.write("Cálculo integrado com gerenciamento completo de cômodos e maquete 3D com rotação automatizada.")

# Inicializa a lista de cômodos na sessão se não existir
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Quarto 1", "largura": 3.20, "comprimento": 3.00, "portas": 1, "janelas": 1}
    ]

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Parâmetros Globais do Molde")

with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.slider("Espessura da Parede Maciça (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    pe_direito = st.slider("Altura da Parede / Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.slider("Espessura da Laje Superior (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🚪 Adicionar Novo Cômodo")
    nome_c = st.text_input("Nome do Cômodo", value="Sala")
    larg_c = st.number_input("Largura Interna (m)", min_value=1.0, max_value=15.0, value=4.00, step=0.1)
    comp_c = st.number_input("Comprimento Interno (m)", min_value=1.0, max_value=15.0, value=3.50, step=0.1)
    
    portas_c = st.number_input("Quantidade de Portas (0.80x2.10m)", min_value=0, max_value=4, value=1, step=1)
    janelas_c = st.number_input("Quantidade de Janelas (1.20x1.00m)", min_value=0, max_value=4, value=1, step=1)
    
    botao_calcular = st.form_submit_button("🚀 CALCULAR MÓDULO COM VÃOS")

if botao_calcular:
    st.session_state.comodos.append({
        "nome": nome_c, 
        "largura": float(larg_c), 
        "comprimento": float(comp_c), 
        "portas": int(portas_c), 
        "janelas": int(janelas_c)
    })
    st.rerun()

# --- GERENCIADOR DE EXCLUSÃO ---
if st.session_state.comodos:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗑️ Gerenciar / Excluir Cômodo")
    
    opcoes_exclusao = [f"{i} - {c['nome']} ({c['largura']}x{c['comprimento']})" for i, c in enumerate(st.session_state.comodos)]
    comodo_para_deletar = st.sidebar.selectbox("Selecione qual deseja remover", opcoes_exclusao)
    
    if st.sidebar.button("❌ Excluir Cômodo Selecionado"):
        idx_deletar = int(comodo_para_deletar.split(" - "))
        st.session_state.comodos.pop(idx_deletar)
        st.toast("Cômodo removido com sucesso!")
        st.rerun()

if st.sidebar.button("🧹 Limpar Toda a Obra"):
    st.session_state.comodos = []
    st.rerun()

if not st.session_state.comodos:
    st.warning("Adicione um cômodo na barra lateral para iniciar o processamento.")
    st.stop()

# --- CÁLCULOS VOLUMÉTRICOS ---
total_concreto_paredes = 0.0
total_concreto_lajes = 0.0
total_forma_paredes = 0.0
total_forma_lajes = 0.0
total_portas = 0
total_janelas = 0

comodo_foco = st.session_state.comodos[-1]
L = comodo_foco["largura"]
C = comodo_foco["comprimento"]

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

concreto_global = total_concreto_paredes + total_concreto_lajes
forma_global = total_forma_paredes + total_forma_lajes

# --- INTERFACE POR ABAS ---
tabs = st.tabs(["📊 Quantitativos Realistas", "🧱 Maquete 3D Prédio/Cômodo"])

with tabs:
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

with tabs:
    st.subheader(f"🧱 Paredes Sólidas Verticais Prontas: {comodo_foco['nome']}")
    st.write("Utilize os controles integrados no gráfico abaixo para rotacionar em 360° automaticamente.")
    
    fig_3d = go.Figure()
    
    # 8 pontos coordenados retificados (Paredes perfeitamente verticais)
    x_v = [0, L, L, 0,  0, L, L, 0]
    y_v = [0, 0, C, C,  0, 0, C, C]
    z_v = [0, 0, 0, 0,  pe_direito, pe_direito, pe_direito, pe_direito]
    
    # Mapeamento estrito para fechar os quadrantes verticais perfeitamente retos (Cubo)
    i_v = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 1, 2]
    j_v = [1, 4, 2, 5, 3, 6, 0, 7, 5, 7, 5, 6]
    k_v = [4, 5, 5, 6, 6, 7, 7, 4, 6, 6, 2, 3]
    
    # Desenha as paredes de concreto fechadas corretas
    fig_3d.add_trace(go.Mesh3d(
        x=x_v, y=y_v, z=z_v, i=i_v, j=j_v, k=k_v,
        color='rgb(135, 140, 145)', opacity=0.95, flatshading=True, name="Paredes"
    ))
    
    # Desenha a laje plana superior
    fig_3d.add_trace(go.Mesh3d(
        x=[0, L, L, 0], y=[0, 0, C, C], z=[pe_direito, pe_direito, pe_direito, pe_direito],
        color='rgb(165, 170, 175)', opacity=0.9, name="Laje"
    ))
    
    # Linhas estruturais pretas para dar nitidez visual nas quinas
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

    # --- IMPLEMENTAÇÃO DO GIRO COMPLETO AUTOMÁTICO (360 DEGREES ANIMAÇÃO) ---
    # Criando os quadros de animação descrevendo uma órbita circular estável ao redor do centro da casa
    frames = []
    lista_angulos = np.linspace(0, 2 * np.pi, 60) # 60 posições calculadas
    
    centro_x = L / 2
    centro_y = C / 2
    raio_camera = max(L, C) * 2 # Distância focal segura para não cortar o modelo
    
    for angulo in lista_angulos:
        cam_x = centro_x + raio_camera * np.cos(angulo)
        cam_y = centro_y + raio_camera * np.sin(angulo)
        
        frames.append(go.Frame(layout=dict(scene=dict(camera=dict(
            eye=dict(x=cam_x/raio_camera*1.8, y=cam_y/raio_camera*1.8, z=1.2),
            center=dict(x=0, y=0, z=-0.1)
        )))))
        
    fig_3d.frames = frames

    # Adicionando botões de controle de animação (Play/Pause) integrados dentro do painel
    fig_3d.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="▶️ ATIVAR GIRO 360°", method="animate", args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode="immediate")]),
                    dict(label="⏸️ PAUSAR", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ],
                direction="left", padding={"r": 10, "t": 10}, x=0.01, y=0.99
            )
        ]
    )

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
