import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

# --- PERCORSO DEL FILE JSON ---
DATA_FILE = "dashboard_data.json"

# --- FUNZIONI PER SALVARE/CARICARE DATI ---
def save_data():
    data = {
        'df_main': st.session_state.df_main.to_dict(orient='records'),
        'df_dettagli': st.session_state.df_dettagli
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.session_state.df_main = pd.DataFrame(data['df_main'])
        if 'BM' in st.session_state.df_main.columns:
            st.session_state.df_main = st.session_state.df_main.rename(columns={'BM': 'TL'})
            new_dettagli = {}
            for risorsa, dati in data['df_dettagli'].items():
                new_dati = {}
                for key, value in dati.items():
                    new_dati['TL' if key == 'BM' else key] = value
                new_dettagli[risorsa] = new_dati
            st.session_state.df_dettagli = new_dettagli
        if '% Allocazione' in st.session_state.df_main.columns:
            st.session_state.df_main['% Allocazione'] = st.session_state.df_main['% Allocazione'].astype('float64')

# --- CSS MINIMO ---
st.markdown("""
<style>
    .stButton > button {
        padding: 4px 8px !important;
        font-size: 13px !important;
        height: 28px !important;
        width: auto !important;
        border-radius: 4px !important;
        border: 1px solid #ddd !important;
        margin-right: 5px !important;
    }
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER CON TITOLO E LOGO ALTENA IN ALTO A DESTRA ---
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center;'>
    <h1 style='margin: 0;'>Allocation Plan</h1>
    <img src='https://dc8986d40dcb258da2ea57.blob.core.windows.net/apps/le-chat/43/e4/23/43e4231e-58c1-42b2-adb3-4f46a42f99fd/ae2dc7a4-c67f-4549-af84-ba05bec62638/83e073e1-d590-411e-86c2-0290e520151b?sv=2025-01-05&se=2026-10-13T18%3A35%3A36Z&sr=b&sp=r&sig=Ah7xM2XVp%2FWojXyyuKjMQh%2BKKv98fLyuFsxTot8Ym2M%3D' width='100'>
</div>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Allocation Plan", layout="wide")

# --- INIZIALIZZAZIONE DATI ---
if 'df_main' not in st.session_state:
    st.session_state.df_main = pd.DataFrame({
        'Risorsa': pd.Series([], dtype='str'),
        'SDC': pd.Series([], dtype='str'),
        'TL': pd.Series([], dtype='str'),
        'Stato': pd.Series([], dtype='str'),
        'Mese di Riferimento': pd.Series([], dtype='str'),
        '% Allocazione': pd.Series([], dtype='float64')
    })
    st.session_state.df_dettagli = {}
    load_data()

# --- FUNZIONI UTILITY ---
def get_3_mesi(mese_riferimento):
    traduzione_it_to_en = {
        "Gennaio": "January", "Febbraio": "February", "Marzo": "March",
        "Aprile": "April", "Maggio": "May", "Giugno": "June",
        "Luglio": "July", "Agosto": "August", "Settembre": "September",
        "Ottobre": "October", "Novembre": "November", "Dicembre": "December"
    }
    traduzione_en_to_it = {v: k for k, v in traduzione_it_to_en.items()}
    nome_mese_it, anno = mese_riferimento.split()
    nome_mese_en = traduzione_it_to_en[nome_mese_it]
    dt = datetime.strptime(f"{nome_mese_en} {anno}", "%B %Y")
    mesi = []
    for i in range(3):
        nuovo_mese = dt.month + i
        nuovo_anno = dt.year + ((nuovo_mese - 1) // 12)
        nuovo_mese = (nuovo_mese - 1) % 12 + 1
        nuovo_dt = datetime(nuovo_anno, nuovo_mese, 1)
        nome_mese_it = traduzione_en_to_it[nuovo_dt.strftime("%B")]
        mesi.append(f"{nome_mese_it} {nuovo_anno}")
    return mesi

def get_emoji(media, stato):
    if stato == 'TM': return '⚪'
    elif stato == 'D': return '⚫'
    elif media > 100: return '🔵'
    elif media == 100: return '🟢'
    elif 50 <= media < 100: return '🟡'
    else: return '🔴'

def calcola_media_risorsa(risorsa):
    if risorsa in st.session_state.df_dettagli:
        dati = st.session_state.df_dettagli[risorsa]
        mesi_forecast = get_3_mesi(dati['Mese di Riferimento'])
        totale = sum(proj['% Allocazione'] for mese in mesi_forecast if mese in dati['Mesi'] for proj in dati['Mesi'][mese])
        return totale / 3
    return 0.0

for index, row in st.session_state.df_main.iterrows():
    st.session_state.df_main.at[index, '% Allocazione'] = float(calcola_media_risorsa(row['Risorsa']))

# --- SIDEBAR: FILTRI ---
st.sidebar.header("🔍 Filtri")
has_data = not st.session_state.df_main.empty

all_sdc = [""]
if has_data and 'SDC' in st.session_state.df_main.columns:
    all_sdc += sorted([s for s in st.session_state.df_main['SDC'].unique() if s])
selected_sdc = st.sidebar.multiselect("SDC", all_sdc, default=all_sdc)

all_tl = [""]
if has_data and 'TL' in st.session_state.df_main.columns:
    all_tl += sorted([t for t in st.session_state.df_main['TL'].unique() if t])
selected_tl = st.sidebar.multiselect("TL", all_tl, default=all_tl)

all_stato = ["TM", "P", "D"]
if has_data and 'Stato' in st.session_state.df_main.columns:
    all_stato = sorted(st.session_state.df_main['Stato'].unique())
selected_stato = st.sidebar.multiselect("Stato", all_stato, default=all_stato)

all_risorse = [""]
if has_data and 'Risorsa' in st.session_state.df_main.columns:
    all_risorse += sorted([r for r in st.session_state.df_main['Risorsa'].unique() if r])
selected_risorse = st.sidebar.multiselect("Risorsa", all_risorse, default=all_risorse)

all_mesi_rif = [""]
if has_data and 'Mese di Riferimento' in st.session_state.df_main.columns:
    all_mesi_rif += sorted([m for m in st.session_state.df_main['Mese di Riferimento'].unique() if m])
selected_mesi_rif = st.sidebar.multiselect("Mese di Riferimento", all_mesi_rif, default=all_mesi_rif)

df_filtered = st.session_state.df_main[
    (st.session_state.df_main['SDC'].isin(selected_sdc)) &
    (st.session_state.df_main['TL'].isin(selected_tl)) &
    (st.session_state.df_main['Stato'].isin(selected_stato)) &
    (st.session_state.df_main['Risorsa'].isin(selected_risorse)) &
    (st.session_state.df_main['Mese di Riferimento'].isin(selected_mesi_rif)) &
    (st.session_state.df_main['Stato'] != 'D')
] if has_data else st.session_state.df_main.copy()

# --- SEZIONE: TABELLA PRINCIPALE O NUOVA RISORSA ---
if not st.session_state.get('selected_risorsa', False):
    if st.button("➕ Aggiungi Nuova Risorsa", type="primary"):
        st.session_state.new_risorsa = True
        st.session_state.temp_dati = {
            'Risorsa': '',
            'SDC': '',
            'TL': '',
            'Stato': 'P',
            'Mese di Riferimento': 'Ottobre 2026',
            'Mesi': {}
        }

    if st.session_state.get('new_risorsa', False):
        st.subheader("📝 Aggiungi Nuova Risorsa con Forecast")
        st.session_state.temp_dati['Risorsa'] = st.text_input("Risorsa (Cognome Nome)", value=st.session_state.temp_dati['Risorsa'], key="new_risorsa_name")
        st.session_state.temp_dati['SDC'] = st.text_input("SDC", value=st.session_state.temp_dati['SDC'], key="new_sdc")
        st.session_state.temp_dati['TL'] = st.text_input("TL", value=st.session_state.temp_dati['TL'], key="new_tl")
        st.session_state.temp_dati['Stato'] = st.selectbox("Stato", ["TM", "P", "D"], index=["TM", "P", "D"].index(st.session_state.temp_dati['Stato']), key="new_stato")
        st.session_state.temp_dati['Mese di Riferimento'] = st.selectbox(
            "Mese di Riferimento",
            ["Ottobre 2026", "Novembre 2026", "Dicembre 2026", "Gennaio 2027", "Febbraio 2027"],
            index=["Ottobre 2026", "Novembre 2026", "Dicembre 2026", "Gennaio 2027", "Febbraio 2027"].index(st.session_state.temp_dati['Mese di Riferimento']),
            key="new_mese_riferimento"
        )

        st.divider()
        st.subheader("📅 Forecast per i prossimi 3 mesi")
        mesi_forecast = get_3_mesi(st.session_state.temp_dati['Mese di Riferimento'])
        for mese in mesi_forecast:
            if mese not in st.session_state.temp_dati['Mesi']:
                st.session_state.temp_dati['Mesi'][mese] = []

        for i, mese in enumerate(mesi_forecast):
            st.markdown("---")
            st.subheader(f"📆 {mese}")
            if st.button(f"➕ Aggiungi Progetto per {mese}", key=f"add_proj_new_{i}"):
                st.session_state.temp_dati['Mesi'][mese].append({'Progetto': '', '% Allocazione': 0.0})
                st.rerun()

            for j, progetto in enumerate(st.session_state.temp_dati['Mesi'][mese]):
                col1, col2, col3 = st.columns([3, 1, 0.5])
                with col1:
                    st.session_state.temp_dati['Mesi'][mese][j]['Progetto'] = st.text_input(f"Progetto {j+1}", value=progetto['Progetto'], key=f"new_proj_{i}_{j}", label_visibility="collapsed")
                with col2:
                    st.session_state.temp_dati['Mesi'][mese][j]['% Allocazione'] = st.number_input(f"% Allocazione", min_value=0.0, max_value=200.0, value=float(progetto['% Allocazione']), key=f"new_alloc_{i}_{j}", label_visibility="collapsed")
                with col3:
                    if st.button(f"❌", key=f"del_new_{i}_{j}"):
                        st.session_state.temp_dati['Mesi'][mese].pop(j)
                        st.rerun()

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Salva", type="primary"):
                new_row = pd.DataFrame({
                    'Risorsa': [st.session_state.temp_dati['Risorsa']],
                    'SDC': [st.session_state.temp_dati['SDC']],
                    'TL': [st.session_state.temp_dati['TL']],
                    'Stato': [st.session_state.temp_dati['Stato']],
                    'Mese di Riferimento': [st.session_state.temp_dati['Mese di Riferimento']],
                    '% Allocazione': [0.0]
                })
                st.session_state.df_main = pd.concat([st.session_state.df_main, new_row], ignore_index=True)
                st.session_state.df_dettagli[st.session_state.temp_dati['Risorsa']] = {
                    'SDC': st.session_state.temp_dati['SDC'],
                    'TL': st.session_state.temp_dati['TL'],
                    'Stato': st.session_state.temp_dati['Stato'],
                    'Mese di Riferimento': st.session_state.temp_dati['Mese di Riferimento'],
                    'Mesi': {k: [p.copy() for p in v] for k, v in st.session_state.temp_dati['Mesi'].items()}
                }
                st.session_state.df_main.loc[st.session_state.df_main['Risorsa'] == st.session_state.temp_dati['Risorsa'], '% Allocazione'] = float(calcola_media_risorsa(st.session_state.temp_dati['Risorsa']))
                save_data()
                st.session_state.new_risorsa = False
                del st.session_state.temp_dati
                st.rerun()
        with col2:
            if st.button("❌ Annulla"):
                st.session_state.new_risorsa = False
                if 'temp_dati' in st.session_state:
                    del st.session_state.temp_dati
                st.rerun()

    st.header("Dati Allocazione")
    cols = st.columns([1.5, 1, 1, 1, 1, 1, 0.5])
    with cols[0]: st.markdown("**Risorsa**")
    with cols[1]: st.markdown("**SDC**")
    with cols[2]: st.markdown("**TL**")
    with cols[3]: st.markdown("**Stato**")
    with cols[4]: st.markdown("**Mese di Riferimento**")
    with cols[5]: st.markdown("**% Allocazione**")
    st.divider()

    for index, row in df_filtered.iterrows():
        media = calcola_media_risorsa(row['Risorsa'])
        emoji = get_emoji(media, row['Stato'])
        cols = st.columns([1.5, 1, 1, 1, 1, 1, 0.5])
        with cols[0]:
            if row['Stato'] == 'P':
                if st.button(f"{emoji} {row['Risorsa']}", key=f"btn_risorsa_{index}", use_container_width=True):
                    st.session_state.selected_risorsa = row['Risorsa']
                    st.rerun()
            else:
                st.markdown(f"{emoji} **{row['Risorsa']}**")
        with cols[1]: st.write(row['SDC'])
        with cols[2]: st.write(row['TL'])
        with cols[3]: st.write(row['Stato'])
        with cols[4]: st.write(row['Mese di Riferimento'])
        with cols[5]: st.write(f"{row['% Allocazione']:.1f}%")
        with cols[6]:
            if st.button("🗑️", key=f"del_row_{index}", help="Elimina risorsa"):
                risorsa = row['Risorsa']
                st.session_state.df_main = st.session_state.df_main[st.session_state.df_main['Risorsa'] != risorsa]
                if risorsa in st.session_state.df_dettagli:
                    del st.session_state.df_dettagli[risorsa]
                save_data()
                st.rerun()

    st.divider()
    if st.button("📊 Mostra/Nascondi Report", type="primary"):
        st.session_state.show_report = not st.session_state.get("show_report", False)
    if st.session_state.get("show_report", False):
        st.header("📈 Report Allocazione")
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df_filtered, x="SDC", y="% Allocazione", color="Stato", title="Allocazione per SDC", barmode="group")
            fig1.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(df_filtered, x="TL", y="% Allocazione", color="Stato", title="Allocazione per TL", barmode="group")
            fig2.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig2, use_container_width=True)
        fig3 = px.pie(df_filtered, names="Stato", values="% Allocazione", title="Distribuzione Allocazione per Stato")
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)

# --- SCHEDA DETTAGLIATA ---
else:
    risorsa = st.session_state.selected_risorsa
    st.header(f"📝 Dettagli per {risorsa}")

    if risorsa not in st.session_state.df_dettagli:
        st.session_state.df_dettagli[risorsa] = {
            'SDC': '', 'TL': '', 'Stato': 'P',
            'Mese di Riferimento': 'Ottobre 2026', 'Mesi': {}
        }
        save_data()

    dati_risorsa = st.session_state.df_dettagli[risorsa]
    st.subheader("📝 Dati Generali")
    dati_risorsa['SDC'] = st.text_input("SDC", value=dati_risorsa.get('SDC', ''), key="det_sdc")
    dati_risorsa['TL'] = st.text_input("TL", value=dati_risorsa.get('TL', ''), key="det_tl")
    dati_risorsa['Stato'] = st.selectbox("Stato", ["TM", "P", "D"], index=["TM", "P", "D"].index(dati_risorsa.get('Stato', 'P')), key="det_stato")
    st.divider()

    st.subheader("📅 FORECAST")

    mese_riferimento = dati_risorsa['Mese di Riferimento']
    mesi_forecast = get_3_mesi(mese_riferimento)

    for i, mese in enumerate(mesi_forecast):
        st.markdown("---")
        st.subheader(f"📆 {mese}")
        if st.button(f"➕ Aggiungi Progetto per {mese}", key=f"add_proj_det_{i}"):
            if mese not in dati_risorsa['Mesi']:
                dati_risorsa['Mesi'][mese] = []
            dati_risorsa['Mesi'][mese].append({'Progetto': '', '% Allocazione': 0.0})
            st.session_state.df_dettagli[risorsa] = dati_risorsa
            st.rerun()

        if mese in dati_risorsa['Mesi']:
            for j, progetto in enumerate(dati_risorsa['Mesi'][mese]):
                col1, col2, col3 = st.columns([3, 1, 0.5])
                with col1:
                    dati_risorsa['Mesi'][mese][j]['Progetto'] = st.text_input(f"Progetto {j+1}", value=progetto['Progetto'], key=f"proj_det_{i}_{j}", label_visibility="collapsed")
                with col2:
                    dati_risorsa['Mesi'][mese][j]['% Allocazione'] = st.number_input(f"%", min_value=0.0, max_value=200.0, value=float(progetto['% Allocazione']), key=f"alloc_det_{i}_{j}", label_visibility="collapsed")
                with col3:
                    if st.button(f"❌", key=f"del_det_{i}_{j}"):
                        dati_risorsa['Mesi'][mese].pop(j)
                        st.session_state.df_dettagli[risorsa] = dati_risorsa
                        st.rerun()

    if st.button("💾 Salva e Chiudi", type="primary"):
        st.session_state.df_dettagli[risorsa] = dati_risorsa
        st.session_state.df_main.loc[st.session_state.df_main['Risorsa'] == risorsa, ['SDC', 'TL', 'Stato']] = dati_risorsa['SDC'], dati_risorsa['TL'], dati_risorsa['Stato']
        st.session_state.df_main.loc[st.session_state.df_main['Risorsa'] == risorsa, '% Allocazione'] = float(calcola_media_risorsa(risorsa))
        save_data()
        st.session_state.selected_risorsa = None
        st.rerun()

# --- SEZIONE: ESPORTA DATI ---
if not st.session_state.get('new_risorsa', False) and not st.session_state.get('selected_risorsa'):
    st.header("💾 Esporta Dati")
    st.download_button(
        label="📥 Scarica Dati come CSV",
        data=df_filtered.to_csv(index=False).encode('utf-8'),
        file_name="allocazione_risorse.csv",
        mime="text/csv"
    )