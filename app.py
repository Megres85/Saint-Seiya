

import sqlite3
from google import genai
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Saint Seiya: Legend of Justice - Database & AI Assistant",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Saint Seiya: Legend of Justice - Database & AI Assistant")
st.write(
    "Consulta le tabelle del database oppure fai domande direttamente"
    " all'Assistente IA su personaggi, abilità e meccaniche di gioco."
)

# Nome esatto del file del database su GitHub
db_path = "dbsqlite"


def get_tables():
  """Estrae l'elenco delle tabelle dal database SQLite."""
  try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()
    return tables
  except Exception:
    return []


tables = get_tables()

# --- SEZIONE 1: CONSULTAZIONE DATABASE ---
st.header("📊 Consultazione Database")

if tables:
  selected_table = st.selectbox("Seleziona una tabella da visualizzare:", tables)
  if selected_table:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM [{selected_table}]", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
else:
  st.warning(
      "⚠️ Impossibile trovare o leggere il file del database `dbsqlite`."
      " Assicurati che si trovi nella stessa cartella."
  )

st.divider()

# --- SEZIONE 2: ASSISTENTE IA INTEGRATO (GEMINI) ---
st.header("🤖 Assistente IA (Gemini)")

# Configurazione della chiave API tramite i Secrets di Streamlit Cloud
try:
  gemini_api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=gemini_api_key)
  ai_available = True
except Exception:
  ai_available = False
  st.warning(
      "⚠️ Per abilitare l'IA, inserisci la tua `GEMINI_API_KEY` nelle"
      " impostazioni 'Secrets' di Streamlit Cloud."
  )

# Gestione della chat
if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input(
    "Es. Spiegami la differenza tra Stun e Paura, o come funziona la barra"
    " rossa."
):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  if ai_available:
    with st.chat_message("assistant"):
      with st.spinner("L'IA sta elaborando la risposta..."):
        try:
          context_info = (
              f"Sei un esperto del gioco Saint Seiya: Legend of Justice."
              f" Tabelle presenti nel database: {', '.join(tables)}."
          )
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=(
                  f"Contesto: {context_info}\n\nDomanda dell'utente:"
                  f" {prompt}\n\nRispondi in modo dettagliato, chiaro e"
                  " preciso."
              ),
          )
          answer = response.text
        except Exception as e:
          answer = f"Errore nella generazione della risposta: {e}"

        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})