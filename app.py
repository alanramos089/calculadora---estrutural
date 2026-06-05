import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Configuração da página web
st.set_page_config(page_title="Calculadora Estrutural 3D", layout="wide")
st.title("🏗️ Software de Engenharia e Quantitativos v3.0")
st.write("Insira os parâmetros da obra e clique em Calcular para gerar os diagramas, quantitativos e o modelo 3D.")

# Inicializa a lista de cômodos na sessão se não existir
if 'comodos' not in st.session_state:
    st.session_state.comodos = [
        {"nome": "Quarto 1", "largura": 3.20, "comprimento": 3.00, "carga": 1.5}
    ]

# --- BARRA LATERAL: ENVELOPADA EM FORMULÁRIO DE CÁLCULO ---
st.sidebar.header("⚙️ Configurações Globais")

# Criamos o formulário para travar o recarregamento automático
with st.sidebar.form("configuracoes_obra_form"):
    espessura_parede = st.slider("Espessura da parede/viga (m)", min_value=0.10, max_value=0.25, value=0.10, step=0.05)
    pe_direito = st.slider("Altura do Pé-Direito (m)", min_value=2.40, max_value=4.00, value=2.80, step=0.10)
    espessura_laje = st.slider("Espessura da Laje (m)", min_value=0.08, max_value=0.20, value=0.10, step=0.01)
    
    st.markdown("---")
    st.markdown("### 🚪 Novo Cômodo rápido")
    nome_c = st.text_input("Nome do Cômodo", value="Sala")
    larg_c = st.number_input("Largura (m)", min_value=1.0, max_value=15.0, value=4.0, step=0.1)
    comp_c = st.number_input("Comprimento (m)", min_value=1.0, max_value=15.0, value=3.5, step=0.1)
    tipo_carga = st.selectbox("Tipo de Uso (Carga Normativa)", ["Residencial (1.5 kN/m²)", "Comercial (3.0 kN/m²)", "Banheiro/Serviço (2.0 kN/m²)"])
    
    # Botão de disparo principal
    botao_calcular = st.form_submit_button("🚀 CALCULAR ESTRUTURA")

# Lógica para adicionar o cômodo temporário se o botão for clicado
if botao_calcular:
    carga_val = 1.5 if "Residencial" in tipo_carga else (3.0 if "Comercial" in tipo_carga else 2.0)
    # Evita duplicar o cômodo padrão inicial se o usuário estiver apenas mudando as configurações globais
    if not any(c['nome'] == nome_c and c['largura'] == larg_c for c in st.session_state.comodos):
        st.session_state.comodos.append({"nome": nome_c, "largura": larg_c, "comprimento": comp_c, "carga": carga_val})

# Botão externo para resetar a lista de cômodos se necessário
if st.sidebar.button("🧹 Limpar Todos os Cômodos"):
    st.session_state.comodos = []
    st.rerun()

# Se não houver cômodos, interrompe
if not st.session_state.comodos:
    st.warning("Adicione pelo menos um cômodo na barra lateral para iniciar o dimensionamento.")
    st.stop()

# --- CÁLCULO ACUMULADO DOS CÔMODOS ---
total_area_laje = 0.0
total_perimetro_vigas = 0.0
volume_concreto_pilares = 0.0
forma_pilares_total = 0.0

comodo_foco = st.session_state.comodos[-1] # Foca sempre no último cômodo calculado/adicionado
L_viga = comodo_foco["largura"]
C_viga = comodo_foco["comprimento"]
q_base = comodo_foco["carga"]

for c in st.session_state.comodos:
    area = c["largura"] * c["comprimento"]
    perimetro = 2 * (c["largura"] + c["comprimento"])
    total_area_laje += area
    total_perimetro_vigas += perimetro
    
    vol_pilar_unitario = espessura_parede * 0.20 * pe_direito
    volume_concreto_pilares += (vol_pilar_unitario * 4)
    
    forma_pilar_unitario = (2 * (espessura_parede + 0.20)) * pe_direito
    forma_pilares_total += (forma_pilar_unitario * 4)

h_viga = 0.40 
vol_concreto_laje = total_area_laje * espessura_laje
vol_concreto_vigas = total_perimetro_vigas * espessura_parede * h_viga
vol_concreto_total = vol_concreto_laje + vol_concreto_vigas + volume_concreto_pilares

forma_laje_total = total_area_laje
forma_vigas_total = total_perimetro_vigas * (h_viga * 2)
forma_total_madeira = forma_laje_total + forma_vigas_total + forma_pilares_total

# --- MOTOR DO ALGORITMO MATRICIAL ---
E = 2.1e11       
I = (espessura_parede * (h_viga**3)) / 12       
q_linear = (q_base * (C_viga / 2)) * 1000 

def criar_matriz_rigidez_elemento(E, I, L):
    return (E * I) / (L**3) * np.array([
        [12, 6*L, -12, 6*L], [6*L, 4*L**2, -6*L, 2*L**2],
        [-12, -6*L, 12, -6*L], [6*L, 2*L**2, -6*L, 4*L**2]
    ])

def vetor_carga_equivalente(q, L):
    return np.array([(q * L)/2, (q * L**2)/12, (q * L)/2, -(q * L**2)/12])

