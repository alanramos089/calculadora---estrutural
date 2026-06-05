import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuração da página web
st.set_page_config(page_title="Calculadora Estrutural Avançada", layout="wide")
st.title("🏗️ Software de Análise de Vigas Contínuas v2.0")
st.write("Mude os parâmetros na barra lateral e veja os diagramas estruturais atualizados instantaneamente.")

# --- BARRA LATERAL COM OS DADOS DE ENTRADA ---
st.sidebar.header("⚙️ Parâmetros da Estrutura")
L = st.sidebar.slider("Comprimento de cada vão (m)", min_value=2.0, max_value=12.0, value=5.0, step=0.5)
q_input = st.sidebar.slider("Carga Distribuída (kN/m)", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
q = q_input * 1000 # Converte para N/m

# Propriedades padrão do material (Aço W200x22.5 de exemplo)
E = 2.1e11       
I = 2.0e-5       

# --- ALGORITMO MATRICIAL ---
def criar_matriz_rigidez_elemento(E, I, L):
    k = (E * I) / (L**3) * np.array([
        [12,      6*L,     -12,     6*L],
        [6*L,     4*L**2,  -6*L,    2*L**2],
        [-12,    -6*L,      12,    -6*L],
        [6*L,     2*L**2,  -6*L,    4*L**2]
    ])
    return k

def vetor_carga_equivalente(q, L):
    return np.array([(q * L)/2, (q * L**2)/12, (q * L)/2, -(q * L**2)/12])

# Montagem do Sistema Global (2 vãos, 3 nós)
nos_elementos = [[0, 1], [1, 2]]
num_gdl = 6
K_global = np.zeros((num_gdl, num_gdl))
F_global = np.zeros(num_gdl)

for el, nos in enumerate(nos_elementos):
    n1, n2 = nos
    gdl_el = [2*n1, 2*n1+1, 2*n2, 2*n2+1]
    k_local = criar_matriz_rigidez_elemento(E, I, L)
    f_local = vetor_carga_equivalente(q, L)
    for i in range(4):
        F_global[gdl_el[i]] += f_local[i]
        for j in range(4):
            K_global[gdl_el[i], gdl_el[j]] += k_local[i, j]

# Condições de contorno (Apoios verticais travados nos nós 0, 1, 2)
gdl_restritos = [0, 2, 4]
gdl_livres = [1, 3, 5]

K_livre = K_global[np.ix_(gdl_livres, gdl_livres)]
F_livre = F_global[gdl_livres]
deslocamentos_livres = np.linalg.solve(K_livre, F_livre)

U_global = np.zeros(num_gdl)
U_global[gdl_livres] = deslocamentos_livres

# Reações corrigidas para convenção positiva para cima (Engenharia)
Reacoes = -(np.dot(K_global, U_global) - F_global)

# --- CORPO PRINCIPAL DO LAYOUT ---
col_dados, col_graficos = st.columns([1, 2])

with col_dados:
    st.subheader("📊 Reações de Apoio")
    st.metric(label="Apoio Esquerdo (Nó 0)", value=f"{Reacoes[0]/1000:.2f} kN")
    st.metric(label="Apoio Central (Nó 1)", value=f"{Reacoes[2]/1000:.2f} kN")
    st.metric(label="Apoio Direito (Nó 2)", value=f"{Reacoes[4]/1000:.2f} kN")
    
    st.subheader("🔄 Rotações nos Nós")
    st.caption(f"**Nó 0:** {U_global[1]:.5f} rad")
    st.caption(f"**Nó 1:** {U_global[3]:.5f} rad")
    st.caption(f"**Nó 2:** {U_global[5]:.5f} rad")

with col_graficos:
    st.subheader("📈 Diagramas Estruturais")
    
    # Processamento dos pontos internos dos diagramas para suavidade do gráfico
    x_total = np.linspace(0, 2*L, 200)
    momento_y = []
    cortante_y = []
    
    # Momento no apoio central por engastamento
    M_central = -(q * L**2) / 8
    
    for x in x_total:
        if x <= L:
            # Primeiro Vão
            R_esq = Reacoes[0]
            v = x
            M = R_esq * v - (q * v**2) / 2
            V = R_esq - q * v
        else:
            # Segundo Vão
            R_dir = Reacoes[4]
            v = (2*L) - x
            M = R_dir * v - (q * v**2) / 2
            V = -(R_dir - q * v)
        momento_y.append(M / 1000) # kN.m
        cortante_y.append(V / 1000)   # kN
        
    # Plotagem usando Matplotlib
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
    
    # Grafico 1: Momento Fletor (Convenção da engenharia civil: tração para baixo)
    ax1.plot(x_total, momento_y, color="red", linewidth=2, label="Momento Fletor")
    ax1.fill_between(x_total, momento_y, color="red", alpha=0.1)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_title("Diagrama de Momento Fletor (kN.m)")
    ax1.invert_yaxis() # Convenção de engenharia civil para momentos
    ax1.grid(True, linestyle="--", alpha=0.5)
    
    # Grafico 2: Esforço Cortante
    ax2.plot(x_total, cortante_y, color="blue", linewidth=2, label="Esforço Cortante")
    ax2.fill_between(x_total, cortante_y, color="blue", alpha=0.1)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_title("Diagrama de Esforço Cortante (kN)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    st.pyplot(fig)
