import streamlit as st
import random
import pandas as pd
import gspread
from google.oauth2 import service_account

# Configurações do Sheets
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_KEY = "1cvgcxvoZH24X5JPJ2SyRuhA7mt4C7VSvBq8gQdShLC8"
RESOURCE = st.secrets["gcp_service_account"]

@st.cache_resource
def get_sheet():
    creds = service_account.Credentials.from_service_account_info(RESOURCE, scopes=SCOPE)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_KEY)
    return sh

def carregar_dados():
    sh = get_sheet()
    ws_s = sh.worksheet("sorteados")
    ws_r = sh.worksheet("registros")
    nums = ws_s.col_values(1)[1:]  # ignora header
    registros = ws_r.get_all_records()
    sorteados = [int(n) for n in nums if n.strip()]
    return sorteados, registros

def salvar_sorteados(numeros):
    sh = get_sheet()
    ws = sh.worksheet("sorteados")
    rows = [[n] for n in numeros]
    ws.append_rows(rows, value_input_option="USER_ENTERED")

def salvar_registros(registros):
    sh = get_sheet()
    ws = sh.worksheet("registros")
    rows = [[rec["numero"], rec["nome"], rec["forma_contato"], rec["contato"]] for rec in registros]
    ws.append_rows(rows, value_input_option="USER_ENTERED")

# Inicialização do app
if "iniciado" not in st.session_state:
    sorteados, registros = carregar_dados()
    st.session_state.numeros_sorteados = sorteados
    st.session_state.numeros_disponiveis = [i for i in range(1, 501) if i not in sorteados]
    st.session_state.registros = registros
    st.session_state.numeros_atuais = []
    st.session_state.iniciado = True

# Interface
st.title("🎁 Sorteio da Loja com Google Sheets")
col1, col2 = st.columns([1,2])

with col1:
    qtd = st.number_input("Quantos números sortear?", min_value=1, max_value=100, value=1)
    if st.button("🎲 Sortear Número(s)"):
        if len(st.session_state.numeros_disponiveis) < qtd:
            st.warning("Não há números suficientes disponíveis.")
        else:
            novos = random.sample(st.session_state.numeros_disponiveis, qtd)
            for n in novos:
                st.session_state.numeros_disponiveis.remove(n)
            st.session_state.numeros_sorteados += novos
            st.session_state.numeros_atuais = novos
            salvar_sorteados(novos)
            st.success(f"Sorteados: {', '.join(map(str, novos))}")

with col2:
    if st.session_state.numeros_atuais:
        st.markdown(f"### Registrando para os números: {', '.join(map(str, st.session_state.numeros_atuais))}")
        with st.form("form_cliente", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            forma = st.selectbox("Forma de contato", ["Instagram","WhatsApp"])
            contato = st.text_input("Usuário ou número")
            enviar = st.form_submit_button("Salvar Registros")
            if enviar:
                regs = []
                for num in st.session_state.numeros_atuais:
                    regs.append({"numero": num, "nome": nome, "forma_contato": forma, "contato": contato})
                st.session_state.registros += regs
                salvar_registros(regs)
                st.success(f"Salvo para {len(regs)} números.")
                st.session_state.numeros_atuais = []

st.subheader("🧮 Números do Sorteio")
def render(n):
    cls = ("current" if n in st.session_state.numeros_atuais else
           "sorted" if n in st.session_state.numeros_sorteados else "sortable")
    return f'<div class="num-box {cls}">{n}</div>'
st.markdown("""
<style>.num-box{width:45px;height:45px;display:flex;align-items:center;justify-content:center;margin:2px;font-weight:bold;border-radius:6px;}
.sortable{background:#d4edda;color:#155724;border:1px solid #c3e6cb;}
.sorted{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;}
.current{background:#fff3cd;color:#856404;border:2px solid #ffeeba;}
.number-grid{display:flex;flex-wrap:wrap;}
</style>""", unsafe_allow_html=True)
grid = '<div class="number-grid">'+''.join(render(i) for i in range(1,501))+'</div>'
st.markdown(grid, unsafe_allow_html=True)

with st.expander("📄 Registros salvos"):
    if st.session_state.registros:
        df = pd.DataFrame(st.session_state.registros)
        df.index += 1
        df.columns = ["Número","Nome","Forma de Contato","Contato"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum registro ainda.")
