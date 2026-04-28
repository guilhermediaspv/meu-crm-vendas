import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização CSS para o Front-end e esconder elementos desnecessários
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #25D366; color: white; }
    .kanban-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #25D366;
    }
    /* Esconder o menu do Streamlit para parecer um app nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SISTEMA DE LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso ao CRM")
    email_input = st.text_input("Digite seu e-mail corporativo para entrar:")
    if st.button("Entrar"):
        if email_input:
            st.session_state.vendedor_email = email_input
            # Extrai o nome antes do @ para a saudação (ex: guilherme.dias)
            st.session_state.vendedor_nome = email_input.split('@')[0].replace('.', ' ').title()
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Por favor, insira um e-mail.")
    st.stop()

# --- APP LOGADO ---

# Lendo os dados da planilha
try:
    df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
except Exception as e:
    st.error("Erro ao ler a planilha. Verifique o link nos Secrets.")
    st.stop()

# Filtro de Leads (usando o nome exato da sua coluna: 'Vendedor')
meus_leads = df[df["Vendedor"] == st.session_state.vendedor_email]

# --- BARRA LATERAL ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

if st.sidebar.button("Sair / Trocar Conta"):
    st.session_state.logado = False
    st.rerun()

st.sidebar.divider()

# --- FORMULÁRIO DE CADASTRO ---
with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone (55...)")
        # Opções limitadas conforme pedido
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        
        # Data e Hora automática mas editável
        data_hoje = datetime.now().date()
        hora_agora = datetime.now().time()
        
        data_col, hora_col = st.columns(2)
        data_f = data_col.date_input("Data", data_hoje)
        hora_f = hora_col.time_input("Hora", hora_agora)
        
        # Junta data e hora para salvar
        data_final = f"{data_f.strftime('%d/%m/%Y')} {hora_f.strftime('%H:%M')}"

        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                # Criar nova linha (Certifique-se que os nomes das chaves são IGUAIS às colunas da planilha)
                nova_linha = pd.DataFrame([{
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": tel,
                    "Status": status,
                    "Última Interação": data_final,
                    "Vendedor": st.session_state.vendedor_email
                }])
                
                # Unir e atualizar
                updated_df = pd.concat([df, nova_linha], ignore_index=True)
                conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=updated_df)
                st.toast("Lead salvo com sucesso!")
                st.rerun()
            else:
                st.error("Preencha Nome e Telefone.")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")

col1, col2, col3 = st.columns(3)

def render_card(row):
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h3 style="margin:0; color:#1f1f1f;">{row['Nome do Cliente']}</h3>
                <p style="margin:5px 0; color:#666; font-size:0.9em;">
                    🚀 {row['Plataforma']}<br>
                    🕒 {row['Última Interação']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        # Limpa o telefone para o link
        numero = str(row['Telefone']).replace('.0', '').replace(' ', '').replace('+', '')
        st.link_button(f"💬 WhatsApp", f"https://wa.me/{numero}")
        st.write("")

# Mapeamento exato para bater com as colunas da sua planilha (case sensitive)
with col1:
    st.markdown("### 🔥 QUENTE")
    for _, row in meus_leads[meus_leads["Status"].str.capitalize() == "Quente"].iterrows():
        render_card(row)

with col2:
    st.markdown("### 🌤️ MORNO")
    for _, row in meus_leads[meus_leads["Status"].str.capitalize() == "Morno"].iterrows():
        render_card(row)

with col3:
    st.markdown("### ❄️ FRIO")
    for _, row in meus_leads[meus_leads["Status"].str.capitalize() == "Frio"].iterrows():
        render_card(row)
