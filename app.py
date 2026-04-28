import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #25D366; color: white; border: none; }
    .kanban-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        border-left: 5px solid #25D366;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login CRM")
    email_input = st.text_input("E-mail corporativo:")
    if st.button("Entrar"):
        if email_input:
            st.session_state.vendedor_email = email_input.strip().lower()
            st.session_state.vendedor_nome = email_input.split('@')[0].replace('.', ' ').title()
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- LEITURA DOS DADOS ---
try:
    df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    # Limpa nomes das colunas e remove linhas vazias
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(subset=['Nome do Cliente']) 
except Exception as e:
    st.error("Erro ao carregar dados. Verifique se a planilha tem os cabeçalhos corretos.")
    st.stop()

# Filtro de Leads (Garante que não falhe por causa de espaços ou maiúsculas no e-mail)
df['Vendedor'] = df['Vendedor'].astype(str).str.strip().str.lower()
meus_leads = df[df["Vendedor"] == st.session_state.vendedor_email]

# --- SIDEBAR ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("novo_lead", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone (55...)")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        data_string = f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

        if st.form_submit_button("Salvar"):
            if nome and tel:
                nova_data = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": tel,
                    "Status": status_sel,
                    "Última Interação": data_string,
                    "Vendedor": st.session_state.vendedor_email
                }
                new_row = pd.DataFrame([nova_data])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=updated_df)
                st.success("Salvo!")
                st.rerun()

# --- KANBAN ---
st.title("📋 Meus Follow-ups")
col_q, col_m, col_f = st.columns(3)

def render_card(row):
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h4 style="margin:0;">{row.get('Nome do Cliente', 'Sem Nome')}</h4>
                <p style="margin:5px 0; color:#666; font-size:0.85em;">
                    🚀 {row.get('Plataforma', '-')} | 🕒 {row.get('Última Interação', '-')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        t = str(row.get('Telefone', '')).split('.')[0].replace(' ', '').replace('+', '')
        st.link_button("💬 WhatsApp", f"https://wa.me/{t}")
        st.write("")

# Lógica para garantir que encontra o status independente de como foi escrito
with col_q:
    st.markdown("### 🔥 QUENTE")
    subset = meus_leads[meus_leads["Status"].astype(str).str.strip().str.lower() == "quente"]
    for _, r in subset.iterrows():
        render_card(r)

with col_m:
    st.markdown("### 🌤️ MORNO")
    subset = meus_leads[meus_leads["Status"].astype(str).str.strip().str.lower() == "morno"]
    for _, r in subset.iterrows():
        render_card(r)

with col_f:
    st.markdown("### ❄️ FRIO")
    subset = meus_leads[meus_leads["Status"].astype(str).str.strip().str.lower() == "frio"]
    for _, r in subset.iterrows():
        render_card(r)
