import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página para ocupar a largura total
st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização CSS para o Front-end (Cards e Botões)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; }
    .kanban-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #25D366;
    }
    </style>
    """, unsafe_allow_html=True)

# Conexão com o Google Sheets usando a URL dos Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- BARRA LATERAL (LOGIN E CADASTRO) ---
st.sidebar.title("🚀 CRM Vendedor")
email_vendedor = st.sidebar.text_input("Introduza o seu e-mail para aceder")

if not email_vendedor:
    st.info("Aguardando login...")
    st.stop()

# Lendo os dados da planilha (usando o link guardado nos Secrets)
try:
    df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
except Exception as e:
    st.error("Erro ao conectar à planilha. Verifique se o link nos 'Secrets' está correto.")
    st.stop()

# Filtro de Privacidade: O vendedor só vê os leads dele
meus_leads = df[df["Vendedor"] == email_vendedor]

# --- FORMULÁRIO DE NOVO LEAD ---
with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=False):
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone (ex: 11999999999)")
        plat = st.selectbox("Plataforma", ["Instagram", "WhatsApp", "Google", "Indicação"])
        status = st.selectbox("Status", ["QUENTE", "MORNO", "FRIO"])
        
        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                nova_linha = pd.DataFrame([{
                    "Nome do Cliente": nome,
                    "Telefone": tel,
                    "Plataforma": plat,
                    "Status": status,
                    "Vendedor": email_vendedor,
                    "Ultima Interação": datetime.now().strftime('%d/%m/%Y %H:%M')
                }])
                # Atualiza a planilha
                updated_df = pd.concat([df, nova_linha], ignore_index=True)
                conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=updated_df)
                st.sidebar.success("Lead salvo!")
                st.rerun()
            else:
                st.sidebar.error("Preencha Nome e Telefone!")

# --- CORPO PRINCIPAL (KANBAN) ---
st.title(f"📋 Fluxo de Leads: {email_vendedor}")

col_quente, col_morno, col_frio = st.columns(3)

def render_card(row):
    # Formata o número para o link do WhatsApp (remove caracteres especiais)
    numero_limpo = str(row['Telefone']).replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    link_wa = f"https://wa.me/55{numero_limpo}"
    
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h3 style="margin-bottom:0;">{row['Nome do Cliente']}</h3>
                <p style="color:gray; font-size:0.9em;">📍 {row['Plataforma']}<br>📅 {row['Ultima Interação']}</p>
            </div>
        """, unsafe_allow_html=True)
        st.link_button(f"💬 Chamar no WhatsApp", link_wa)
        st.write("") # Espaçador

with col_quente:
    st.markdown("### 🔥 QUENTE")
    leads_q = meus_leads[meus_leads["Status"] == "QUENTE"]
    for _, row in leads_q.iterrows():
        render_card(row)

with col_morno:
    st.markdown("### 🌤️ MORNO")
    leads_m = meus_leads[meus_leads["Status"] == "MORNO"]
    for _, row in leads_m.iterrows():
        render_card(row)

with col_frio:
    st.markdown("### ❄️ FRIO")
    leads_f = meus_leads[meus_leads["Status"] == "FRIO"]
    for _, row in leads_f.iterrows():
        render_card(row)
