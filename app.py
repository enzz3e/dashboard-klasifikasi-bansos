import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import json
import joblib
import os
from shapely.geometry import Polygon

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Bansos — Tanjung Perak",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SETUP SESSION STATE UNTUK TEMA ─────────────────────────────────────────────
if 'light_mode' not in st.session_state:
    st.session_state.light_mode = False

# Sidebar Toggle Tema
with st.sidebar:
    st.markdown("### Pengaturan Tema")
    st.session_state.light_mode = st.toggle(" Mode Terang (Light Mode)", value=st.session_state.light_mode)
    st.markdown("---")

is_light = st.session_state.light_mode

# Variabel dinamis berdasarkan tema
CHART_FONT_COLOR = "#0f172a" if is_light else "#e2e8f0"
PLOTLY_TEMPLATE = "plotly_white" if is_light else "plotly_dark"
MAP_TILES = 'CartoDB positron' if is_light else 'CartoDB dark_matter'
MAP_BG = '#ffffff' if is_light else '#1e293b'
MAP_TEXT = '#0f172a' if is_light else '#f8fafc'
MAP_BORDER = '#e2e8f0' if is_light else '#334155'
MUTED_TEXT = '#64748b' if is_light else '#cbd5e1'

# ── FUNGSI POP-UP PREDIKSI REAL-TIME ──────────────────────────────────────────
@st.dialog("Prediksi Kelayakan Warga Baru")
def popup_prediksi():
    desc_color = '#475569' if st.session_state.light_mode else '#cbd5e1'
    st.markdown(f"<p style='color: {desc_color}; margin-bottom: 15px;'>Masukkan detail data warga di bawah ini untuk menguji kelayakan secara langsung menggunakan kecerdasan Model C4.5.</p>", unsafe_allow_html=True)
    
    with st.form("form_prediksi"):
        nama = st.text_input("Nama Kepala Keluarga", placeholder="Contoh: Ahmad Fauzi")
        jml_jiwa = st.number_input("Jumlah Anggota Keluarga (Jiwa)", min_value=1, max_value=20, value=3)
        ijazah = st.selectbox("Pendidikan Terakhir", 
                              ['Tidak punya ijazah','SD/sederajat','SMP/sederajat','SMA/sederajat','D1/D2/D3','D4/S1','S2/S3'])
        
        if os.path.exists('le_pekerjaan.joblib'):
            le = joblib.load('le_pekerjaan.joblib')
            pekerjaan_options = sorted(list(le.classes_))
        else:
            pekerjaan_options = ['BURUH', 'KARYAWAN SWASTA', 'WIRASWASTA', 'LANSIA', 'PEDAGANG']
            
        pekerjaan = st.selectbox("Jenis Pekerjaan Mandiri", pekerjaan_options)
        pendapatan = st.number_input("Total Pendapatan (Rp)", min_value=0, value=1500000, step=100000)
        
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        submit = st.form_submit_button(" Hitung Prediksi Status", use_container_width=True)
        
        if submit:
            if not os.path.exists('model_c45.joblib') or not os.path.exists('le_pekerjaan.joblib'):
                st.error(" File 'model_c45.joblib' atau 'le_pekerjaan.joblib' belum ada!")
            else:
                perkapita = pendapatan / jml_jiwa if jml_jiwa > 0 else pendapatan

                if perkapita <= 500000: bin_pendapatan = 0
                elif perkapita <= 600000: bin_pendapatan = 1
                elif perkapita <= 750000: bin_pendapatan = 2
                else: bin_pendapatan = 3

                ij_map = {'Tidak punya ijazah': 0, 'SD/sederajat': 1, 'SMP/sederajat': 2, 'SMA/sederajat': 3, 'D1/D2/D3': 4, 'D4/S1': 4, 'S2/S3': 4}
                ij_enc = ij_map[ijazah]

                try:
                    le = joblib.load('le_pekerjaan.joblib')
                    pek_enc = le.transform([pekerjaan])[0]
                except Exception:
                    pek_enc = 0

                input_df = pd.DataFrame([[jml_jiwa, ij_enc, pek_enc, bin_pendapatan]], columns=['JML_JIWA', 'IJAZAH_ENC', 'PEKERJAAN_ENC', 'PENDAPATAN_BIN'])

                model = joblib.load('model_c45.joblib')
                pred = model.predict(input_df)[0]
                prob = model.predict_proba(input_df).max()

                label_map = {0: 'MISKIN', 1: 'PRA SEJAHTERA', 2: 'SEJAHTERA'}
                hasil_label = label_map[pred]

                hr_color = '#e2e8f0' if st.session_state.light_mode else '#475569'
                st.markdown(f"<hr style='border-color:{hr_color};'>", unsafe_allow_html=True)
                st.markdown("###  Hasil Prediksi Sistem:")
                
                if pred == 0:
                    st.error(" Kepala Keluarga **{}** diklasifikasikan sebagai: **{}** (Prioritas Penerima Bansos)\n\n*Tingkat Kepercayaan Sistem: {:.1f}%*".format(nama, hasil_label, prob*100))
                elif pred == 1:
                    st.warning(" Kepala Keluarga **{}** diklasifikasikan sebagai: **{}**\n\n*Tingkat Kepercayaan Sistem: {:.1f}%*".format(nama, hasil_label, prob*100))
                else:
                    st.success(" Kepala Keluarga **{}** diklasifikasikan sebagai: **{}**\n\n*Tingkat Kepercayaan Sistem: {:.1f}%*".format(nama, hasil_label, prob*100))

