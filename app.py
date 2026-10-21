import pandas as pd
import streamlit as st
from google import genai

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

# --- CONFIGURA QUI IL NOME DEL TUO FILE EXCEL SU GITHUB ---
excel_path = (
    "saint.xlsx"  # Es. "saint_seiya_database.xlsx" (metti il nome esatto)
)


@st.cache_data
def load_excel_sheets(path):
  """Carica tutti i fogli del file Excel in un dizionario di DataFrame."""
  try:
    xls = pd.ExcelFile(path)
    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    return sheets
  except Exception as e:
    return None


sheets_data = load_excel_sheets(excel_path)

# --- SEZIONE 1: CONSULTAZIONE DATABASE (EXCEL) ---
st.header("📊 Consultazione Database")

if sheets_data:
  selected_sheet = st.selectbox(
      "Seleziona una sezione/tabella:", list(sheets_data.keys())
  )
  if selected_sheet:
    df = sheets_data[selected_sheet]
    st.dataframe(df, use_container_width=True)
else:
  st.warning(
      "⚠️ Impossibile trovare o leggere il file Excel su GitHub. Assicurati"
      " che il nome nel codice (`tuo_file.xlsx`) corrisponda esattamente a"
      " quello caricato."
  )

st.divider()

# --- SEZIONE 2: ASSISTENTE IA INTEGRATO (GEMINI) ---
st.header("🤖 Assistente IA (Gemini)")

try:
  gemini_api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=gemini_api_key)
  ai_available = True
except Exception:
  ai_available_False = False
  ai_available = False
  st.warning(
      "⚠️ Per abilitare l'IA, inserisci la tua `GEMINI_API_KEY` nelle"
      " impostazioni 'Secrets' di Streamlit Cloud."
  )

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
          table_names = (
              list(sheets_data.keys()) if sheets_data else []
          )
          context_info = (
              f"Sei un esperto del gioco Saint Seiya: Legend of Justice."
              f" Sezioni presenti nel database: {', '.join(table_names)}."
          )
          response = client.models.generate_content(
              model="gemini-3.8-flash",
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
