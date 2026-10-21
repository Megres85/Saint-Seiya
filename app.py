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
    "Consulta il database completo, cerca rapidamente tra le schede dei"
    " personaggi, i marchi e le abilità, oppure chiedi all'Assistente IA."
)

# --- NOME DEL TUO FILE EXCEL AGGIORNATO ---
excel_path = "saint.xlsx"


@st.cache_data
def load_excel_sheets(path):
  """Carica tutte le schede del file Excel originale in un dizionario."""
  try:
    xls = pd.ExcelFile(path)
    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    return sheets
  except Exception as e:
    return None


sheets_data = load_excel_sheets(excel_path)

# --- INTERFACCIA: CONSULTAZIONE E RICERCA INTERATTIVA ---
if sheets_data:
  sheet_names = list(sheets_data.keys())

  tab1, tab2 = st.tabs(
      [
          "📊 Consultazione Schede (Manuale)",
          "🔍 Ricerca Interattiva & Filtri",
      ]
  )

  with tab1:
    st.subheader("Sfoglia le schede del database")
    selected_sheet = st.selectbox(
        "Seleziona una scheda/sezione:",
        sheet_names,
        key="select_sheet_manual",
    )
    if selected_sheet:
      df_current = sheets_data[selected_sheet]
      st.dataframe(df_current, use_container_width=True)

  with tab2:
    st.subheader("Cerca nel database globale")
    st.info(
        "Digita un termine (es. un elemento come **Fuoco**, un nome di"
        " personaggio come **Ikki**, o un effetto come **Stun**) per cercarlo"
        " istantaneamente in tutte le schede del database."
    )

    search_query = st.text_input(
        "Parola chiave da cercare:", key="search_global"
    )

    if search_query:
      results_found = False
      # Cerchiamo in tutte le schede del file Excel
      for sheet_name, df in sheets_data.items():
        # Converte tutto in stringa per effettuare la ricerca senza problemi di tipo
        mask = df.astype(str).apply(
            lambda x: x.str.contains(search_query, case=False, na=False)
        ).any(axis=1)
        filtered_df = df[mask]

        if not filtered_df.empty:
          results_found = True
          with st.expander(
              f"📁 Trovato nella scheda: `{sheet_name}` ({len(filtered_df)}"
              f" righe corrispondenti)",
              expanded=True,
          ):
            st.dataframe(filtered_df, use_container_width=True)

      if not results_found:
        st.warning(
            f"Nessun risultato trovato per '{search_query}' nel database."
        )
    else:
      st.write("Inserisci una parola chiave nel campo sopra per iniziare.")

else:
  st.warning(
      "⚠️ Impossibile trovare il file 'saint.xlsx' nella cartella principale"
      " di GitHub. Assicurati che il nome corrisponda esattamente."
  )

st.divider()

# --- ASSISTENTE IA INTEGRATO (GEMINI) ---
st.header("🤖 Assistente IA (Gemini)")

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

if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input(
    "Es. Quali sono le migliori sinergie o come funzionano le abilità di"
    " Shura DC?"
):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  if ai_available:
    with st.chat_message("assistant"):
      with st.spinner("L'IA sta consultando il database..."):
        try:
          table_names = list(sheets_data.keys()) if sheets_data else []
          context_info = (
              f"Sei un esperto del gioco Saint Seiya: Legend of Justice."
              f" Schede presenti nel database Excel:"
              f" {', '.join(table_names[:30])}..."
          )
          response = client.models.generate_content(
              model="gemini-3.8-flash",
              contents=(
                  f"Contesto: {context_info}\n\nDomanda dell'utente:"
                  f" {prompt}\n\nRispondi in modo dettagliato, chiaro e"
                  " preciso basandoti sulle meccaniche del gioco."
              ),
          )
          answer = response.text
        except Exception as e:
          answer = f"Errore nella generazione della risposta: {e}"

        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
