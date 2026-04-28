import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Inside Sales", layout="wide")

pd.options.mode.chained_assignment = None

st.markdown("""
<style>
.stButton>button {
    width: 100%;
    border-radius: 8px;
    background-color: #25D366;
    color: white;
    border: none;
    height: 3em;
    font-weight: bold;
}
.kanban-card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    margin-bottom: 10px;
    border-left: 5px solid #25D366;
}
</style>
""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

COLUNAS = [
    "Nome do Cliente",
    "Plataforma",
    "Telefone",
    "Status",
    "Última Interação",
    "Vendedor"
]

WORKSHEET = 0


# ---------------- LOGIN ----------------

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login CRM")

    email_input = st.text_input("E-mail corporativo:").strip().lower()

    if st.button("Entrar"):
        if email_input:
            st.session_state.vendedor_email = email_input
            st.session_state.vendedor_nome = (
                email_input.split("@")[0]
                .replace(".", " ")
                .title()
            )
            st.session_state.logado = True
            st.rerun()
        else:
            st.warning("Digite seu e-mail.")

    st.stop()


# ---------------- CARREGAR DADOS ----------------

try:
    df_origem = conn.read(
        spreadsheet=st.secrets["public_gsheets_url"],
        worksheet=0,
        ttl=0
    )

    if df_origem is None or df_origem.empty:
        df_origem = pd.DataFrame(columns=COLUNAS)

    for coluna in COLUNAS:
        if coluna not in df_origem.columns:
            df_origem[coluna] = ""

    df_origem = df_origem[COLUNAS].fillna("")

except Exception as e:
    st.error(f"Erro ao ler planilha: {e}")
    st.stop()


df_kanban = df_origem.copy()

meus_leads = df_kanban[
    df_kanban["Vendedor"].astype(str).str.lower().str.strip()
    == st.session_state.vendedor_email
].copy()


# ---------------- SIDEBAR ----------------

st.sidebar.write(f"### Oi, {st.session_state.vendedor_nome}! 👋")

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

with st.sidebar.expander("➕ CADASTRAR NOVO LEAD", expanded=True):
    with st.form("form_novo_lead"):
        nome = st.text_input("Nome do Cliente")
        tel = st.text_input("Telefone")
        plat = st.selectbox(
            "Plataforma",
            ["Hyperflow", "WhatsApp 1", "WhatsApp 2"]
        )
        status_sel = st.selectbox("Status", ["Quente", "Morno", "Frio"])

        d = st.date_input("Data Interação", datetime.now())
        t = st.time_input("Hora", datetime.now())

        salvar = st.form_submit_button("SALVAR LEAD")

        if salvar:
            if nome.strip() and tel.strip():
                novo_lead = {
                    "Nome do Cliente": nome.strip(),
                    "Plataforma": plat,
                    "Telefone": str(tel).strip(),
                    "Status": status_sel,
                    "Última Interação": f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}",
                    "Vendedor": st.session_state.vendedor_email
                }

                df_novo = pd.DataFrame([novo_lead])
                df_para_salvar = pd.concat(
                    [df_origem, df_novo],
                    ignore_index=True
                )

                df_para_salvar = df_para_salvar[COLUNAS].fillna("")

                try:
                    conn.update(
                        spreadsheet=st.secrets["public_gsheets_url"],
                        worksheet=0,
                        data=df_para_salvar
                    )

                    st.success("✅ Lead salvo com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
            else:
                st.warning("Preencha Nome e Telefone.")


# ---------------- KANBAN ----------------

st.title("📋 Meus Follow-ups")

c1, c2, c3 = st.columns(3)


def render_card(row):
    nome_cliente = row.get("Nome do Cliente", "Sem Nome")
    plataforma = row.get("Plataforma", "-")
    ultima_interacao = row.get("Última Interação", "-")
    telefone = row.get("Telefone", "")

    t_clean = "".join(filter(str.isdigit, str(telefone)))

    with st.container():
        st.markdown(f"""
        <div class="kanban-card">
            <h4>{nome_cliente}</h4>
            <p>🚀 {plataforma}</p>
            <p>🕒 {ultima_interacao}</p>
            <p>📞 {telefone}</p>
        </div>
        """, unsafe_allow_html=True)

        if t_clean:
            st.link_button("💬 WhatsApp", f"https://wa.me/{t_clean}")
        else:
            st.warning("Telefone inválido.")


with c1:
    st.header("🔥 QUENTE")
    q = meus_leads[
        meus_leads["Status"].astype(str).str.lower().str.strip() == "quente"
    ]
    for _, r in q.iterrows():
        render_card(r)

with c2:
    st.header("🌤️ MORNO")
    m = meus_leads[
        meus_leads["Status"].astype(str).str.lower().str.strip() == "morno"
    ]
    for _, r in m.iterrows():
        render_card(r)

with c3:
    st.header("❄️ FRIO")
    f = meus_leads[
        meus_leads["Status"].astype(str).str.lower().str.strip() == "frio"
    ]
    for _, r in f.iterrows():
        render_card(r)
