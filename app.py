import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilo visual para o Kanban
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #25D366; color: white; border: none; height: 3em; }
    .kanban-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; border-left: 5px solid #25D366; }
    </style>
    """, unsafe_allow_html=True)

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SISTEMA DE LOGIN ---
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

# --- CARREGAMENTO DE DADOS (LEITURA APENAS) ---
# Usamos o .copy() para garantir que o que lemos não está "preso" à planilha
df_view = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0).copy()

# Filtro para o Kanban
if 'Vendedor' in df_view.columns:
    meus_leads = df_view[df_view['Vendedor'].astype(str).str.lower() == st.session_state.vendedor_email].copy()
else:
    st.error("Erro: Coluna 'Vendedor' não encontrada na planilha.")
    st.stop()

# --- SIDEBAR (CADASTRO) ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_vendas_direto"):
        nome = st.text_input("Nome")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        
        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                # ESTRATÉGIA NOVA: Criamos um DataFrame minúsculo de 1 linha
                # Sem tentar ler ou concatenar com o banco antigo
                novo_lead_df = pd.DataFrame([{
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }])
                
                try:
                    # USAMOS O COMANDO DE APPEND (ACRESCENTAR)
                    # O segredo: Pegamos o DF original (df_view) e apenas adicionamos a linha nova
                    # Sem fazer filtros ou manipulações antes do update
                    df_atualizado = pd.concat([df_view, novo_lead_df], ignore_index=True)
                    
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_atualizado)
                    
                    st.success("✅ Cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha Nome e Telefone.")

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
    subset_q = meus_leads[meus_leads["Status"].str.lower() == "quente"]
    for _, r in subset_q.iterrows(): card(r)

with c2:
    st.header("🌤️ MORNO")
    subset_m = meus_leads[meus_leads["Status"].str.lower() == "morno"]
    for _, r in subset_m.iterrows(): card(r)

with c3:
    st.header("❄️ FRIO")
    subset_f = meus_leads[meus_leads["Status"].str.lower() == "frio"]
    for _, r in subset_f.iterrows(): card(r)
