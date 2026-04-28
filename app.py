import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# DESLIGA O AVISO DE CÓPIA DO PANDAS (O erro que está aparecendo)
pd.options.mode.chained_assignment = None 

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilo visual
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #25D366; color: white; border: none; height: 3em; }
    .kanban-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; border-left: 5px solid #25D366; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login CRM")
    email_input = st.text_input("E-mail corporativo:").strip().lower()
    if st.button("Entrar"):
        if email_input:
            st.session_state.vendedor_email = email_input
            st.session_state.vendedor_nome = email_input.split('@')[0].replace('.', ' ').title()
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- CARREGAMENTO DE DADOS (USANDO LISTAS PARA NÃO DAR ERRO) ---
try:
    # Lemos a planilha
    df_db = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    
    # Criamos uma cópia profunda e isolada
    df_limpo = pd.DataFrame(df_db.values, columns=df_db.columns).copy()
    
    # Filtramos apenas os leads do vendedor logado
    if 'Vendedor' in df_limpo.columns:
        meus_leads = df_limpo[df_limpo['Vendedor'].astype(str).str.lower() == st.session_state.vendedor_email].copy()
    else:
        st.error("Coluna 'Vendedor' não encontrada.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar: {e}")
    st.stop()

# --- SIDEBAR (CADASTRO) ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_final"):
        nome = st.text_input("Nome")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        
        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                # 1. Transformamos o banco atual em uma lista de dicionários (ISOLAMENTO TOTAL)
                banco_em_lista = df_limpo.to_dict('records')
                
                # 2. Criamos o novo registro
                novo = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }
                
                # 3. Adicionamos o novo lead à lista
                banco_em_lista.append(novo)
                
                # 4. Criamos um DataFrame NOVO do zero, sem metadados antigos
                df_final = pd.DataFrame(banco_em_lista)
                
                try:
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_final)
                    st.success("✅ Cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no Google: {e}")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")
c1, c2, c3 = st.columns(3)

def card(r):
    with st.container():
        st.markdown(f'<div class="kanban-card"><h4>{r.get("Nome do Cliente","")}</h4><p>🚀 {r.get("Plataforma","")} | 🕒 {r.get("Última Interação","")}</p></div>', unsafe_allow_html=True)
        num = "".join(filter(str.isdigit, str(r.get("Telefone",""))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{num}")

with c1:
    st.header("🔥 QUENTE")
    subset = meus_leads[meus_leads["Status"].str.lower() == "quente"]
    for _, r in subset.iterrows(): card(r)
with c2:
    st.header("🌤️ MORNO")
    subset = meus_leads[meus_leads["Status"].str.lower() == "morno"]
    for _, r in subset.iterrows(): card(r)
with c3:
    st.header("❄️ FRIO")
    subset = meus_leads[meus_leads["Status"].str.lower() == "frio"]
    for _, r in subset.iterrows(): card(r)
