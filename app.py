import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #25D366; color: white; border: none; height: 3em; }
    .kanban-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; border-left: 5px solid #25D366; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# LOGIN
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

# LEITURA
try:
    # Lemos a planilha e transformamos em uma LISTA PURA de Python imediatamente.
    # Isso desconecta o dado da planilha e mata o erro de "Slice".
    df_inicial = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    lista_de_dados = df_inicial.to_dict(orient='records')
except Exception as e:
    st.error(f"Erro na leitura: {e}")
    st.stop()

# SIDEBAR
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_novo"):
        nome = st.text_input("Nome")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        
        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                # CRIAMOS O NOVO DICIONÁRIO
                novo = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }
                
                # RECONSTRUÇÃO ATÔMICA:
                # Criamos uma nova lista, adicionamos o antigo + o novo.
                nova_lista_completa = lista_de_dados + [novo]
                
                # Transformamos em um DataFrame NOVO, do zero, sem NENHUM histórico.
                df_para_enviar = pd.DataFrame(nova_lista_completa)
                
                # Filtramos as colunas para garantir que não vá lixo
                cols = ["Nome do Cliente", "Plataforma", "Telefone", "Status", "Última Interação", "Vendedor"]
                df_para_enviar = df_para_enviar[cols]
                
                try:
                    # O comando UPDATE agora recebe um objeto que nunca viu a planilha antes
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_para_enviar)
                    st.success("✅ Salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# KANBAN (Usando a lista que já temos em memória)
st.title("📋 Meus Follow-ups")
df_kanban = pd.DataFrame(lista_de_dados)
if not df_kanban.empty:
    df_kanban['Vendedor'] = df_kanban['Vendedor'].astype(str).str.lower()
    meus_leads = df_kanban[df_kanban["Vendedor"] == st.session_state.vendedor_email]
else:
    meus_leads = pd.DataFrame()

c1, c2, c3 = st.columns(3)

def card(r):
    with st.container():
        st.markdown(f'<div class="kanban-card"><h4>{r.get("Nome do Cliente","")}</h4><p>🚀 {r.get("Plataforma","")} | 🕒 {r.get("Última Interação","")}</p></div>', unsafe_allow_html=True)
        num = "".join(filter(str.isdigit, str(r.get("Telefone",""))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{num}")

with c1:
    st.header("🔥 QUENTE")
    if not meus_leads.empty:
        for _, r in meus_leads[meus_leads["Status"].str.lower() == "quente"].iterrows(): card(r)
with c2:
    st.header("🌤️ MORNO")
    if not meus_leads.empty:
        for _, r in meus_leads[meus_leads["Status"].str.lower() == "morno"].iterrows(): card(r)
with c3:
    st.header("❄️ FRIO")
    if not meus_leads.empty:
        for _, r in meus_leads[meus_leads["Status"].str.lower() == "frio"].iterrows(): card(r)
