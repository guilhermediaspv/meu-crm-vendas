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
    .stButton>button:hover { background-color: #128C7E; color: white; }
    .kanban-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        border-left: 5px solid #25D366;
    }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONTROLE DE SESSÃO (LOGIN) ---
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
        else:
            st.error("Insira seu e-mail.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
try:
    # ttl=0 para garantir dados sempre frescos
    df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    # Limpa nomes de colunas (remove espaços extras)
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    st.error(f"Erro ao conectar na planilha: {e}")
    st.stop()

# Filtro de Leads do Vendedor
# Nota: A coluna na planilha deve se chamar exatamente 'Vendedor'
if 'Vendedor' in df.columns:
    meus_leads = df[df["Vendedor"].str.lower() == st.session_state.vendedor_email]
else:
    st.error("Coluna 'Vendedor' não encontrada na planilha.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

st.sidebar.divider()

# --- FORMULÁRIO DE CADASTRO ---
with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("novo_lead", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone (55...)")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        
        # Data e Hora editáveis
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        data_string = f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

        if st.form_submit_button("Salvar na Planilha"):
            if nome and tel:
                # Criamos a linha garantindo os nomes das colunas da SUA planilha
                # Importante: O nome das chaves abaixo deve ser IGUAL ao topo da sua planilha
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
                
                try:
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=updated_df)
                    st.success("Salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar. Verifique se os nomes das colunas na planilha estão idênticos aos do código.")
            else:
                st.warning("Preencha os campos obrigatórios.")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")

col_q, col_m, col_f = st.columns(3)