K_global = np.zeros((6, 6))
F_global = np.zeros(6)
nos_elementos = [,(1,2)]
L_elemento = L_viga / 2 

for el, nos in enumerate(nos_elementos):
    n1, n2 = nos
    gdl_el = [2*n1, 2*n1+1, 2*n2, 2*n2+1]
    k_local = criar_matriz_rigidez_elemento(E, I, L_elemento)
    f_local = vetor_carga_equivalente(q_linear, L_elemento)
    for i in range(4):
        F_global[gdl_el[i]] += f_local[i]
        for j in range(4):
            K_global[gdl_el[i], gdl_el[j]] += k_local[i, j]

gdl_restritos = [0, 2, 4]
gdl_livres = [1, 3, 5]
K_livre = K_global[np.ix_(gdl_livres, gdl_livres)]
F_livre = F_global[gdl_livres]
deslocamentos_livres = np.linalg.solve(K_livre, F_livre)
U_global = np.zeros(6)
U_global[gdl_livres] = deslocamentos_livres
Reacoes = -(np.dot(K_global, U_global) - F_global)

# --- LAYOUT DE INTERFACE ---
tabs = st.tabs(["📊 Visão Geral e Materiais", "🧱 Modelo Estrutural 3D", "📈 Gráficos de Esforços"])

with tabs[0]:
    st.subheader("📋 Resumo do Imóvel Planejado")
    st.dataframe(st.session_state.comodos, use_container_width=True)
    
    st.subheader("🛒 Lista Estimada de Materiais (Orçamento)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Total de Concreto C25/C30", value=f"{vol_concreto_total:.2f} m³")
        st.caption(f"Laje: {vol_concreto_laje:.2f}m³ | Vigas: {vol_concreto_vigas:.2f}m³ | Pilares: {volume_concreto_pilares:.2f}m³")
    with col2:
        st.metric(label="Área de Fôrmas de Madeira", value=f"{forma_total_madeira:.2f} m²")
        st.caption(f"Laje: {forma_laje_total:.2f}m² | Vigas: {forma_vigas_total:.2f}m² | Pilares: {forma_pilares_total:.2f}m²")
    with col3:
        escoras_estimadas = int(np.ceil(forma_laje_total * 1.2))
        st.metric(label="Quantidade de Escoras Metálicas/Madeira", value=f"{escoras_estimadas} unid")
        st.caption("Estimativa de escoramento para segurança da cura da laje")

with tabs[1]:
    st.subheader(f"📦 Maquete Estrutural 3D Interativa: {comodo_foco['nome']}")
    fig_3d = go.Figure()
    cantos_x = [0, L_viga, 0, L_viga]
    cantos_y = [0, 0, C_viga, C_viga]
    
    for cx, cy in zip(cantos_x, cantos_y):
        fig_3d.add_trace(go.Scatter3d(
            x=[cx, cx], y=[cy, cy], z=[0, pe_direito],
            mode='lines', line=dict(color='gray', width=12)
        ))
        
    vigas_coords = [
        ([0, L_viga], [0, 0]), ([0, L_viga], [C_viga, C_viga]),
        ([0, 0], [0, C_viga]), ([L_viga, L_viga], [0, C_viga])
    ]
    for vx, vy in vigas_coords:
        fig_3d.add_trace(go.Scatter3d(
            x=vx, y=vy, z=[pe_direito, pe_direito],
            mode='lines', line=dict(color='darkred', width=8)
        ))
        
    lx = [0, L_viga, L_viga, 0]
    ly = [0, 0, C_viga, C_viga]
    lz = [pe_direito, pe_direito, pe_direito, pe_direito]
    
    fig_3d.add_trace(go.Mesh3d(x=lx, y=ly, z=lz, color='lightblue', opacity=0.5))
    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title='Largura (m)', range=[-0.5, L_viga+1]),
            yaxis=dict(title='Comprimento (m)', range=[-0.5, C_viga+1]),
            zaxis=dict(title='Altura (m)', range=[0, pe_direito+0.5]),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0), showlegend=False, height=500
    )
    st.plotly_chart(fig_3d, use_container_width=True)

with tabs[2]:
    st.subheader(f"📈 Análise de Esforços da Viga Principal ({comodo_foco['nome']})")
    x_total = np.linspace(0, L_viga, 200)
    momento_y = []
    cortante_y = []
    
    for x in x_total:
        if x <= L_elemento:
            R_esq = Reacoes[0]
            M = R_esq * x - (q_linear * x**2) / 2
            V = R_esq - q_linear * x
        else:
            R_dir = Reacoes[4]
            dist_dir = L_viga - x
            M = R_dir * dist_dir - (q_linear * dist_dir**2) / 2
            V = -(R_dir - q_linear * dist_dir)
        momento_y.append(M / 1000)
        cortante_y.append(V / 1000)
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5))
    ax1.plot(x_total, momento_y, color="red", linewidth=2)
    ax1.fill_between(x_total, momento_y, color="red", alpha=0.1)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_title("Diagrama de Momento Fletor (kN.m) - Tração para Baixo")
    ax1.invert_yaxis()
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    ax2.plot(x_total, cortante_y, color="blue", linewidth=2)
    ax2.fill_between(x_total, cortante_y, color="blue", alpha=0.1)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_title("Diagrama de Esforço Cortante (kN)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    st.pyplot(fig)
