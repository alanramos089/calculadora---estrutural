import streamlit as st
import numpy as np

# Configuração da página web
st.set_page_config(page_title="Calculadora Estrutural", layout="centered")
st.title("🏗️ Calculadora de Viga Contínua")
st.write("Altere os parâmetros na barra lateral para ver o comportamento da estrutura em tempo real.")

# --- BARRA LATERAL COM OS DADOS DE ENTRADA ---
st.sidebar.header("⚙️ Parâmetros da Estrutura")
L = st.sidebar.slider("Comprimento de cada vão (m)", min_value=2.0, max_value=12.0, value=5.0, step=0.5)
q_input = st.sidebar.slider("Carga Distribuída (kN/m)", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
q = q_input * 1000 # Converte para N/m

# Propriedades padrão do material (Aço W200x22.5 de exemplo)
E = 2.1e11       
I = 2.0e-5       

# --- ALGORITMO MATRICIAL (O Coração do Sistema) ---
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
Reacoes = np.dot(K_global, U_global) - F_global

# --- RENDERIZAÇÃO DOS RESULTADOS NA TELA ---
st.subheader("📊 Reações de Apoio nos Nós")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Apoio Esquerdo (Nó 0)", value=f"{Reacoes[0]/1000:.2f} kN")
with col2:
    st.metric(label="Apoio Central (Nó 1)", value=f"{Reacoes[2]/1000:.2f} kN")
with col3:
    st.metric(label="Apoio Direito (Nó 2)", value=f"{Reacoes[4]/1000:.2f} kN")

st.subheader("🔄 Rotações Calculadas (Radianos)")
st.text(f"Nó 0: {U_global[1]:.6f} rad | Nó 1: {U_global[3]:.6f} rad | Nó 2: {U_global[5]:.6f} rad")