# ── 2. CSS DINAMIS UNTUK TEMA LIGHT/DARK ──────────────────────────────────────
css_dark = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 0 1.5rem 2rem 1.5rem; max-width: 100%; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #0f172a !important; color: #f1f5f9 !important; }
[data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155 !important; }
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #cbd5e1 !important; }

/* Dashboard Header & Cards */
.dash-header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px 32px; border-radius: 0 0 16px 16px; margin: -1rem -1.5rem 2rem -1.5rem; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #334155 !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
.dash-header h1 { color: #ffffff !important; font-size: 22px; font-weight: 700; margin: 0; padding:0;}
.dash-header p  { color: #94a3b8 !important; font-size: 14px; margin: 4px 0 0 0; }
.dash-header .badge { background: rgba(255,255,255,0.05); border: 1px solid #334155; color: #ffffff !important; padding: 8px 16px; border-radius: 30px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }

.section-title { font-size: 17px; font-weight: 700; color: #ffffff !important; margin-bottom: 16px; margin-top: 24px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #334155; padding-bottom: 8px; }
.metric-card { background: #1e293b !important; border-radius: 14px; padding: 20px 24px; border: 1px solid #334155 !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); position: relative; overflow: hidden; height: 140px; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card::after { content:''; position:absolute; top:0; left:0; width: 4px; height: 100%; }
.metric-card.total::after    { background:#3b82f6; } .metric-card.miskin::after   { background:#ef4444; }
.metric-card.pra::after      { background:#f59e0b; } .metric-card.sejahtera::after{ background:#10b981; }

.metric-top { display:flex; align-items:center; gap:12px; }
.metric-icon-wrap { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.metric-card.total .metric-icon-wrap { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.metric-card.miskin .metric-icon-wrap { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.metric-card.pra .metric-icon-wrap { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.metric-card.sejahtera .metric-icon-wrap { background: rgba(16, 185, 129, 0.15); color: #34d399; }

.metric-lbl  { font-size:12px; color:#94a3b8 !important; font-weight:600; text-transform: uppercase; }
.metric-val  { font-size:34px; font-weight:700; color:#ffffff !important; line-height:1; margin-top: 6px;}
.metric-pct  { font-size:11px; font-weight:600; display:inline-block; padding:4px 10px; border-radius:20px; margin-top: 4px; }
.pct-total    { background:#334155 !important; color:#cbd5e1 !important; border: 1px solid #475569; }
.pct-miskin   { background:rgba(239, 68, 68, 0.1) !important; color:#fca5a5 !important; }
.pct-pra      { background:rgba(245, 158, 11, 0.1) !important; color:#fcd34d !important; }
.pct-sejahtera{ background:rgba(16, 185, 129, 0.1) !important; color:#6ee7b7 !important; }

/* FIX MODAL/DIALOG HEADINGS (DARK) */
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] p, div[data-testid="stDialog"] label, div[data-testid="stDialog"] span,
div[role="dialog"] h1, div[role="dialog"] h2, div[role="dialog"] h3, div[role="dialog"] p, div[role="dialog"] label, div[role="dialog"] span { 
    color: #ffffff !important; 
}
/* Ensure the submit button text remains white */
div[data-testid="stFormSubmitButton"] > button, div[data-testid="stFormSubmitButton"] > button span, div[data-testid="stFormSubmitButton"] > button p { color: #ffffff !important; }

/* FIX NUMBER INPUT PLUS MINUS BUTTONS (DARK) */
.stNumberInput button { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
.stNumberInput button svg { fill: #f8fafc !important; }
.stNumberInput button:hover { background-color: #334155 !important; }

/* FIX MODAL/DIALOG & FORM (DARK) */
div[role="dialog"], div[data-testid="stModalContent"] { background-color: #1e293b !important; border: 1px solid #334155 !important; }
div[role="dialog"] button[kind="header"] { color: #f8fafc !important; }
div[data-testid="stForm"] { border: 1px solid #334155 !important; background-color: #0f172a !important; }
div[data-testid="stFormSubmitButton"] > button { background-color: #3b82f6 !important; border: none !important; width: 100%; font-weight: 600;}
div[data-testid="stFormSubmitButton"] > button:hover { background-color: #2563eb !important; }

/* NATIVE INPUTS (DARK) */
.stMultiSelect div[data-baseweb="select"] > div, .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, div[data-baseweb="input"] { background-color: #0f172a !important; border: 1px solid #334155 !important; color: #f8fafc !important; }
.stMultiSelect span[data-baseweb="tag"] { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important;}
.stButton > button, div[data-testid="stDownloadButton"] button { background-color: #1e293b !important; border: 1px solid #334155 !important; color: #f8fafc !important; font-weight: 500; }
.stButton > button:hover, div[data-testid="stDownloadButton"] button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; background-color: #0f172a !important;}
.stRadio div[role="radiogroup"] * { color: #f8fafc !important; }
div[role="listbox"], div[data-baseweb="popover"] > div { background-color: #0f172a !important; border: 1px solid #334155 !important; }
li[role="option"] { color: #f8fafc !important; }

hr { border-color:#334155; margin:2rem 0; opacity: 0.5;}
.stDataFrame { border: 1px solid #334155; border-radius: 8px; }
label, .stMarkdown p { color: #e2e8f0 !important; }
</style>
"""

css_light = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 0 1.5rem 2rem 1.5rem; max-width: 100%; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: #f8fafc !important; color: #0f172a !important; }
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #475569 !important; }

/* Dashboard Header & Cards */
.dash-header { background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%); padding: 24px 32px; border-radius: 0 0 16px 16px; margin: -1rem -1.5rem 2rem -1.5rem; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e8f0 !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
.dash-header h1 { color: #0f172a !important; font-size: 22px; font-weight: 700; margin: 0; padding:0;}
.dash-header p  { color: #64748b !important; font-size: 14px; margin: 4px 0 0 0; }
.dash-header .badge { background: rgba(0,0,0,0.05); border: 1px solid #cbd5e1; color: #1e293b !important; padding: 8px 16px; border-radius: 30px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }

.section-title { font-size: 17px; font-weight: 700; color: #1e293b !important; margin-bottom: 16px; margin-top: 24px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
.metric-card { background: #ffffff !important; border-radius: 14px; padding: 20px 24px; border: 1px solid #e2e8f0 !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); position: relative; overflow: hidden; height: 140px; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card::after { content:''; position:absolute; top:0; left:0; width: 4px; height: 100%; }
.metric-card.total::after    { background:#3b82f6; } .metric-card.miskin::after   { background:#ef4444; }
.metric-card.pra::after      { background:#f59e0b; } .metric-card.sejahtera::after{ background:#10b981; }

.metric-top { display:flex; align-items:center; gap:12px; }
.metric-icon-wrap { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.metric-card.total .metric-icon-wrap { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.metric-card.miskin .metric-icon-wrap { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.metric-card.pra .metric-icon-wrap { background: rgba(245, 158, 11, 0.15); color: #d97706; }
.metric-card.sejahtera .metric-icon-wrap { background: rgba(16, 185, 129, 0.15); color: #10b981; }

.metric-lbl  { font-size:12px; color:#64748b !important; font-weight:600; text-transform: uppercase; }
.metric-val  { font-size:34px; font-weight:700; color:#1e293b !important; line-height:1; margin-top: 6px;}
.metric-pct  { font-size:11px; font-weight:600; display:inline-block; padding:4px 10px; border-radius:20px; margin-top: 4px; }
.pct-total    { background:#f1f5f9 !important; color:#475569 !important; border: 1px solid #cbd5e1; }
.pct-miskin   { background:rgba(239, 68, 68, 0.1) !important; color:#b91c1c !important; }
.pct-pra      { background:rgba(245, 158, 11, 0.1) !important; color:#b45309 !important; }
.pct-sejahtera{ background:rgba(16, 185, 129, 0.1) !important; color:#047857 !important; }

/* FIX MODAL/DIALOG HEADINGS (LIGHT) */
div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] p, div[data-testid="stDialog"] label, div[data-testid="stDialog"] span,
div[role="dialog"] h1, div[role="dialog"] h2, div[role="dialog"] h3, div[role="dialog"] p, div[role="dialog"] label, div[role="dialog"] span { 
    color: #0f172a !important; 
}
/* Ensure the submit button text remains white */
div[data-testid="stFormSubmitButton"] > button, div[data-testid="stFormSubmitButton"] > button span, div[data-testid="stFormSubmitButton"] > button p { color: #ffffff !important; }

/* FIX NUMBER INPUT PLUS MINUS BUTTONS (LIGHT) */
.stNumberInput button { background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
.stNumberInput button svg { fill: #0f172a !important; color: #0f172a !important; }
.stNumberInput button:hover { background-color: #e2e8f0 !important; }

/* FIX MODAL/DIALOG & FORM (LIGHT) */
div[role="dialog"], div[data-testid="stModalContent"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; }
div[role="dialog"] button[kind="header"] { color: #0f172a !important; }
div[role="dialog"] button[kind="header"] svg { fill: #0f172a !important; }
div[data-testid="stForm"] { border: 1px solid #e2e8f0 !important; background-color: #f8fafc !important; }
div[data-testid="stFormSubmitButton"] > button { background-color: #3b82f6 !important; border: none !important; width: 100%; font-weight: 600;}
div[data-testid="stFormSubmitButton"] > button:hover { background-color: #2563eb !important; }

/* NATIVE INPUTS (LIGHT) */
.stMultiSelect div[data-baseweb="select"] > div, .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, div[data-baseweb="input"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #0f172a !important; }
.stMultiSelect span[data-baseweb="tag"] { background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important;}
.stMultiSelect span[data-baseweb="tag"] span { color: #0f172a !important; }
.stButton > button, div[data-testid="stDownloadButton"] button { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #0f172a !important; font-weight: 500; }
.stButton > button:hover, div[data-testid="stDownloadButton"] button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; background-color: #f8fafc !important;}
.stRadio div[role="radiogroup"] * { color: #0f172a !important; }
div[role="listbox"], div[data-baseweb="popover"] > div { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; }
li[role="option"] { color: #0f172a !important; }

hr { border-color:#e2e8f0; margin:2rem 0;}
.stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
label, .stMarkdown p, .stMarkdown li { color: #334155 !important; }
</style>
"""

st.markdown(css_light if is_light else css_dark, unsafe_allow_html=True)

# ── 3. VEKTOR DATA IKON UTAMA ──────────────────────────────────────────────────
ICON_USERS = """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>"""
ICON_ALERT = """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""
ICON_WARN = """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>"""
ICON_CHECK = """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>"""
ICON_DB = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>"""

# ── 4. MEMUAT GEOJSON BATAS WILAYAH RW ─────────────────────────────────────────
with open('PetaRW.geojson', 'r') as f:
    geojson_data = json.load(f)

RW_POLYGONS = {}
for feature in geojson_data['features']:
    rw_id = int(feature['properties']['id'])
    coords = feature['geometry']['coordinates'][0]
    poly_latlon = [[pt[1], pt[0]] for pt in coords]
    RW_POLYGONS[rw_id] = poly_latlon

def get_label_position(polygon):
    coords = [(lon, lat) for lat, lon in polygon]
    poly = Polygon(coords)
    point = poly.representative_point()
    return point.y, point.x

COLOR_MAP = {'Miskin':'#ef4444','Pra Sejahtera':'#f59e0b','Sejahtera':'#10b981'}

@st.cache_data
def load_data():
    df = pd.read_csv('hasil_prediksi_c45.csv')
    df['RW'] = pd.to_numeric(df['RW'], errors='coerce')
    df['RT'] = pd.to_numeric(df['RT'], errors='coerce')
    return df

df = load_data()

# ── FUNGSI PEMBANTU UNTUK RENDER TABEL SESUAI TEMA ────────────────────────────
def render_styled_dataframe(df_to_render, **kwargs):
    if is_light:
        styled = df_to_render.style.set_properties(**{
            'background-color': '#ffffff',
            'color': '#0f172a',
            'border-color': '#e2e8f0'
        })
        st.dataframe(styled, **kwargs)
    else:
        st.dataframe(df_to_render, **kwargs)

# ── 5. HEADER DASHBOARD ───────────────────────────────────────────────────────
header_html = """
<div class="dash-header">
    <div>
        <h1>Dashboard Penentuan Kelayakan Bantuan Sosial</h1>
        <p>Sistem Pendukung Keputusan Distribusi Bansos — Kelurahan Tanjung Perak, Kota Surabaya</p>
    </div>
    <div class="badge">{icon} {total} KK Terdata</div>
</div>
"""
st.markdown(header_html.format(icon=ICON_DB, total=f"{len(df):,}"), unsafe_allow_html=True)

# ── 6. SIDEBAR KONTROL PANEL & TOMBOL POP-UP ──────────────────────────────────
with st.sidebar:
    st.markdown("### Prediksi Real-Time")
    if st.button("Uji Warga Baru", use_container_width=True):
        popup_prediksi()
    st.markdown(f"<p style='font-size:11px; color:{MUTED_TEXT}; margin-top:-5px;'>Klik tombol diatas untuk menguji kelayakan KK baru.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Panel Kontrol Data")
    
    rw_options = sorted([int(r) for r in df['RW'].dropna().unique()])
    rw_sel = st.multiselect("Cakupan Wilayah (RW)", options=rw_options, default=rw_options,
                            format_func=lambda x: "RW {:02d}".format(int(x)))
    
    status_sel = st.multiselect("Kategori Kesejahteraan",
                                options=['Miskin','Pra Sejahtera','Sejahtera'],
                                default=['Miskin','Pra Sejahtera','Sejahtera'])
    
    history_options = ['Belum', 'Sudah']
    history_sel = st.multiselect("Riwayat Bansos KK", 
                                 options=history_options, 
                                 default=history_options,
                                 format_func=lambda x: "Belum Pernah Menerima" if x == 'Belum' else "Sudah Pernah Menerima")
    
    st.markdown("---")
    st.markdown("Informasi Analisis Model")
    st.info("Metode Pokok: **C4.5 Tree**")

df_f = df[df['RW'].isin(rw_sel) & df['PREDIKSI_LABEL'].isin(status_sel) & df['HISTORY_BANTUAN'].isin(history_sel)].copy()

total     = len(df_f) if len(df_f) > 0 else 1
miskin    = (df_f['PREDIKSI_LABEL']=='Miskin').sum()
pra       = (df_f['PREDIKSI_LABEL']=='Pra Sejahtera').sum()
sejahtera = (df_f['PREDIKSI_LABEL']=='Sejahtera').sum()

# ── 7. KOTAK INFORMASI METRIK UTAMA ───────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_total = f"""<div class="metric-card total">
        <div class="metric-top"><div class="metric-icon-wrap">{ICON_USERS}</div>
        <div class="metric-lbl">KK Terfilter</div></div>
        <div class="metric-val">{len(df_f):,} <span style="font-size:14px; color:{MUTED_TEXT}; font-weight:500;">KK</span></div>
        <div><span class="metric-pct pct-total">Total Master: {len(df):,}</span></div>
    </div>"""
    st.markdown(metric_total, unsafe_allow_html=True)

with c2:
    metric_miskin = f"""<div class="metric-card miskin">
        <div class="metric-top"><div class="metric-icon-wrap">{ICON_ALERT}</div>
        <div class="metric-lbl">Klasifikasi Miskin</div></div>
        <div class="metric-val">{miskin:,}</div>
        <div><span class="metric-pct pct-miskin">{miskin/total*100:.1f}% Porsi</span></div>
    </div>"""
    st.markdown(metric_miskin, unsafe_allow_html=True)

with c3:
    metric_pra = f"""<div class="metric-card pra">
        <div class="metric-top"><div class="metric-icon-wrap">{ICON_WARN}</div>
        <div class="metric-lbl">Pra Sejahtera</div></div>
        <div class="metric-val">{pra:,}</div>
        <div><span class="metric-pct pct-pra">{pra/total*100:.1f}% Porsi</span></div>
    </div>"""
    st.markdown(metric_pra, unsafe_allow_html=True)

with c4:
    metric_sej = f"""<div class="metric-card sejahtera">
        <div class="metric-top"><div class="metric-icon-wrap">{ICON_CHECK}</div>
        <div class="metric-lbl">Sejahtera</div></div>
        <div class="metric-val">{sejahtera:,}</div>
        <div><span class="metric-pct pct-sejahtera">{sejahtera/total*100:.1f}% Porsi</span></div>
    </div>"""
    st.markdown(metric_sej, unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ── 8. PEMETAAN SPASIAL & GRAFIK PROPORSI WILAYAH RW ──────────────────────────
col_peta, col_rw = st.columns([1.55, 1])

with col_peta:
    st.markdown('<div class="section-title"> Sebaran Wilayah Tingkat Kesejahteraan (Spasial)</div>', unsafe_allow_html=True)

    rw_stats = df_f.groupby('RW')['PREDIKSI_LABEL'].value_counts().unstack(fill_value=0)
    for col in ['Miskin','Pra Sejahtera','Sejahtera']:
        if col not in rw_stats.columns: rw_stats[col] = 0
    rw_stats['TOTAL'] = rw_stats.sum(axis=1)
    rw_stats.index = rw_stats.index.astype(int)

    m = folium.Map(location=[-7.2150, 112.7310], zoom_start=15, tiles=MAP_TILES)

    for rw_int, polygon_coords in RW_POLYGONS.items():
        lat, lon = get_label_position(polygon_coords)
        
        if rw_int in rw_stats.index:
            row = rw_stats.loc[rw_int]
            total_rw  = int(row['TOTAL'])
            miskin_rw = int(row['Miskin'])
            pra_rw    = int(row['Pra Sejahtera'])
            sej_rw    = int(row['Sejahtera'])
            pct_m     = miskin_rw / total_rw * 100 if total_rw > 0 else 0
            pct_pra   = pra_rw   / total_rw * 100 if total_rw > 0 else 0
            pct_sej   = sej_rw   / total_rw * 100 if total_rw > 0 else 0
            
            dominant  = max(
                [('Miskin', pct_m), ('Pra Sejahtera', pct_pra), ('Sejahtera', pct_sej)],
                key=lambda x: x[1]
            )[0]
            color = COLOR_MAP[dominant]
        else:
            total_rw, miskin_rw, pra_rw, sej_rw = 0, 0, 0, 0
            color = '#64748b' 

        popup_html = f"""<div style='font-family:sans-serif;font-size:13px;min-width:180px;padding:4px;color:{MAP_TEXT};background:{MAP_BG}'>
            <div style='border-bottom:1px solid {MAP_BORDER}; padding-bottom:6px; margin-bottom:6px;'>
                <b style='font-size:14px'>Data Wilayah RW {rw_int:02d}</b><br>
                <span style='color:{MUTED_TEXT}'>Total Terdata: {total_rw} KK</span>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:3px'>
                <span style='color:#ef4444; font-weight:600'>● Miskin:</span> <b>{miskin_rw} KK</b>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:3px'>
                <span style='color:#f59e0b; font-weight:600'>● Pra Sejahtera:</span> <b>{pra_rw} KK</b>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span style='color:#10b981; font-weight:600'>● Sejahtera:</span> <b>{sej_rw} KK</b>
            </div>
        </div>"""

        folium.Polygon(
            locations=polygon_coords,
            color=color, weight=2, fill=True, fill_color=color, fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip="RW {:02d} — {} KK".format(rw_int, total_rw)
        ).add_to(m)
        
        icon_html = "<div style='width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#1e293b;background:rgba(255,255,255,0.95);border-radius:50%;box-shadow:0 1px 3px rgba(0,0,0,0.4);pointer-events:none;'>{}</div>".format(rw_int)
        
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=icon_html, icon_size=(22, 22), icon_anchor=(11, 11))
        ).add_to(m)

    legend = f"""<div style='position:fixed;bottom:20px;left:20px;z-index:9999;
        background:{MAP_BG};padding:12px 16px;border-radius:10px; border: 1px solid {MAP_BORDER};
        box-shadow:0 4px 10px rgba(0,0,0,0.15);font-size:12px;font-family:sans-serif; color:{MAP_TEXT}'>
        <b style='font-size:13px'>Kelas Dominan Wilayah</b><div style='margin-top:6px'></div>
        <div style='display:flex;align-items:center;margin-bottom:4px'><div style='width:12px;height:12px;background:#ef4444;border-radius:3px;margin-right:8px'></div>Dominan Miskin</div>
        <div style='display:flex;align-items:center;margin-bottom:4px'><div style='width:12px;height:12px;background:#f59e0b;border-radius:3px;margin-right:8px'></div>Dominan Pra Sejahtera</div>
        <div style='display:flex;align-items:center;margin-bottom:4px'><div style='width:12px;height:12px;background:#10b981;border-radius:3px;margin-right:8px'></div>Dominan Sejahtera</div>
        <div style='display:flex;align-items:center;'><div style='width:12px;height:12px;background:#64748b;border-radius:3px;margin-right:8px'></div>Data Kosong / Nihil</div>
        </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    st_folium(m, width=None, height=420, returned_objects=[])

with col_rw:
    st.markdown('<div class="section-title"> Proporsi Komposisi Per Wilayah RW</div>', unsafe_allow_html=True)

    rw_plot = df_f.groupby(['RW','PREDIKSI_LABEL']).size().reset_index(name='Jumlah')
    rw_plot['RW_label'] = rw_plot['RW'].apply(lambda x: "RW {:02d}".format(int(x)))
    rw_plot = rw_plot.sort_values('RW')

    fig_rw = px.bar(
        rw_plot, x='Jumlah', y='RW_label',
        color='PREDIKSI_LABEL', orientation='h',
        color_discrete_map=COLOR_MAP,
        labels={'PREDIKSI_LABEL':'Kategori','RW_label':'','Jumlah':'Jumlah KK'},
        category_orders={'PREDIKSI_LABEL':['Miskin','Pra Sejahtera','Sejahtera']},
        template=PLOTLY_TEMPLATE
    )
    fig_rw.update_layout(
        height=420, margin=dict(l=0,r=0,t=10,b=0), font=dict(color=CHART_FONT_COLOR),
        legend=dict(title="", orientation="h", y=1.06, x=0, font=dict(size=11, color=CHART_FONT_COLOR)),
        yaxis=dict(categoryorder='category ascending', tickfont=dict(size=11, color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR)),
        xaxis=dict(tickfont=dict(size=10, color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR)),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', bargap=0.3
    )
    st.plotly_chart(fig_rw, use_container_width=True, theme=None)

# ── 9. SECTION SISTEM PENDUKUNG KEPUTUSAN (SPK) PRIORITAS UTAMA ────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title"> Urutan Rekomendasi Prioritas Penyaluran Bansos</div>', unsafe_allow_html=True)
st.write("Daftar di bawah mengekstrak Kepala Keluarga (KK) hasil klasifikasi **Miskin** dan berstatus **Belum Pernah Menerima Bantuan**. Sistem menyusun rangking otomatis berdasarkan Pendapatan Perkapita terkecil dan Jumlah Jiwa terbanyak.")

df_spk = df_f[(df_f['PREDIKSI_LABEL'] == 'Miskin') & (df_f['HISTORY_BANTUAN'] == 'Belum')].copy()
df_spk_sorted = df_spk.sort_values(by=['PENDAPATAN_PERKAPITA', 'JML_JIWA'], ascending=[True, False])

if not df_spk_sorted.empty:
    csv_data = df_spk_sorted[['NAMA','RW','RT','JML_JIWA','IJAZAH_TERAKHIR','PEKERJAAN','TOTAL_PENDAPATAN','PENDAPATAN_PERKAPITA']].to_csv(index=False)
    st.download_button(
        label=" Unduh Berkas Hasil Prioritas Kelurahan (.CSV)",
        data=csv_data,
        file_name="Rekomendasi_Prioritas_Bansos_Tanjung_Perak.csv",
        mime="text/csv"
    )
    
    df_spk_display = df_spk_sorted[['NAMA','RW','RT','JML_JIWA','IJAZAH_TERAKHIR','PEKERJAAN','TOTAL_PENDAPATAN','PENDAPATAN_PERKAPITA','PROBABILITAS']].rename(columns={
        'NAMA':'Nama Kepala Keluarga','RW':'RW','RT':'RT','JML_JIWA':'Beban Jiwa',
        'IJAZAH_TERAKHIR':'Pendidikan','PEKERJAAN':'Bidang Pekerjaan','TOTAL_PENDAPATAN':'Total Gaji (Rp)',
        'PENDAPATAN_PERKAPITA':'Gaji/Kapita (Rp)','PROBABILITAS':'Akurasi Model'
    })
    
    render_styled_dataframe(df_spk_display, use_container_width=True, height=260, hide_index=True)
    
    st.caption("Ditemukan **{:,}** KK berstatus prioritas tinggi yang membutuhkan intervensi darurat kelurahan.".format(len(df_spk_sorted)))
else:
    st.success("Sempurna! Tidak ditemukan kandidat warga berstatus Miskin yang belum tersentuh bantuan pada cakupan filter aktif saat ini.")

# ── 10. ANALISIS KORELASI VARIABEL FAKTOR ─────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title"> Analisis Korelasi Faktor Pendidikan, Sektor Kerja & Pendapatan</div>', unsafe_allow_html=True)

cv1, cv2, cv3 = st.columns(3)

with cv1:
    ijazah_order = ['Tidak punya ijazah','SD/sederajat','SMP/sederajat','SMA/sederajat','D1/D2/D3','D4/S1','S2/S3']
    ij = df_f.groupby(['IJAZAH_TERAKHIR','PREDIKSI_LABEL']).size().reset_index(name='n')
    fig_ij = px.bar(ij, x='n', y='IJAZAH_TERAKHIR', color='PREDIKSI_LABEL',
                    orientation='h', color_discrete_map=COLOR_MAP,
                    title='Tingkat Pendidikan Terakhir',
                    labels={'n':'Jumlah KK','IJAZAH_TERAKHIR':''},
                    category_orders={'IJAZAH_TERAKHIR':ijazah_order, 'PREDIKSI_LABEL':['Miskin','Pra Sejahtera','Sejahtera']},
                    template=PLOTLY_TEMPLATE)
    fig_ij.update_layout(showlegend=False, height=290, margin=dict(l=0,r=0,t=40,b=0), font=dict(color=CHART_FONT_COLOR),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    fig_ij.update_xaxes(tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    fig_ij.update_yaxes(tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    st.plotly_chart(fig_ij, use_container_width=True, theme=None)

with cv2:
    top10 = df_f['PEKERJAAN'].value_counts().head(10).index
    pek   = df_f[df_f['PEKERJAAN'].isin(top10)]
    pek_g = pek.groupby(['PEKERJAAN','PREDIKSI_LABEL']).size().reset_index(name='n')
    fig_pek = px.bar(pek_g, x='n', y='PEKERJAAN', color='PREDIKSI_LABEL',
                     orientation='h', color_discrete_map=COLOR_MAP,
                     title='Top 10 Sektor Mata Pencaharian',
                     labels={'n':'Jumlah KK','PEKERJAAN':''},
                     category_orders={'PREDIKSI_LABEL':['Miskin','Pra Sejahtera','Sejahtera']},
                     template=PLOTLY_TEMPLATE)
    fig_pek.update_layout(showlegend=False, height=290, margin=dict(l=0,r=0,t=40,b=0), font=dict(color=CHART_FONT_COLOR),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    fig_pek.update_xaxes(tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    fig_pek.update_yaxes(tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    st.plotly_chart(fig_pek, use_container_width=True, theme=None)

with cv3:
    fig_box = px.box(df_f, x='PREDIKSI_LABEL', y='PENDAPATAN_PERKAPITA',
                     color='PREDIKSI_LABEL', color_discrete_map=COLOR_MAP,
                     title='Rentang Distribusi Nominal Gaji Per Kapita',
                     labels={'PREDIKSI_LABEL':'','PENDAPATAN_PERKAPITA':'Pendapatan (Rp/Bulan)'},
                     category_orders={'PREDIKSI_LABEL':['Miskin','Pra Sejahtera','Sejahtera']},
                     template=PLOTLY_TEMPLATE)
    fig_box.update_layout(showlegend=False, height=290, margin=dict(l=0,r=0,t=40,b=0), font=dict(color=CHART_FONT_COLOR),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    fig_box.update_xaxes(tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    fig_box.update_yaxes(tickformat=',.0f', tickprefix='Rp ', tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR))
    st.plotly_chart(fig_box, use_container_width=True, theme=None)

# ── 11. DIREKTORI MASTER DATA DIREKTORI WARGA TERFILTER ────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title"> Direktori Induk Database Kepala Keluarga Aktif</div>', unsafe_allow_html=True)

cs1, cs2, cs3 = st.columns([2.5, 1, 1])
with cs1:
    search = st.text_input(" Pencarian Spesifik Nama / Alamat", placeholder="Ketik potongan nama warga atau alamat...")
with cs2:
    sort_col = st.selectbox("Urutkan Berdasarkan Parameter", ['RW','RT','PENDAPATAN_PERKAPITA','JML_JIWA','PREDIKSI_LABEL'])
with cs3:
    sort_asc = st.radio("Sifat Arah Urutan", ['Menaik (Asc)','Menurun (Desc)'], horizontal=True) == 'Menaik (Asc)'

df_tbl = df_f.copy()
if search:
    df_tbl = df_tbl[df_tbl['NAMA'].str.contains(search, case=False, na=False) | df_tbl['ALAMAT'].str.contains(search, case=False, na=False)]
df_tbl = df_tbl.sort_values(sort_col, ascending=sort_asc)

df_tbl_display = df_tbl[['NAMA','RW','RT','JML_JIWA','IJAZAH_TERAKHIR','PEKERJAAN','PENDAPATAN_PERKAPITA','HISTORY_BANTUAN','PREDIKSI_LABEL','PROBABILITAS']].rename(columns={
    'NAMA':'Nama Kepala Keluarga','RW':'RW','RT':'RT','JML_JIWA':'Jml. Jiwa',
    'IJAZAH_TERAKHIR':'Pendidikan','PEKERJAAN':'Bidang Pekerjaan',
    'PENDAPATAN_PERKAPITA':'Pendapatan/Kapita (Rp)','HISTORY_BANTUAN':'Riwayat Bansos',
    'PREDIKSI_LABEL':'Kategori Prediksi','PROBABILITAS':'Akurasi Model'
})

render_styled_dataframe(df_tbl_display, use_container_width=True, height=350, hide_index=True)

# ── 12. TABEL MATRIKS MATURITAS TINGKAT WILAYAH RW ────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-title"> Tabel Matriks Ringkasan Akumulasi Angka per Wilayah RW</div>', unsafe_allow_html=True)

rw_sum = df_f.groupby('RW').agg(
    Total_KK        =('PREDIKSI_LABEL','count'),
    Miskin          =('PREDIKSI_LABEL', lambda x: (x=='Miskin').sum()),
    Pra_Sejahtera   =('PREDIKSI_LABEL', lambda x: (x=='Pra Sejahtera').sum()),
    Sejahtera       =('PREDIKSI_LABEL', lambda x: (x=='Sejahtera').sum()),
    Rata_Pendapatan =('PENDAPATAN_PERKAPITA','mean'),
    Rata_Jiwa       =('JML_JIWA','mean'),
).reset_index()
rw_sum['% Kerentanan (Miskin)'] = (rw_sum['Miskin']/rw_sum['Total_KK']*100).round(1)
rw_sum['Rata_Pendapatan']       = rw_sum['Rata_Pendapatan'].round(0).astype(int)
rw_sum['Rata_Jiwa']             = rw_sum['Rata_Jiwa'].round(1)
rw_sum['RW']                    = rw_sum['RW'].apply(lambda x: "RW {:02d}".format(int(x)))

df_rw_sum_display = rw_sum.rename(columns={
    'RW':'Batas Wilayah','Total_KK':'Total KK Terdata',
    'Miskin':'Jumlah Miskin','Pra_Sejahtera':'Jumlah Pra Sejahtera','Sejahtera':'Jumlah Sejahtera',
    '% Kerentanan (Miskin)':'Persentase Miskin (%)',
    'Rata_Pendapatan':'Rerata Pendapatan/Kapita (Rp)',
    'Rata_Jiwa':'Rerata Beban Jiwa/KK'
})

render_styled_dataframe(df_rw_sum_display, use_container_width=True, hide_index=True)

# Footer Instansional
st.markdown(f"""
<div style='text-align:center; color:{MUTED_TEXT}; font-size:13px; margin-top:3rem; padding:1.5rem; border-top:1px solid {MAP_BORDER};'>
    <b>Sistem Pendukung Keputusan Penentuan Kelayakan Penyaluran Bantuan Sosial</b><br>
    Model Klasifikasi Utama: C4.5 Decision Tree
</div>""", unsafe_allow_html=True)