import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

# Estilização básica
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
    email_input = st.text_input("E-mail corporativo:")
    if st.button("Entrar"):
        if email_input:
            st.session_state.vendedor_email = email_input.strip().lower()
            st.session_state.vendedor_nome = email_input.split('@')[0].replace('.', ' ').title()
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- LEITURA (MÉTODO LIMPO) ---
try:
    # Lemos os dados brutos e convertemos para uma lista de dicionários imediatamente
    # Isso mata qualquer vínculo com "slices" do Pandas
    data_df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
    lista_leads = data_df.to_dict(orient='records')
    
    # Criamos um DataFrame novo apenas para o filtro do Kanban
    df_kanban = pd.DataFrame(lista_leads)
    df_kanban.columns = [str(c).strip() for c in df_kanban.columns]
except Exception as e:
    st.error(f"Erro ao carregar planilha: {e}")
    st.stop()

# Filtro de Leads
if 'Vendedor' in df_kanban.columns:
    df_kanban['Vendedor'] = df_kanban['Vendedor'].astype(str).str.lower().str.strip()
    meus_leads = df_kanban[df_kanban["Vendedor"] == st.session_state.vendedor_email]
else:
    st.error("Coluna 'Vendedor' não encontrada.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_vendas", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone")
        plat = st.selectbox("Plataforma", ["Hyperflow", "Whatsapp"])
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])
        d = st.date_input("Data", datetime.now())
        t = st.time_input("Hora", datetime.now())
        data_string = f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"

        if st.form_submit_button("Salvar"):
            if nome and tel:
                # Criamos o novo registro
                novo_registro = {
                    "Nome do Cliente": nome,
                    "Plataforma": plat,
                    "Telefone": str(tel),
                    "Status": status_sel,
                    "Última Interação": data_string,
                    "Vendedor": st.session_state.vendedor_email
                }
                
                # ADICIONAR À LISTA E RECONSTRUIR O DATAFRAME DO ZERO
                # Esta é a única forma de garantir que o Pandas não reclame de "Slice"
                lista_leads.append(novo_registro)
                df_final = pd.DataFrame(lista_leads)
                
                # Forçar a limpeza de qualquer coluna fantasma antes de salvar
                df_final = df_final[["Nome do Cliente", "Plataforma", "Telefone", "Status", "Última Interação", "Vendedor"]]
                
                try:
                    # O segredo: usamos o df_final que foi recém-criado, sem metadados antigos
                    conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df_final)
                    st.success("✅ Salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha Nome e Telefone.")

# --- KANBAN ---
st.title("📋 Meus Follow-ups")
c1, c2, c3 = st.columns(3)

def render_card(row):
    with st.container():
        st.markdown(f"""
            <div class="kanban-card">
                <h4 style="margin:0;">{row.get('Nome do Cliente', 'N/A')}</h4>
                <p style="margin:5px 0; color:#666; font-size:0.85em;">
                    🚀 {row.get('Plataforma', '-')} | 🕒 {row.get('Última Interação', '-')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        t_clean = "".join(filter(str.isdigit, str(row.get('Telefone', ''))))
        st.link_button("💬 WhatsApp", f"https://wa.me/{t_clean}")
        st.write("")

with c1:
    st.markdown("### 🔥 QUENTE")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "quente"].iterrows(): render_card(r)
with c2:
    st.markdown("### 🌤️ MORNO")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "morno"].iterrows(): render_card(r)
with c3:
    st.markdown("### ❄️ FRIO")
    for _, r in meus_leads[meus_leads["Status"].str.lower() == "frio"].iterrows(): render_card(r)
