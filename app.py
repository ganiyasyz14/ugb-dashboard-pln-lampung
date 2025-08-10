# app.py
"""
Dashboard Geo-Monitor UGB PT. PLN UID Lampung
Aplikasi utama Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# Import konfigurasi dan utilities
from config import *
from utils.data_processor import *

# ===== KONFIGURASI STREAMLIT =====
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# ===== GLOBAL STATE NAVIGASI (pola DASH_INSPEKSI) =====
if "page" not in st.session_state:
    st.session_state.page = "upload"

def set_page(page_name: str):
    st.session_state.page = page_name

# ===== UTIL: Konversi gambar ke base64 =====
def image_to_base64(image: Image.Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def normalize_status(s: str) -> str:
    """Normalisasi STATUS agar 'STANDBY' == 'STAND BY'."""
    if s is None:
        return ""
    x = str(s).strip().upper()
    if x.replace(" ", "") == "STANDBY":
        return "STAND BY"
    if x in ("RUSAK", "TERPASANG", "STAND BY"):
        return x
    return x

# ===== CUSTOM CSS (pola INSPEKSI + revisi header dua baris) =====
st.markdown(
    """
    <style>
    /* Compact container spacing */
    .block-container { padding: 1.5rem 2rem 2rem 2rem; }
    /* Divider style */
    hr { height: 3px !important; background-color: #5e5e5e !important; border: none !important; margin: 0 !important; }

    /* Header container pakai grid agar judul betul-betul di tengah */
    .header-container {
        background-color: #007C8F;
        padding: 8px 22px;
        border-radius: 10px;
        display: grid;
        grid-template-columns: 1fr 2fr 1fr; /* kolom kiri - judul - kanan */
        align-items: center;              /* vertikal center untuk seluruh isi */
        gap: 14px;
        margin-top: 72px;                /* turunkan header dari atas */
        margin-bottom: 18px;
        min-height: 96px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Logo containers */
    .logo-container { display: flex; align-items: center; min-width: 140px; }
    .logo-left { justify-content: flex-start; }
    .logo-right { justify-content: flex-end; }

    /* Ukuran logo konsisten, PLN sedikit lebih besar sesuai permintaan */
    .logo-img-dinantara, .logo-img-pln {
        height: 72px;
        max-height: 72px;
        width: auto;
        max-width: 200px;
        object-fit: contain;
        display: block;
    }
    .logo-img-pln { height: 90px; max-height: 90px; }

    /* Geser Danantara sedikit ke kanan agar tidak terlalu menempel kiri */
    .logo-img-dinantara { margin-left: 28px; }

    /* Pusatkan judul di kolom tengah lalu geser sedikit ke kanan mendekati logo PLN */
    .title-container { text-align: center; display: flex; align-items: center; justify-content: center; transform: translate(18px, 6px); }
    .main-title { color: white; margin: 0; line-height: 1.1; letter-spacing: 0.5px; }
    /* Dua baris judul sama besar */
    .main-title .title-line1 { display: block; font-size: 40px; font-weight: 800; }
    .main-title .title-line2 { display: block; font-size: 40px; font-weight: 800; }

    /* Info container (untuk Upload) */
    .info-container {
        border: 1.5px solid #007C8F;
        background-color: transparent;
        padding: 25px;
        border-radius: 10px;
        margin-top: 10px;
    }
    .info-container p { margin-bottom: 10px; }
    .info-container ul { list-style-position: inside; padding-left: 5px; }

    /* ==== Tambahan: gaya SLICER & KPI seperti DASH_INSPEKSI ==== */
    .filter-header { color: #007C8F; font-weight: bold; font-size: 16px; margin-bottom: 0px; display: flex; align-items: center; gap: 8px; }
    /* Lower the selectboxes so they align with the Apply/Reset buttons */
    div[data-testid="stSelectbox"] { margin-top: 12px !important; margin-bottom: 8px !important; }
    div[data-testid="stButton"] > button { height: 38px !important; padding: 8px 16px !important; margin-top: 0px !important; }
    .button-container { margin-top: 8px; height: 38px; display: flex; align-items: flex-start; }
    .metric-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 20px; text-align: center; border: 1px solid #e1e5e9; margin-bottom: 10px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
    .metric-number { font-size: 2.5em; font-weight: bold; margin-bottom: 8px; color: #2c3e50; }
    .metric-label { font-size: 0.9em; color: #7f8c8d; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .color-primary { color: #3498db; } .color-success { color: #27ae60; } .color-warning { color: #f39c12; } .color-danger { color: #e74c3c; } .color-info { color: #8e44ad; }

    /* Responsif */
    @media (max-width: 1200px) {
        .logo-img-dinantara, .logo-img-pln { height: 64px; max-height: 64px; }
        .logo-img-pln { height: 76px; max-height: 76px; }
        .logo-img-dinantara { margin-left: 20px; }
        .main-title .title-line1 { font-size: 36px; }
        .main-title .title-line2 { font-size: 36px; }
        .header-container { padding: 8px 18px; min-height: 88px; margin-top: 56px; }
    /* geser sedikit ke kanan & turun pada layar besar */
    .title-container { transform: translate(14px, 4px); }
    }
    @media (max-width: 992px) {
        .logo-container { min-width: 120px; }
        .logo-img-dinantara, .logo-img-pln { height: 56px; max-height: 56px; }
        .logo-img-pln { height: 68px; max-height: 68px; }
        .logo-img-dinantara { margin-left: 16px; }
        .main-title .title-line1 { font-size: 32px; }
        .main-title .title-line2 { font-size: 32px; }
        .header-container { padding: 6px 16px; min-height: 80px; margin-top: 44px; }
    .title-container { transform: translate(10px, 3px); }
    }
    @media (max-width: 768px) {
        .header-container { padding: 6px 14px; grid-template-columns: 1fr 2fr 1fr; min-height: 72px; margin-top: 32px; }
        .logo-img-dinantara, .logo-img-pln { height: 50px; max-height: 50px; }
        .logo-img-pln { height: 60px; max-height: 60px; }
        .logo-img-dinantara { margin-left: 12px; }
        .main-title .title-line1 { font-size: 26px; }
        .main-title .title-line2 { font-size: 26px; }
    .title-container { transform: translate(6px, 2px); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== HEADER (identik gaya INSPEKSI, judul 2 baris) =====
def display_header():
    try:
        logo_dinantara = Image.open("assets/LOGO DANANTARA.png")
        logo_pln = Image.open("assets/LOGO PLN.png")
        b64_logo_dinantara = image_to_base64(logo_dinantara)
        b64_logo_pln = image_to_base64(logo_pln)
    except Exception:
        b64_logo_dinantara = b64_logo_pln = None

    if b64_logo_dinantara and b64_logo_pln:
        st.markdown(
            f"""
            <div class=\"header-container\"> 
                <div class=\"logo-container logo-left\"> 
                    <img src=\"data:image/png;base64,{b64_logo_dinantara}\" class=\"logo-img-dinantara\" />
                </div>
                <div class=\"title-container\">
                    <h1 class=\"main-title\">
                        <span class=\"title-line1\">Dashboard Geo-Monitor UGB</span>
                        <span class=\"title-line2\">PT. PLN UID Lampung</span>
                    </h1>
                </div>
                <div class=\"logo-container logo-right\"> 
                    <img src=\"data:image/png;base64,{b64_logo_pln}\" class=\"logo-img-pln\" />
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ===== SIDEBAR NAVIGASI (tombol session_state) =====
def render_sidebar_nav():
    st.sidebar.markdown("<h1 style='text-align: center; font-size: 24px;'>Navigasi Aplikasi</h1>", unsafe_allow_html=True)
    st.sidebar.button("📁 Upload Data", on_click=set_page, args=("upload",), use_container_width=True)
    st.sidebar.button("📊 Dashboard Utama", on_click=set_page, args=("dashboard",), use_container_width=True)
    st.sidebar.button("📋 Rekapitulasi Data", on_click=set_page, args=("recap",), use_container_width=True)
    st.sidebar.markdown("---")

# ===== HALAMAN UPLOAD DATA (gaya INSPEKSI, konten UGB) =====
def page_upload_data():
    st.header("📁 Upload Data", divider="rainbow")
    st.markdown(
        """
        <div class="info-container">
            <p><strong>Silakan unggah file ugb dari hasil lapangan.</strong></p>
            <ul>
                <li>File boleh berisi 1–4 sheet: <b>UGB UP3 KARANG, METRO, KOTABUMI, PRINGSEWU</b></li>
                <li>Header di baris ke-1, data mulai dari baris ke-2</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Pilih file:",
        type=["xlsx", "xlsm"],
        help="Maksimal 200 MB (sesuai batas Streamlit default)"
    )

    if uploaded_file is not None:
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0, text="Memulai...")
            try:
                # Langsung proses tanpa ringkasan sheet
                progress_bar.progress(10, text="Menyiapkan file untuk diproses...")
                progress_bar.progress(30, text="Membaca & mengekstrak data per sheet yang valid...")
                success, message, df = process_excel_file(uploaded_file)
                progress_bar.progress(60, text="Validasi dan persiapan data...")
                if success:
                    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
                    # Simpan langsung ke session apa adanya (tanpa deduplikasi & tanpa merge)
                    progress_bar.progress(75, text="Menyiapkan data untuk disimpan...")
                    try:
                        current = df.copy()
                        # Re-number kolom NO (override apapun yang ada di file)
                        if 'NO' in current.columns:
                            current = current.drop(columns=['NO'])
                        current.insert(0, 'NO', range(1, len(current) + 1))
                        st.session_state['ugb_db'] = current
                    except Exception as me:
                        st.warning(f"Peringatan saat merge session: {me}")

                    progress_bar.progress(88, text="Menyimpan salinan cadangan (CSV)...")
                    if save_to_database(st.session_state['ugb_db'], DATABASE_PATH):
                        progress_bar.progress(100, text="Selesai 100%!")
                        st.success(f"✅ {message}")
                        # Bersihkan cache dan reset filter agar tampilan tidak menduplikasi data lama
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        for key in [
                            'ugb_filter_state', 'temp_ugb_filter',
                            'ugb_recap_filter_state', 'temp_ugb_recap_filter'
                        ]:
                            if key in st.session_state:
                                del st.session_state[key]
                        # (Hapus tombol unduh database dari laman Upload sesuai permintaan)
                        with st.expander("🔍 Preview Data (10 baris pertama dari database aktif)", expanded=False):
                            st.dataframe(st.session_state['ugb_db'].head(10), use_container_width=True, height=320)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.button("📊 Dashboard Utama", on_click=set_page, args=("dashboard",), use_container_width=True)
                        with col2:
                            st.button("📋 Rekapitulasi Data", on_click=set_page, args=("recap",), use_container_width=True)
                        with col3:
                            st.button("🔄 Upload Lagi", on_click=set_page, args=("upload",), use_container_width=True)
                    else:
                        progress_bar.empty(); st.error("❌ Gagal menyimpan ke database")
                else:
                    progress_bar.empty(); st.error(f"❌ Error: {message}")
            except Exception as e:
                progress_bar.empty(); st.error(f"❌ Gagal memproses file: {str(e)}")

# ===== HALAMAN DASHBOARD UTAMA =====
def page_dashboard():
    """Halaman dashboard utama: Slicer -> KPI Cards -> Peta (gaya DASH_INSPEKSI)"""
    st.header("📊 Dashboard Utama", divider="rainbow")

    # Load data (prefer session)
    if 'ugb_db' in st.session_state and isinstance(st.session_state['ugb_db'], pd.DataFrame) and not st.session_state['ugb_db'].empty:
        df = st.session_state['ugb_db']
    else:
        df = load_database(DATABASE_PATH)

    if df.empty:
        st.markdown(
            """
            <div style="text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                        border-radius: 15px; margin: 40px 0;">
                <h2 style="color: #666; margin-bottom: 20px;">📊 Dashboard Siap Digunakan</h2>
                <p style="color: #888; font-size: 18px; margin-bottom: 30px;">
                    Belum ada data UGB yang diupload. Silakan upload data terlebih dahulu untuk melihat visualisasi.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.button("📤 Upload Data Sekarang", on_click=set_page, args=("upload",), use_container_width=True)
        return

    # Siapkan kolom STATUS yang sudah dinormalisasi
    df_ui = df.copy()
    df_ui['STATUS_NORM'] = df_ui['STATUS'].apply(normalize_status)

    # ===== FILTER SECTION (persis pola Apply/Reset) =====
    # Inisialisasi state
    if 'ugb_filter_state' not in st.session_state:
        st.session_state.ugb_filter_state = { 'UP3': 'Semua', 'ULP': 'Semua', 'STATUS': 'Semua' }
    if 'temp_ugb_filter' not in st.session_state:
        st.session_state.temp_ugb_filter = st.session_state.ugb_filter_state.copy()

    # Opsi filter dari data (gunakan kolom yang tersedia)
    up3_opts = ['Semua'] + sorted([x for x in df_ui['UP3'].dropna().astype(str).unique()]) if 'UP3' in df_ui.columns else ['Semua']
    ulp_opts = ['Semua'] + sorted([x for x in df_ui['ULP'].dropna().astype(str).unique()]) if 'ULP' in df_ui.columns else ['Semua']
    status_opts = ['Semua'] + ['RUSAK', 'STAND BY', 'TERPASANG']

    with st.container():
        # Reorder to match DASH_INSPEKSI: ULP, UP3, STATUS | Apply | Reset
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        with col1:
            st.markdown('<div class="filter-header">🏪 ULP</div>', unsafe_allow_html=True)
            sel_ulp = st.selectbox("ULP", ulp_opts, index=ulp_opts.index(st.session_state.temp_ugb_filter['ULP']) if st.session_state.temp_ugb_filter['ULP'] in ulp_opts else 0, key="ugb_temp_ulp", label_visibility="collapsed")
            st.session_state.temp_ugb_filter['ULP'] = sel_ulp
        with col2:
            st.markdown('<div class="filter-header">🏢 UP3</div>', unsafe_allow_html=True)
            sel_up3 = st.selectbox("UP3", up3_opts, index=up3_opts.index(st.session_state.temp_ugb_filter['UP3']) if st.session_state.temp_ugb_filter['UP3'] in up3_opts else 0, key="ugb_temp_up3", label_visibility="collapsed")
            st.session_state.temp_ugb_filter['UP3'] = sel_up3
        with col3:
            st.markdown('<div class="filter-header">⚡ STATUS</div>', unsafe_allow_html=True)
            sel_status = st.selectbox("STATUS", status_opts, index=status_opts.index(st.session_state.temp_ugb_filter['STATUS']) if st.session_state.temp_ugb_filter['STATUS'] in status_opts else 0, key="ugb_temp_status", label_visibility="collapsed")
            st.session_state.temp_ugb_filter['STATUS'] = sel_status
        with col4:
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            if st.button("🔍 Apply Filter", use_container_width=True, key="ugb_apply_filter"):
                st.session_state.ugb_filter_state = st.session_state.temp_ugb_filter.copy()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col5:
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            if st.button("🔄 Reset Filter", use_container_width=True, key="ugb_reset_filter"):
                default_filter = { 'UP3': 'Semua', 'ULP': 'Semua', 'STATUS': 'Semua' }
                st.session_state.ugb_filter_state = default_filter.copy()
                st.session_state.temp_ugb_filter = default_filter.copy()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Terapkan filter ke data
    f = st.session_state.ugb_filter_state
    filtered = df_ui.copy()
    if f['UP3'] != 'Semua' and 'UP3' in filtered.columns:
        filtered = filtered[filtered['UP3'] == f['UP3']]
    if f['ULP'] != 'Semua' and 'ULP' in filtered.columns:
        filtered = filtered[filtered['ULP'] == f['ULP']]
    if f['STATUS'] != 'Semua':
        filtered = filtered[filtered['STATUS_NORM'] == f['STATUS']]

    if len(filtered) != len(df_ui):
        st.info(f"📊 Menampilkan {len(filtered)} dari {len(df_ui)} total data berdasarkan filter")

    # ===== KPI CARDS (gaya INSPEKSI) =====
    def count_nonempty(series):
        return series.astype(str).str.strip().replace({'None': ''}).ne('').sum()

    total_ugb = count_nonempty(filtered['PENOMORAN UGB BARU']) if 'PENOMORAN UGB BARU' in filtered.columns else len(filtered)
    domain_mask = filtered['STATUS_NORM'].isin(['RUSAK', 'STAND BY', 'TERPASANG'])
    denom = int(domain_mask.sum()) if 'STATUS_NORM' in filtered.columns else 0
    def pct(val):
        return (val/denom*100) if denom > 0 else 0

    rusak = int((filtered['STATUS_NORM'] == 'RUSAK').sum())
    stand_by = int((filtered['STATUS_NORM'] == 'STAND BY').sum())
    terpasang = int((filtered['STATUS_NORM'] == 'TERPASANG').sum())

    pct_rusak = pct(rusak)
    pct_standby = pct(stand_by)
    pct_terpasang = pct(terpasang)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number color-primary">{total_ugb:,}</div>
            <div class="metric-label">TOTAL UGB</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number color-danger">{pct_rusak:.1f}%</div>
            <div class="metric-label">% UGB RUSAK</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number color-warning">{pct_standby:.1f}%</div>
            <div class="metric-label">% UGB STAND BY</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number color-success">{pct_terpasang:.1f}%</div>
            <div class="metric-label">% UGB TERPASANG</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <hr style="height:3px;border:none;background-color:#5e5e5e;margin:10px 0;"/>
    """, unsafe_allow_html=True)

    # ===== PETA INTERAKTIF (Folium) =====
    st.markdown("### 🗺️ Peta Tagging UGB")
    map_height = 500  # fixed height requested

    if filtered.empty:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter")
        return

    map_center = MAP_CONFIG['default_center'] if 'MAP_CONFIG' in globals() else [-5.3971, 105.2663]
    m = folium.Map(location=map_center, zoom_start=MAP_CONFIG.get('default_zoom', 9) if 'MAP_CONFIG' in globals() else 9, tiles='OpenStreetMap')

    # Kelompokkan baris berdasarkan koordinat (dibulatkan 6 desimal agar konsisten)
    from collections import defaultdict
    import re
    groups = defaultdict(list)
    for _, row in filtered.iterrows():
        lat, lon = parse_coordinates(str(row.get('KOORDINAT TAGGING', '')))
        if lat is None or lon is None:
            continue
        key = (round(float(lat), 6), round(float(lon), 6))
        groups[key].append(row)

    def _peno_suffix(s: str) -> int:
        m = re.search(r'(\d+)$', str(s))
        return int(m.group(1)) if m else 0

    def _status_color_for_group(rows) -> str:
        # Prioritas warna: RUSAK > TERPASANG > STAND BY
        statuses = {str(r.get('STATUS_NORM','')) for r in rows}
        if 'RUSAK' in statuses: return 'red'
        if 'TERPASANG' in statuses: return 'orange'
        return 'green'

    def _build_tooltip_html(rows) -> str:
        # Urutkan untuk membaca pergerakan: tanggal -> suffix penomoran -> NO
        dfc = pd.DataFrame(rows)
        if 'TANGGAL TERPASANG' in dfc.columns:
            try:
                dfc['_ts_'] = pd.to_datetime(dfc['TANGGAL TERPASANG'], errors='coerce')
            except Exception:
                dfc['_ts_'] = pd.NaT
        else:
            dfc['_ts_'] = pd.NaT
        dfc['_peno_'] = dfc['PENOMORAN UGB BARU'].apply(_peno_suffix) if 'PENOMORAN UGB BARU' in dfc.columns else 0
        dfc['_no_'] = dfc['NO'] if 'NO' in dfc.columns else range(1, len(dfc)+1)
        dfc = dfc.sort_values(by=['_ts_', '_peno_', '_no_'], ascending=[True, True, True])

        dot_color = { 'STAND BY': '#28a745', 'RUSAK': '#dc3545', 'TERPASANG': '#ffc107' }
        arrow_up = '&#8593;'; arrow_down = '&#8595;'
        items = []
        prev = None
        for _, r in dfc.iterrows():
            status = str(r.get('STATUS_NORM',''))
            pn = str(r.get('PENOMORAN UGB BARU','-'))
            sn = str(r.get('NO SERI','-'))
            cap_val = r.get('KAPASITAS','-')
            cap_str = str(cap_val)
            if prev is not None:
                try:
                    now = float(str(cap_val).replace(',','.'))
                    prv = float(str(prev.get('KAPASITAS','')).replace(',','.'))
                    if pd.notna(now) and pd.notna(prv):
                        if now > prv: cap_str = f"{arrow_up} {cap_str}"
                        elif now < prv: cap_str = f"{arrow_down} {cap_str}"
                except Exception:
                    pass
            items.append(
                f"""
                <div style='margin:6px 0;'>
                  <span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{dot_color.get(status,'#6c757d')};margin-right:6px;vertical-align:middle'></span>
                  <span style='font-weight:700;'>{pn}</span>
                  <div style='margin-left:14px;color:#333'>Capacity: <b>{cap_str}</b></div>
                  <div style='margin-left:14px;color:#333'>No Seri: {sn}</div>
                </div>
                """
            )
            prev = r
        html = """
        <div style='font-family: Inter, Roboto, Arial; font-size:12px; max-width: 280px;'>
          <div style='font-weight:800; margin-bottom:6px; color:#1f4e79;'>UGB pada Koordinat Ini</div>
          {}
        </div>
        """.format("".join(items))
        return html

    marker_count = 0
    for (lat, lon), rows in groups.items():
        marker_count += 1
        color = _status_color_for_group(rows)
        tooltip_html = _build_tooltip_html(rows)
        # Popup ringkas: tampilkan entri terakhir sebagai ringkasan
        try:
            _df_last = pd.DataFrame(rows).copy()
            if 'NO' in _df_last.columns:
                _df_last = _df_last.sort_values(by=['NO'])
            last = _df_last.iloc[-1]
        except Exception:
            last = rows[-1]
        nomor = last.get('PENOMORAN UGB BARU','-')
        kapasitas = last.get('KAPASITAS','-')
        ulp = last.get('ULP','-')
        status = last.get('STATUS_NORM','')
        popup_text = f"""
        <div style=\"font-family: Arial; width: 260px;\">
            <h4 style=\"color: #1f4e79; margin-bottom: 10px;\">🔧 {nomor}</h4>
            <hr style=\"margin: 10px 0;\">
            <p><b>⚡ Kapasitas:</b> {kapasitas}</p>
            <p><b>📊 Status:</b> <span>{status}</span></p>
            <p><b>🏪 ULP:</b> {ulp}</p>
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=color, icon='bolt', prefix='fa'),
            tooltip=folium.Tooltip(tooltip_html, sticky=True, direction='top')
        ).add_to(m)

    # State untuk menentukan apakah panel kanan ditampilkan
    if 'ugb_show_side_panel' not in st.session_state:
        st.session_state.ugb_show_side_panel = False
    want_panel = bool(st.session_state.ugb_show_side_panel)

    # Helper: cari semua entri pada koordinat yang sama (klik)
    def _find_cluster(df_source: pd.DataFrame, map_state_dict):
        # Ambil klik terakhir dari map_state; jika tidak ada, coba dari session_state
        lc = None
        if map_state_dict and isinstance(map_state_dict, dict):
            lc = map_state_dict.get('last_clicked')
        if not lc:
            lc = st.session_state.get('ugb_last_clicked')
        else:
            # simpan agar bertahan saat rerun
            st.session_state['ugb_last_clicked'] = lc
        if not lc:
            return None, pd.DataFrame()
        lat = lc.get('lat'); lon = lc.get('lng')
        if lat is None or lon is None:
            return None, pd.DataFrame()
        eps = 1e-6
        def same_coord(r):
            a,b = parse_coordinates(str(r.get('KOORDINAT TAGGING','')))
            if a is None or b is None:
                return False
            return abs(a - float(lat)) < eps and abs(b - float(lon)) < eps
        msk = df_source.apply(same_coord, axis=1)
        return (float(lat), float(lon)), df_source[msk].copy()

    # Render peta dan panel adaptif
    map_state = None
    if want_panel:
        col_map, col_side = st.columns([7,5])
        with col_map:
            if marker_count > 0:
                try:
                    map_state = st_folium(m, height=map_height, returned_objects=["last_clicked"], use_container_width=True)
                except TypeError:
                    map_state = st_folium(m, height=map_height, returned_objects=["last_clicked"]) 
                st.success(f"🗺️ Menampilkan {marker_count} marker UGB di peta")
            else:
                st.warning("⚠️ Tidak ada koordinat yang valid untuk ditampilkan di peta")
        with col_side:
            coord, cluster_df = _find_cluster(filtered, map_state)
            has_cluster = cluster_df is not None and not cluster_df.empty
            if not has_cluster:
                # Jika panel aktif tapi tidak ada pilihan, matikan dan rerun agar map full width
                st.session_state.ugb_show_side_panel = False
                st.rerun()
            # Jika ada, render panel
            if has_cluster:
                # Urutkan untuk memudahkan membaca pergerakan
                dfc = cluster_df.copy()
                if 'TANGGAL TERPASANG' in dfc.columns:
                    try:
                        dfc['_ts_'] = pd.to_datetime(dfc['TANGGAL TERPASANG'], errors='coerce')
                    except Exception:
                        dfc['_ts_'] = pd.NaT
                else:
                    dfc['_ts_'] = pd.NaT
                import re
                def peno_key(s):
                    m = re.search(r'(\d+)$', str(s))
                    return int(m.group(1)) if m else 0
                if 'PENOMORAN UGB BARU' in dfc.columns:
                    dfc['_peno_'] = dfc['PENOMORAN UGB BARU'].apply(peno_key)
                else:
                    dfc['_peno_'] = 0
                dfc['_no_'] = dfc['NO'] if 'NO' in dfc.columns else range(1, len(dfc)+1)
                dfc = dfc.sort_values(by=['_ts_', '_peno_', '_no_'], ascending=[True, True, True])

                # Bangun HTML panel
                dot_color = { 'STAND BY': '#28a745', 'RUSAK': '#dc3545', 'TERPASANG': '#ffc107' }
                items = []
                prev = None
                arrow_up = '&#8593;'; arrow_down = '&#8595;'
                for _, r in dfc.iterrows():
                    status = str(r.get('STATUS_NORM',''))
                    pn = str(r.get('PENOMORAN UGB BARU','-'))
                    sn = str(r.get('NO SERI','-'))
                    cap_val = r.get('KAPASITAS','-')
                    cap_str = str(cap_val)
                    if prev is not None:
                        try:
                            now = float(str(cap_val).replace(',','.'))
                            prv = float(str(prev.get('KAPASITAS','')).replace(',','.'))
                            if pd.notna(now) and pd.notna(prv):
                                if now > prv: cap_str = f"{arrow_up} {cap_str}"
                                elif now < prv: cap_str = f"{arrow_down} {cap_str}"
                        except Exception:
                            pass
                    def diff(label, val, prev_val):
                        if prev is not None and str(val) != str(prev_val):
                            return f'<div><b>{label}:</b> <span style="color:#ff8c00">{val}</span> <span style="color:#888">(sebelumnya: {prev_val})</span></div>'
                        return f'<div><b>{label}:</b> {val}</div>'
                    row_html = f'''
                    <div class="tl-item">
                      <div class="tl-dot" style="background:{dot_color.get(status,'#6c757d')}"></div>
                      <div class="tl-content">
                        {diff('UGB', pn, prev.get('PENOMORAN UGB BARU','-') if prev is not None else pn)}
                        {diff('Capacity', cap_str, str(prev.get('KAPASITAS','-')) if prev is not None else cap_str)}
                        {diff('No Seri', sn, prev.get('NO SERI','-') if prev is not None else sn)}
                      </div>
                    </div>
                    '''
                    items.append(row_html)
                    prev = r

                koor = f"{coord[0]:.6f}, {coord[1]:.6f}" if coord else '-'
                panel_css = """
                <style>
                .side-panel { background:rgba(255,255,255,0.92); color:#222; border-radius:12px; box-shadow:0 6px 24px rgba(0,0,0,0.15); padding:16px 18px; border-left:4px solid #ff8c00; backdrop-filter: blur(2px); }
                .side-title { font-weight:800; font-size:18px; margin:0 0 8px 0; }
                .side-sub { font-size:12px; color:#555; margin-bottom:10px; }
                .tl-item { position:relative; padding-left:18px; margin:10px 0; }
                .tl-item .tl-dot { position:absolute; left:0; top:6px; width:8px; height:8px; border-radius:50%; }
                .tl-content { background:rgba(255,140,0,0.06); border-left:2px solid #ff8c00; padding:8px 10px; border-radius:6px; }
                </style>
                """
                st.markdown(panel_css, unsafe_allow_html=True)
                st.markdown(f"""
                <div class=side-panel>
                  <div class=side-title>Detail & Ringkasan di Koordinat</div>
                  <div class=side-sub>Koordinat: {koor} • Total entri: <b>{len(dfc)}</b></div>
                  {''.join(items)}
                </div>
                """, unsafe_allow_html=True)
    else:
        # Full width map (tidak ada panel)
        if marker_count > 0:
            try:
                map_state = st_folium(m, height=map_height, returned_objects=["last_clicked"], use_container_width=True)
            except TypeError:
                map_state = st_folium(m, height=map_height, returned_objects=["last_clicked"]) 
            st.success(f"🗺️ Menampilkan {marker_count} marker UGB di peta")
        else:
            st.warning("⚠️ Tidak ada koordinat yang valid untuk ditampilkan di peta")
        # Cek apakah ada cluster terpilih; jika ya, aktifkan panel dan rerun agar layout dua kolom
        coord, cluster_df = _find_cluster(filtered, map_state)
        if cluster_df is not None and not cluster_df.empty:
            # simpan klik ke session lalu aktifkan panel dan rerun
            if coord:
                st.session_state['ugb_last_clicked'] = { 'lat': coord[0], 'lng': coord[1] }
            st.session_state.ugb_show_side_panel = True
            st.rerun()
            # Urutkan untuk memudahkan membaca pergerakan
            dfc = cluster_df.copy()
            # Key urut: TANGGAL TERPASANG (jika ada) -> numeric suffix penomoran -> NO
            if 'TANGGAL TERPASANG' in dfc.columns:
                try:
                    dfc['_ts_'] = pd.to_datetime(dfc['TANGGAL TERPASANG'], errors='coerce')
                except Exception:
                    dfc['_ts_'] = pd.NaT
            else:
                dfc['_ts_'] = pd.NaT
            import re
            def peno_key(s):
                m = re.search(r'(\d+)$', str(s))
                return int(m.group(1)) if m else 0
            if 'PENOMORAN UGB BARU' in dfc.columns:
                dfc['_peno_'] = dfc['PENOMORAN UGB BARU'].apply(peno_key)
            else:
                dfc['_peno_'] = 0
            dfc['_no_'] = dfc['NO'] if 'NO' in dfc.columns else range(1, len(dfc)+1)
            dfc = dfc.sort_values(by=['_ts_', '_peno_', '_no_'], ascending=[True, True, True])

            # Bangun HTML panel
            dot_color = { 'STAND BY': '#28a745', 'RUSAK': '#dc3545', 'TERPASANG': '#ffc107' }
            items = []
            prev = None
            arrow_up = '&#8593;'; arrow_down = '&#8595;'
            for _, r in dfc.iterrows():
                status = str(r.get('STATUS_NORM',''))
                pn = str(r.get('PENOMORAN UGB BARU','-'))
                sn = str(r.get('NO SERI','-'))
                cap_val = r.get('KAPASITAS','-')
                cap_str = str(cap_val)
                # panah naik/turun untuk kapasitas
                if prev is not None:
                    try:
                        now = float(str(cap_val).replace(',','.'))
                        prv = float(str(prev.get('KAPASITAS','')).replace(',','.'))
                        if pd.notna(now) and pd.notna(prv):
                            if now > prv: cap_str = f"{arrow_up} {cap_str}"
                            elif now < prv: cap_str = f"{arrow_down} {cap_str}"
                    except Exception:
                        pass
                def diff(label, val, prev_val):
                    if prev is not None and str(val) != str(prev_val):
                        return f'<div><b>{label}:</b> <span style="color:#ff8c00">{val}</span> <span style="color:#888">(sebelumnya: {prev_val})</span></div>'
                    return f'<div><b>{label}:</b> {val}</div>'
                row_html = f'''
                <div class="tl-item">
                  <div class="tl-dot" style="background:{dot_color.get(status,'#6c757d')}"></div>
                  <div class="tl-content">
                    {diff('UGB', pn, prev.get('PENOMORAN UGB BARU','-') if prev is not None else pn)}
                    {diff('Capacity', cap_str, str(prev.get('KAPASITAS','-')) if prev is not None else cap_str)}
                    {diff('No Seri', sn, prev.get('NO SERI','-') if prev is not None else sn)}
                  </div>
                </div>
                '''
                items.append(row_html)
                prev = r

            koor = f"{coord[0]:.6f}, {coord[1]:.6f}" if coord else '-'
            panel_css = """
            <style>
            .side-panel { background:rgba(255,255,255,0.92); color:#222; border-radius:12px; box-shadow:0 6px 24px rgba(0,0,0,0.15); padding:16px 18px; border-left:4px solid #ff8c00; backdrop-filter: blur(2px); }
            .side-title { font-weight:800; font-size:18px; margin:0 0 8px 0; }
            .side-sub { font-size:12px; color:#555; margin-bottom:10px; }
            .tl-item { position:relative; padding-left:18px; margin:10px 0; }
            .tl-item .tl-dot { position:absolute; left:0; top:6px; width:8px; height:8px; border-radius:50%; }
            .tl-content { background:rgba(255,140,0,0.06); border-left:2px solid #ff8c00; padding:8px 10px; border-radius:6px; }
            </style>
            """
            st.markdown(panel_css, unsafe_allow_html=True)
            st.markdown(f"""
            <div class=side-panel>
              <div class=side-title>Detail & Ringkasan di Koordinat</div>
              <div class=side-sub>Koordinat: {koor} • Total entri: <b>{len(dfc)}</b></div>
              {''.join(items)}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Tidak menampilkan apa pun saat belum ada koordinat yang dipilih
            st.write("")

    # Selesai - tidak menampilkan chart lain agar fokus pada peta sesuai brief

# ===== HALAMAN REKAPITULASI DATA =====
def page_recap():
    """Halaman rekapitulasi data (gaya INSPEKSI): Slicer -> Apply/Reset/Export -> Tabel penuh"""
    st.header("📋 Rekapitulasi Data", divider="rainbow")

    # Load data (prefer session)
    if 'ugb_db' in st.session_state and isinstance(st.session_state['ugb_db'], pd.DataFrame) and not st.session_state['ugb_db'].empty:
        df = st.session_state['ugb_db']
    else:
        df = load_database(DATABASE_PATH)
    if df.empty:
        st.warning("⚠️ Belum ada data. Silakan upload data terlebih dahulu.")
        return

    # Siapkan kolom STATUS normalisasi untuk filter runtime (tidak disimpan)
    df_ui = df.copy()
    if 'STATUS' in df_ui.columns:
        df_ui['STATUS_NORM'] = df_ui['STATUS'].apply(normalize_status)

    # ===== FILTER SECTION (multi-select + Apply/Reset seperti INSPEKSI) =====
    if 'ugb_recap_filter_state' not in st.session_state:
        st.session_state.ugb_recap_filter_state = {'UP3': [], 'ULP': [], 'STATUS': []}
    if 'temp_ugb_recap_filter' not in st.session_state:
        st.session_state.temp_ugb_recap_filter = st.session_state.ugb_recap_filter_state.copy()

    # Opsi filter
    up3_all = sorted(df_ui['UP3'].dropna().astype(str).unique()) if 'UP3' in df_ui.columns else []
    # ULP tergantung UP3 (temp selection)
    temp_sel_up3 = st.session_state.temp_ugb_recap_filter.get('UP3', [])
    if temp_sel_up3 and 'ULP' in df_ui.columns:
        ulp_all = sorted(df_ui[df_ui['UP3'].astype(str).isin(temp_sel_up3)]['ULP'].dropna().astype(str).unique())
    else:
        ulp_all = sorted(df_ui['ULP'].dropna().astype(str).unique()) if 'ULP' in df_ui.columns else []
    status_all = ['RUSAK', 'STAND BY', 'TERPASANG']

    st.subheader("🎯 Filter Data")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="filter-header">🏢 UP3</div>', unsafe_allow_html=True)
            sel_up3 = st.multiselect("UP3", up3_all, default=st.session_state.temp_ugb_recap_filter.get('UP3', []), key="rec_temp_up3", placeholder="Semua", label_visibility="collapsed")
            st.session_state.temp_ugb_recap_filter['UP3'] = sel_up3
        with c2:
            st.markdown('<div class="filter-header">🏪 ULP</div>', unsafe_allow_html=True)
            # Pastikan default tetap valid jika opsi berubah
            temp_valid_ulp = [u for u in st.session_state.temp_ugb_recap_filter.get('ULP', []) if u in ulp_all]
            sel_ulp = st.multiselect("ULP", ulp_all, default=temp_valid_ulp, key="rec_temp_ulp", placeholder="Semua", label_visibility="collapsed")
            st.session_state.temp_ugb_recap_filter['ULP'] = sel_ulp
        with c3:
            st.markdown('<div class="filter-header">⚡ STATUS</div>', unsafe_allow_html=True)
            temp_valid_status = [s for s in st.session_state.temp_ugb_recap_filter.get('STATUS', []) if s in status_all]
            sel_status = st.multiselect("STATUS", status_all, default=temp_valid_status, key="rec_temp_status", placeholder="Semua", label_visibility="collapsed")
            st.session_state.temp_ugb_recap_filter['STATUS'] = sel_status
    # -- tombol akan dirender setelah data terfilter agar Export memakai hasil filter yang aktif --

    # Terapkan filter (berdasarkan state yang sudah di-Apply)
    f = st.session_state.ugb_recap_filter_state
    filtered = df_ui.copy()
    if f.get('UP3'):
        filtered = filtered[filtered['UP3'].astype(str).isin(f['UP3'])]
    if f.get('ULP'):
        filtered = filtered[filtered['ULP'].astype(str).isin(f['ULP'])]
    if f.get('STATUS') and 'STATUS_NORM' in filtered.columns:
        filtered = filtered[filtered['STATUS_NORM'].isin(f['STATUS'])]

    # Siapkan data untuk export (berdasarkan filter yang sudah di-Apply)
    def to_excel_bytes(df_export: pd.DataFrame) -> bytes:
        buf = BytesIO()
        try:
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Rekap UGB")
        except Exception:
            with pd.ExcelWriter(buf) as writer:
                df_export.to_excel(writer, index=False, sheet_name="Rekap UGB")
        return buf.getvalue()

    export_df = filtered.drop(columns=['STATUS_NORM'], errors='ignore').copy()
    if 'NO' not in export_df.columns:
        export_df.insert(0, 'NO', range(1, len(export_df) + 1))

    # Baris tombol: Reset | Apply | Export (sejajar)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("🔄 Reset Filter", use_container_width=True, key="rec_reset"):
            default = {'UP3': [], 'ULP': [], 'STATUS': []}
            st.session_state.ugb_recap_filter_state = default.copy()
            st.session_state.temp_ugb_recap_filter = default.copy()
            st.rerun()
    with b2:
        if st.button("🔍 Apply Filter", use_container_width=True, key="rec_apply"):
            st.session_state.ugb_recap_filter_state = st.session_state.temp_ugb_recap_filter.copy()
            st.rerun()
    with b3:
        st.download_button(
            label=f"📥 Export Data ({len(export_df):,})",
            data=to_excel_bytes(export_df),
            file_name=f"UGB_Rekap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="rec_export_btn",
        )

    # Info jumlah data setelah tombol
    if len(filtered) != len(df_ui):
        st.info(f"📊 Menampilkan {len(filtered):,} dari {len(df_ui):,} total data berdasarkan filter")
    else:
        st.info(f"📊 Menampilkan seluruh {len(filtered):,} data")

    # (Hapus export button lama yang ada di bawah)

    st.subheader("📊 Hasil Data")

    # ===== TABEL INTERAKTIF TANPA LIMIT =====
    display_df = export_df  # tampilkan sesuai yang diekspor

    # Coba gunakan AgGrid untuk performa & style seperti INSPEKSI
    try:
        import importlib
        aggrid_mod = importlib.import_module("st_aggrid")
        GridOptionsBuilder = aggrid_mod.GridOptionsBuilder
        AgGrid = aggrid_mod.AgGrid
        GridUpdateMode = aggrid_mod.GridUpdateMode
        # Quick search
        q = st.text_input("🔎 Cari cepat", value="", placeholder="Ketik untuk filter cepat pada tabel...")
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_grid_options(
            enableRangeSelection=True,
            rowSelection='multiple',
            domLayout='normal',
            quickFilterText=q
        )
        gb.configure_pagination(enabled=False)  # tampilkan semua, tanpa paging
        grid_options = gb.build()
        AgGrid(
            display_df,
            gridOptions=grid_options,
            height=600,
            fit_columns_on_grid_load=True,
            theme='alpine-dark',
            update_mode=GridUpdateMode.NO_UPDATE,
        )
    except Exception:
        # Fallback standar
        st.dataframe(display_df, use_container_width=True, height=600)

# ===== MAIN APPLICATION =====
def main():
    # Header
    display_header()
    # Sidebar nav
    render_sidebar_nav()
    # Routing halaman
    if st.session_state.page == "upload":
        page_upload_data()
    elif st.session_state.page == "dashboard":
        page_dashboard()
    elif st.session_state.page == "recap":
        page_recap()
    # Footer
    st.markdown("---")
    st.caption("© 2025 – Dashboard Geo-Monitor UGB • Dibuat untuk Magang MBKM PLN UID Lampung oleh Ganiya Syazwa")

if __name__ == "__main__":
    main()
