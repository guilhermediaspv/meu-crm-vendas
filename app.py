import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
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

# --- LEITURA (APENAS PARA O KANBAN) ---
try:
    # Lemos os dados e transformamos em uma lista simples de dicionários IMEDIATAMENTE
    # Isso garante que o Kanban não tenha NENHUMA ligação com a parte de salvamento
    data_raw = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    lista_leads = data_raw.to_dict(orient='records')
    df_kanban = pd.DataFrame(lista_leads)
    
    if 'Vendedor' in df_kanban.columns:
        df_kanban['Vendedor'] = df_kanban['Vendedor'].astype(str).str.lower()
        meus_leads = df_kanban[df_kanban["Vendedor"] == st.session_state.vendedor_email].copy()
    else:
        st.error("Coluna 'Vendedor' não encontrada.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar: {e}")
    st.stop()

# --- SIDEBAR (CADASTRO) ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_final_mesmo"):
        nome = st.text_input("Nome")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        
        if st.form_submit_button("Salvar Lead"):
            if nome and tel:
                # CRIAMOS UM DATAFRAME TOTALMENTE NOVO DE 1 LINHA
                # Ele não tem ligação com o df_kanban ou com a leitura inicial
                novo_lead = pd.DataFrame([{
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }])
                
                try:
                    # EM VEZ DE UPDATE, USAMOS UMA TÉCNICA DE RECONSTRUÇÃO LIMPA
                    # Pegamos a lista original, adicionamos o novo dicionário e sobrescrevemos tudo
                    # Isso evita que o Pandas tente "fatiar" (slice) os dados
                    full_data_list = lista_leads + novo_lead.to_dict(orient='records')
                    df_to_save = pd.DataFrame(full_data_list)
                    
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_to_save)
                    
                    st.success("✅ Cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")
c1, c2, c3 = st.columns(3)

def render_card(row):
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h4>{row.get('Nome do Cliente', 'N/A')}</h4>
                <p>🚀 {row.get('Plataforma', '-')} | 🕒 {row.get('Última Interação', '-')}</p>
            </div>
        """, unsafe_allow_html=True)
        t_clean = "".join(filter(str.isdigit, str(row.get('Telefone', ''))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{t_clean}")

with c1:
    st.header("🔥 QUENTE")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "quente"].iterrows(): render_card(r)
with c2:
    st.header("🌤️ MORNO")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "morno"].iterrows(): render_card(r)
with c3:
    st.header("❄️ FRIO")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "frio"].iterrows(): render_card(r)
