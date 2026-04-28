import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configuração Inicial e Desativação de alertas do Pandas
st.set_page_config(page_title="CRM Inside Sales", layout="wide")
pd.options.mode.chained_assignment = None 

# Estilização
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #25D366; color: white; border: none; height: 3em; font-weight: bold; }
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

# --- CARREGAMENTO DOS DADOS ---
# Lemos a planilha e convertemos para lista de dicionários para "desgrudar" do Pandas
try:
    df_origem = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    # Criamos uma cópia em lista para o processo de salvamento
    lista_leads_geral = df_origem.to_dict(orient='records')
    # Criamos um DataFrame limpo apenas para mostrar no Kanban
    df_kanban = pd.DataFrame(lista_leads_geral)
except Exception as e:
    st.error(f"Erro ao ler planilha: {e}")
    st.stop()

# Filtro de Leads do Vendedor
if not df_kanban.empty and 'Vendedor' in df_kanban.columns:
    meus_leads = df_kanban[df_kanban['Vendedor'].astype(str).str.lower() == st.session_state.vendedor_email].copy()
else:
    meus_leads = pd.DataFrame()

# --- SIDEBAR (CADASTRO) ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_venda_final"):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data Interação", datetime.now())
        t = st.time_input("Hora", datetime.now())
        
        if st.form_submit_button("SALVAR LEAD"):
            if nome and tel:
                # 1. Criar o novo lead em formato de dicionário
                novo_lead_dic = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }
                
                # 2. Adicionar à lista que já tínhamos na memória
                lista_leads_geral.append(novo_lead_dic)
                
                # 3. Gerar um DataFrame NOVO do zero (sem conexões antigas)
                df_para_salvar = pd.DataFrame(lista_leads_geral)
                
                # 4. Forçar a ordem das colunas para bater com a planilha
                colunas = ["Nome do Cliente", "Plataforma", "Telefone", "Status", "Última Interação", "Vendedor"]
                df_para_salvar = df_para_salvar[colunas]
                
                try:
                    # USAMOS CREATE PARA FORÇAR A SOBREPOSIÇÃO LIMPA
                    conn.create(spreadsheet=st.secrets["public_gsheets_url"], data=df_para_salvar)
                    st.success("✅ Lead salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha Nome e Telefone!")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")
c1, c2, c3 = st.columns(3)

def render_card(row):
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h4>{row.get('Nome do Cliente', 'Sem Nome')}</h4>
                <p>🚀 {row.get('Plataforma', '-')} | 🕒 {row.get('Última Interação', '-')}</p>
            </div>
        """, unsafe_allow_html=True)
        t_clean = "".join(filter(str.isdigit, str(row.get('Telefone', ''))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{t_clean}")

with c1:
    st.header("🔥 QUENTE")
    if not meus_leads.empty:
        q = meus_leads[meus_leads["Status"].astype(str).str.lower() == "quente"]
        for _, r in q.iterrows(): render_card(r)

with c2:
    st.header("🌤️ MORNO")
    if not meus_leads.empty:
        m = meus_leads[meus_leads["Status"].astype(str).str.lower() == "morno"]
        for _, r in m.iterrows(): render_card(r)

with c3:
    st.header("❄️ FRIO")
    if not meus_leads.empty:
        f = meus_leads[meus_leads["Status"].astype(str).str.lower() == "frio"]
        for _, r in f.iterrows(): render_card(r)
