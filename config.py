# config.py
"""
Konfigurasi utama untuk Dashboard Geo-Monitor UGB PT. PLN UID Lampung
"""

import os

# ===== KONFIGURASI APLIKASI =====
APP_TITLE = "Dashboard UGB PT. PLN UID Lampung"
APP_ICON = "⚡"
LAYOUT = "wide"

# ===== KONFIGURASI DATABASE =====
DATABASE_PATH = "data/ugb_database.csv"
BACKUP_PATH = "data/backup/"

# ===== OPSIONAL: Gunakan Google Sheets sebagai database =====
# Set True untuk memakai Google Sheets sebagai database utama.
# Jika False, sistem memakai CSV lokal (DATABASE_PATH).
USE_GOOGLE_SHEETS = False

# ID Spreadsheet dan nama Sheet untuk UGB (isi saat mengaktifkan USE_GOOGLE_SHEETS)
GSHEETS_SPREADSHEET_ID = ""  # contoh: "1AbCDefGhIJKLmn..."
GSHEETS_SHEET_NAME = "UGB_Master"

# Path ke credentials.json (default: file di folder root repo)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GSHEETS_CREDENTIALS_PATH = os.path.abspath(os.path.join(_BASE_DIR, "..", "credentials.json"))

# ===== MODE PENYIMPANAN DATA =====
# Jika True: setiap upload MENGGANTIKAN database dengan file terbaru (disarankan untuk kasus Anda)
# Jika False: setiap upload DITAMBAHKAN di atas data lama (append/merge)
REPLACE_ON_UPLOAD = True

# Jika True: saat upload, sistem akan menghapus duplikasi absolut berbasis normalisasi
# (normalisasi hanya untuk pembandingan; nilai asli TIDAK diubah)
DEDUPE_ON_UPLOAD = True

# ===== SHEET YANG VALID =====
VALID_SHEETS = [
    "UGB UP3 KARANG",
    "UGB UP3 METRO", 
    "UGB UP3 KOTABUMI",
    "UGB UP3 PRINGSEWU"
]

# ===== HEADER KOLOM YANG VALID =====
VALID_COLUMNS = [
    "UP3",                              # Kolom B
    "ULP",                              # Kolom C  
    "KETERANGAN",                       # Kolom D
    "KAPASITAS",                        # Kolom E
    "STATUS",                           # Kolom F
    "NO SERI",                          # Kolom G
    "ALAMAT TERPASANG",                 # Kolom H
    "PENOMORAN UGB BARU",              # Kolom I
    "KOORDINAT TAGGING",                # Kolom J
    "MENGGUNAKAN TRAFO RETROFIT/NIAGA", # Kolom K
    "TANGGAL TERPASANG",               # Kolom L
    "TANGGAL TERBONGKAR"               # Kolom M
]

# ===== NORMALISASI TEKS =====
# Untuk mengatasi variasi penulisan seperti TDK, tdk, Tidak, TIDAK, tidak
NORMALIZATION_DICTIONARY = {
    # Status umum
    'STANDBY': ['STANDBY', 'STAND BY', 'STANBY', 'SIAP', 'READY', 'SIAGA'],
    'RUSAK': ['RUSAK', 'RUSK', 'BROKEN', 'DAMAGE', 'RUSAK', 'JELEK'],
    'TERPASANG': ['TERPASANG', 'PASANG', 'INSTALLED', 'AKTIF', 'ACTIVE'],
    
    # Kata negasi dan afirmasi
    'TIDAK': ['TDK', 'TIAK', 'TIDKA', 'TIDAK', 'TDK.', 'TIDK', 'TDAK', 'ENGGAK', 'ENGGA', 'GA', 'NGGAK', 'NDAK', 'tidak', 'tdk'],
    'YA': ['YES', 'IYA', 'IYAH', 'Y', 'OK', 'OKE', 'BETUL', 'BENAR', 'ya', 'iya'],
    
    # UP3 normalisasi
    'KARANG': ['KARANG', 'TANJUNG KARANG', 'TJK', 'TJ KARANG'],
    'METRO': ['METRO', 'MTR', 'METRO CITY'],
    'KOTABUMI': ['KOTABUMI', 'KOTA BUMI', 'KTB'],
    'PRINGSEWU': ['PRINGSEWU', 'PRINGSEU', 'PSW', 'PRINGS'],
    
    # Status kondisi
    'BAIK': ['BAIK', 'BAGUS', 'OK', 'AMAN', 'NORMAL'],
    'BURUK': ['BURUK', 'JELEK', 'BAD', 'POOR', 'RUSAK'],
}

# ===== KONFIGURASI PETA =====
MAP_CONFIG = {
    'default_center': [-5.3971, 105.2663],  # Koordinat Lampung
    'default_zoom': 9,
    'marker_colors': {
        'STANDBY': 'green',
        'RUSAK': 'red', 
        'TERPASANG': 'orange'
    }
}

# ===== KONFIGURASI FILTER =====
FILTER_COLUMNS = ['UP3', 'ULP', 'STATUS']

# ===== PATH ASSETS =====
ASSETS_PATH = "assets/"
LOGO_DANANTARA_PATH = os.path.join(ASSETS_PATH, "LOGO DANANTARA.png")
LOGO_PLN_PATH = os.path.join(ASSETS_PATH, "LOGO PLN.png")

# ===== FORMAT FILE YANG DITERIMA =====
ACCEPTED_FILE_TYPES = ['xlsx', 'xlsm']

# ===== STYLING =====
HEADER_STYLE = """
    <style>
    .main-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-content {
        display: flex;
        align-items: center;
        gap: 30px;
    }
    
    .logo {
        width: 80px;
        height: 80px;
        object-fit: contain;
    }
    
    .title {
        color: white;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background-color: #f9f9f9;
        margin: 20px 0;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2980b9;
    }
    </style>
"""
