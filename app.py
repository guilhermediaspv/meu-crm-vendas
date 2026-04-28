import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização
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

# --- LEITURA TOTALMENTE INDEPENDENTE ---
try:
    # Lemos como DataFrame mas convertemos IMEDIATAMENTE para uma lista de dicionários
    # Isso desconecta o dado de qualquer "fatia" da memória
    raw_df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    dados_lista = raw_df.to_dict('records')
    
    # Criamos um DF novo apenas para exibição no Kanban
    df_exibicao = pd.DataFrame(dados_lista)
    df_exibicao.columns = [str(c).strip() for c in df_exibicao.columns]
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Filtro de Leads para o Kanban
if 'Vendedor' in df_exibicao.columns:
    df_exibicao['Vendedor'] = df_exibicao['Vendedor'].astype(str).str.strip().str.lower()
    meus_leads = df_exibicao[df_exibicao["Vendedor"] == st.session_state.vendedor_email].copy()
else:
    st.error("Coluna 'Vendedor' não encontrada.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_novo_lead", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone (55...)")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        data_string = f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

        if st.form_submit_button("Salvar"):
            if nome and tel:
                # Criamos o novo lead como um dicionário simples
                novo_lead = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": data_string,
                    "Vendedor": st.session_state.vendedor_email
                }
                
                # ADICIONAMOS À LISTA PURA (Sem Pandas aqui para não dar erro de slice)
                dados_lista.append(novo_lead)
                
                # Transformamos a lista final num DataFrame limpo apenas para o update
                df_para_salvar = pd.DataFrame(dados_lista)
                
                try:
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_para_salvar)
                    st.success("✅ Cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no Google Sheets: {e}")
            else:
                st.warning("Preencha Nome e Telefone.")

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
        t_limpo = "".join(filter(str.isdigit, str(row.get('Telefone', ''))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{t_limpo}")
        st.write("")

def filtrar(s):
    return meus_leads[meus_leads["Status"].astype(str).str.strip().str.lower() == s.lower()]

with col_q:
    st.markdown("### 🔥 QUENTE")
    for _, r in filtrar("Quente").iterrows(): render_card(r)

with col_m:
    st.markdown("### 🌤️ MORNO")
    for _, r in filtrar("Morno").iterrows(): render_card(r)

with col_f:
    st.markdown("### ❄️ FRIO")
    for _, r in filtrar("Frio").iterrows(): render_card(r)
