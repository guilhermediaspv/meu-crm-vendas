import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN ---
st.sidebar.title("🚀 CRM Vendedor")
email_vendedor = st.sidebar.text_input("Seu e-mail")

if not email_vendedor:
    st.info("Digite seu e-mail para acessar seus leads.")
    st.stop()

# Lendo os dados (ttl=0 garante que atualiza na hora)
df = conn.read(ttl=0)

# Filtro de privacidade: só vê o que é dele
meus_leads = df[df["Vendedor"] == email_vendedor]

# --- CADASTRO ---
with st.sidebar.expander("➕ CADASTRAR LEAD"):
    with st.form("novo_lead", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("WhatsApp (ex: 11999999999)")
        plat = st.selectbox("Plataforma", ["Instagram", "WhatsApp", "Indicação", "Google"])
        status = st.selectbox("Status", ["QUENTE", "MORNO", "FRIO"])
        if st.form_submit_button("Salvar"):
            nova_linha = pd.DataFrame([{
                "Nome do Cliente": nome, "Telefone": tel, "Plataforma": plat,
                "Status": status, "Vendedor": email_vendedor, 
                "Ultima Interação": datetime.now().strftime('%d/%m/%Y %H:%M')
            }])
            updated_df = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(data=updated_df)
            st.toast("Cadastrado!")
            st.rerun()

# --- FRONT-END (KANBAN) ---
st.title(f"Fluxo de Leads - {email_vendedor}")
col1, col2, col3 = st.columns(3)

def render_card(row):
    with st.container(border=True):
        st.subheader(row["Nome do Cliente"])
        st.write(f"📍 {row['Plataforma']}")
        link_wa = f"https://wa.me/55{row['Telefone']}"
        st.link_button("💬 WhatsApp", link_wa)

with col1:
    st.header("🔥 QUENTE")
    for _, row in meus_leads[meus_leads["Status"] == "QUENTE"].iterrows():
        render_card(row)

with col2:
    st.header("🌤️ MORNO")
    for _, row in meus_leads[meus_leads["Status"] == "MORNO"].iterrows():
        render_card(row)

with col3:
    st.header("❄️ FRIO")
    for _, row in meus_leads[meus_leads["Status"] == "FRIO"].iterrows():
        render_card(row)
