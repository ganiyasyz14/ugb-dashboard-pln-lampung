# utils/data_processor.py
"""
Utilitas untuk pemrosesan data UGB dengan normalisasi teks intelligent
"""

import pandas as pd
import re
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
from config import NORMALIZATION_DICTIONARY, VALID_COLUMNS, VALID_SHEETS, BACKUP_PATH, USE_GOOGLE_SHEETS, REPLACE_ON_UPLOAD, DEDUPE_ON_UPLOAD
try:
    if USE_GOOGLE_SHEETS:
        from .gsheets_adapter import load_sheet as gs_load_sheet, save_merge as gs_save_merge
    else:
        gs_load_sheet = gs_save_merge = None  # type: ignore
except Exception:
    gs_load_sheet = gs_save_merge = None  # type: ignore

def normalize_text(text: str) -> str:
    """
    Normalisasi teks untuk mengatasi variasi penulisan
    Contoh: TDK, tdk, Tidak, TIDAK, tidak -> TIDAK
    """
    if pd.isna(text) or text == "":
        return ""
    
    # Konversi ke string dan bersihkan
    text = str(text).strip().upper()
    
    # Hapus karakter khusus yang tidak perlu
    text = re.sub(r'[^\w\s.-]', ' ', text)
    
    # Normalisasi spasi berlebih
    text = ' '.join(text.split())
    
    # Cari di kamus normalisasi - exact match dulu
    for standard_form, variations in NORMALIZATION_DICTIONARY.items():
        if text in variations or text == standard_form:
            return standard_form
    
    # Cari partial match untuk frasa yang mengandung kata kunci
    for standard_form, variations in NORMALIZATION_DICTIONARY.items():
        for variant in variations:
            if variant in text:
                # Replace hanya jika kata utuh (word boundary)
                pattern = r'\b' + re.escape(variant) + r'\b'
                if re.search(pattern, text):
                    text = re.sub(pattern, standard_form, text)
                break
    
    return text

def _normalized_value(val: Any) -> str:
    """Bangun nilai ter-normalisasi untuk komparasi (tanpa mengubah data asli)."""
    if pd.isna(val) or val == "":
        return ""
    s = str(val).strip().upper()
    s = re.sub(r'[\s]+', ' ', s)
    # rapikan spasi di sekitar koma
    s = re.sub(r"\s*,\s*", ",", s)
    # Pakai kamus NORMALIZATION_DICTIONARY untuk mapping longgar
    for standard_form, variations in NORMALIZATION_DICTIONARY.items():
        if s == standard_form or s in variations:
            return standard_form
    return s

def _build_dedupe_key(row: pd.Series, key_cols: List[str]) -> str:
    """Bangun kunci duplikasi dari beberapa kolom dengan normalisasi ringan (untuk validasi saja)."""
    parts: List[str] = []
    for c in key_cols:
        parts.append(_normalized_value(row.get(c, "")))
    return "|".join(parts)

# ===== Versi vektorisasi (lebih cepat) untuk deduplikasi =====
def _build_normalization_map() -> Dict[str, str]:
    """Bangun peta normalisasi: setiap variasi -> bentuk baku (untuk validasi saja)."""
    mapping: Dict[str, str] = {}
    for standard, variations in NORMALIZATION_DICTIONARY.items():
        # standard map ke dirinya sendiri
        mapping[standard.upper()] = standard
        for v in variations:
            mapping[str(v).upper()] = standard
    return mapping

_NORMALIZATION_MAP = _build_normalization_map()

def _normalize_series_for_key(s: pd.Series) -> pd.Series:
    """Normalisasi sebuah Series string untuk kunci duplikasi (tanpa mengubah data asli)."""
    # ke string, isi NaN
    s2 = s.astype(str).fillna("")
    # trim dan uppercase
    s2 = s2.str.strip().str.upper()
    # kompakkan spasi
    s2 = s2.str.replace(r"\s+", " ", regex=True)
    # rapikan spasi di sekitar koma (contoh koordinat "-5, 105" -> "-5,105")
    s2 = s2.str.replace(r"\s*,\s*", ",", regex=True)
    # map variasi -> standar (gunakan map lalu fallback ke nilai asli)
    s2 = s2.map(_NORMALIZATION_MAP).fillna(s2)
    return s2

def build_dedupe_keys_vectorized(df: pd.DataFrame, key_cols: List[str]) -> pd.Series:
    """Bangun kunci duplikasi ter-normalisasi secara vektorisasi untuk seluruh dataframe."""
    cols = [c for c in key_cols if c in df.columns]
    if not cols:
        return pd.Series([], dtype=str)
    norm_cols = []
    for c in cols:
        norm_cols.append(_normalize_series_for_key(df[c]))
    # gabungkan dengan pemisah | secara vektorisasi
    key = norm_cols[0].copy()
    for s in norm_cols[1:]:
        key = key.str.cat(s, sep='|')
    return key

def normalize_header(header: str) -> str:
    """
    Normalisasi nama header untuk mengatasi typo dan variasi penulisan
    """
    if pd.isna(header) or header == "":
        return ""
    
    # Bersihkan header
    header = str(header).strip().upper()
    header = re.sub(r'[^\w\s/]', ' ', header)
    header = ' '.join(header.split())
    
    # Mapping khusus untuk header yang sering typo
    header_mappings = {
        'UP3': ['UP3', 'UP 3', 'UNIT PELAKSANA PELAYANAN PELANGGAN'],
        'ULP': ['ULP', 'UL P', 'UNIT LAYANAN PELANGGAN'],
        'KETERANGAN': ['KETERANGAN', 'KETERANGN', 'KETERANAGN', 'KET'],
        'KAPASITAS': ['KAPASITAS', 'KAPASTAS', 'KAPASITS', 'CAPACITY'],
        'STATUS': ['STATUS', 'STATS', 'STATE'],
        'NO SERI': ['NO SERI', 'NOMOR SERI', 'SERIAL NUMBER', 'SN'],
        'ALAMAT TERPASANG': ['ALAMAT TERPASANG', 'ALAMAT PASANG', 'LOKASI PASANG'],
        'PENOMORAN UGB BARU': ['PENOMORAN UGB BARU', 'NOMOR UGB BARU', 'NO UGB BARU'],
        'KOORDINAT TAGGING': ['KOORDINAT TAGGING', 'KOORDINAT TAG', 'COORD TAGGING', 'KOORDINAT'],
        'MENGGUNAKAN TRAFO RETROFIT/NIAGA': [
            'MENGGUNAKAN TRAFO RETROFIT/NIAGA',
            'MENGGUNAKAN TRAFO RETROFIT / NIAGA',
            'MENGUNAKAN TRAFO RETROFIT/NIAGA',
            'MENGUNAKAN TRAFO RETROFIT / NIAGA',
            'MENGUNAKAKAN TRAFO RETROFIT/NIAGA',
            'MENGUNAKAKAN TRAFO RETROFIT / NIAGA',
            'MENGGUNAKAKAN TRAFO RETROFIT/NIAGA',
            'MENGGUNAKAKAN TRAFO RETROFIT / NIAGA',
            'TRAFO RETROFIT NIAGA',
            'TRAFO RETROFIT/NIAGA',
            'TRAFO RETROFIT / NIAGA',
            'RETROFIT NIAGA',
            'RETROFIT/NIAGA',
            'RETROFIT / NIAGA'
        ],
        'TANGGAL TERPASANG': ['TANGGAL TERPASANG', 'TGL TERPASANG', 'DATE INSTALLED'],
        'TANGGAL TERBONGKAR': ['TANGGAL TERBONGKAR', 'TGL TERBONGKAR', 'DATE REMOVED']
    }
    
    # Cari header yang cocok
    for standard, variants in header_mappings.items():
        if header in variants:
            return standard
    
    return header

def validate_sheet_name(sheet_name: str) -> bool:
    """
    Validasi nama sheet apakah sesuai dengan yang diizinkan
    """
    if pd.isna(sheet_name) or sheet_name == "":
        return False
    
    # Normalisasi nama sheet
    normalized_sheet = str(sheet_name).strip().upper()
    
    # Cek apakah ada di VALID_SHEETS
    for valid_sheet in VALID_SHEETS:
        if normalized_sheet == valid_sheet.upper():
            return True
    
    return False

def process_excel_file(file_data) -> Tuple[bool, str, pd.DataFrame]:
    """
    Proses file Excel yang diupload
    
    Returns:
        Tuple[bool, str, pd.DataFrame]: (success, message, dataframe)
    """
    try:
        # Baca file Excel
        excel_file = pd.ExcelFile(file_data)
        
        # Validasi sheet names
        valid_sheets = []
        for sheet_name in excel_file.sheet_names:
            if validate_sheet_name(str(sheet_name)):
                valid_sheets.append(str(sheet_name))
        
        if not valid_sheets:
            return False, f"Tidak ditemukan sheet yang valid. Sheet harus salah satu dari: {', '.join(VALID_SHEETS)}", pd.DataFrame()
        
        # Proses setiap sheet yang valid
        all_dataframes = []
        
        for sheet_name in valid_sheets:
            try:
                # Baca seluruh kolom sheet (kita akan buang kolom NO sumber secara eksplisit)
                df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    header=0,
                    dtype=str  # Baca sebagai string untuk menjaga nilai asli
                )

                # Normalisasi hanya untuk header yang dikenal; sisanya biarkan apa adanya
                normalized_cols = []
                for col in df.columns:
                    norm = normalize_header(col)
                    if norm in VALID_COLUMNS or norm == 'NO':
                        normalized_cols.append(norm)
                    else:
                        normalized_cols.append(str(col))  # pertahankan nama asli
                df.columns = normalized_cols

                # Jika ada kolom yang ter-normalisasi ganda (nama sama), gabungkan nilainya dan sisakan satu kolom
                # Prioritaskan nilai pertama yang tidak kosong per baris
                from collections import Counter, defaultdict
                name_counts = Counter(df.columns)
                dup_names = [n for n, c in name_counts.items() if c > 1]
                for name in dup_names:
                    # Ambil semua kolom dengan nama ini dalam urutan kemunculan
                    same_cols = [c for c in df.columns if c == name]
                    base = df[same_cols[0]].astype(str)
                    for extra in same_cols[1:]:
                        extra_series = df[extra].astype(str)
                        base = base.where(base.str.strip().ne(''), extra_series)
                    # Tulis kembali ke kolom pertama dan drop sisanya
                    df[same_cols[0]] = base
                    df = df.drop(columns=same_cols[1:])

                # Pastikan kolom 'NO' dari file sumber tidak ikut dipakai
                df = df.drop(columns=['NO'], errors='ignore')
                
                # Validasi struktur kolom
                missing_columns = []
                for required_col in VALID_COLUMNS:
                    if required_col not in df.columns:
                        missing_columns.append(required_col)

                # Kolom opsional yang boleh tidak ada
                optional_cols = {'MENGGUNAKAN TRAFO RETROFIT/NIAGA'}
                blocking_missing = [c for c in missing_columns if c not in optional_cols]

                if blocking_missing:
                    return False, f"Sheet '{sheet_name}' kehilangan kolom: {', '.join(blocking_missing)}", pd.DataFrame()

                # Tambahkan kolom opsional yang hilang sebagai kosong
                for opt in optional_cols:
                    if opt not in df.columns:
                        df[opt] = ""

                # Reorder: letakkan kolom yang wajib di depan, tapi JANGAN buang kolom-kolom lain
                known_cols_ordered = [c for c in VALID_COLUMNS if c in df.columns]
                other_cols = [c for c in df.columns if c not in known_cols_ordered]
                df = df[known_cols_ordered + other_cols]

                # Tambah kolom source sheet (di akhir)
                df['SOURCE_SHEET'] = sheet_name
                
                # PRESERVE: Jangan normalisasi isi kolom (hindari mengubah kata seperti "RUSAK" -> "BURUK")
                # Hanya bersihkan spasi awal/akhir dan ubah NaN menjadi string kosong
                for col in df.columns:
                    if col != 'SOURCE_SHEET':
                        df[col] = df[col].apply(lambda v: "" if pd.isna(v) else str(v).strip())
                
                # Hapus baris kosong (benar-benar kosong di semua kolom)
                df = df.dropna(how='all')
                df = df[df.apply(lambda x: x.astype(str).str.strip().ne('').any(), axis=1)]
                
                if not df.empty:
                    # Batasi per lembar: hanya baris dengan PENOMORAN UGB BARU non-empty
                    if 'PENOMORAN UGB BARU' in df.columns:
                        df = df[df['PENOMORAN UGB BARU'].astype(str).str.strip().ne('')]
                    if not df.empty:
                        all_dataframes.append(df)
                    
            except Exception as e:
                return False, f"Error memproses sheet '{sheet_name}': {str(e)}", pd.DataFrame()
        
        if not all_dataframes:
            return False, "Tidak ada data valid yang ditemukan dalam file", pd.DataFrame()
        
        # Gabungkan semua dataframe
        final_df = pd.concat(all_dataframes, ignore_index=True)

        # Sertakan HANYA baris yang memiliki PENOMORAN UGB BARU (non-empty)
        if 'PENOMORAN UGB BARU' in final_df.columns:
            final_df = final_df[final_df['PENOMORAN UGB BARU'].astype(str).str.strip().ne('')]

        # Nonaktifkan deduplikasi: tampilkan persis isi file

        # Urutkan berdasarkan tanggal terpasang SECARA SEMENTARA (tanpa mengubah nilai asli di kolom)
        if 'TANGGAL TERPASANG' in final_df.columns:
            try:
                sort_key = pd.to_datetime(final_df['TANGGAL TERPASANG'], errors='coerce')
                final_df = final_df.assign(_SORT_KEY=sort_key).sort_values('_SORT_KEY', ascending=False, na_position='last').drop(columns=['_SORT_KEY'])
            except Exception:
                # Jika gagal parsing tanggal, biarkan urutan apa adanya
                pass

        # Tambah kolom NO otomatis (data baru di atas)
        if 'NO' in final_df.columns:
            final_df = final_df.drop(columns=['NO'])
        final_df.insert(0, 'NO', range(1, len(final_df) + 1))

        msg = f"Berhasil memproses {len(final_df)} baris data dari {len(valid_sheets)} sheet"
        return True, msg, final_df
        
    except Exception as e:
        return False, f"Error membaca file: {str(e)}", pd.DataFrame()

def save_to_database(df: pd.DataFrame, database_path: str) -> bool:
    """
    Simpan dataframe ke database CSV
    """
    try:
        # Jika menggunakan Google Sheets sebagai database
        if USE_GOOGLE_SHEETS and gs_save_merge is not None:
            if REPLACE_ON_UPLOAD:
                # Replace mode: clear and write only the new data
                try:
                    from .gsheets_adapter import _get_client
                    from config import GSHEETS_SPREADSHEET_ID, GSHEETS_SHEET_NAME
                    gc = _get_client()
                    sh = gc.open_by_key(GSHEETS_SPREADSHEET_ID)
                    ws = sh.worksheet(GSHEETS_SHEET_NAME)
                    ws.clear()
                    to_write = df.drop(columns=['NO'], errors='ignore').copy()
                    to_write.insert(0, 'NO', range(1, len(to_write) + 1))
                    values = [to_write.columns.tolist()] + to_write.astype(str).values.tolist()
                    ws.update(values)
                    return True
                except Exception as e:
                    print(f"Gagal replace Google Sheets: {e}")
                    return False
            # Append/Merge mode
            ok, msg = gs_save_merge(df.drop(columns=['NO'], errors='ignore'))
            if not ok:
                print(msg)
                return False
            return True

        # Jika database sudah ada, buat backup cepat dan gabungkan data
        if os.path.exists(database_path):
            # Backup file lama dengan timestamp (best-effort)
            try:
                os.makedirs(BACKUP_PATH, exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                base = os.path.basename(database_path)
                name, _ = os.path.splitext(base)
                backup_file = os.path.join(BACKUP_PATH, f"{name}_{ts}.csv")
                shutil.copy2(database_path, backup_file)
            except Exception as be:
                print(f"Backup gagal: {str(be)}")

        # Tentukan mode simpan: replace atau append
        if REPLACE_ON_UPLOAD:
            combined_df = df.copy()
            # Pastikan NO di-generate ulang di depan
            combined_df = combined_df.drop(columns=['NO'], errors='ignore')
            combined_df.insert(0, 'NO', range(1, len(combined_df) + 1))
        else:
            if os.path.exists(database_path):
                existing_df = pd.read_csv(database_path)
                # Letakkan data baru di atas agar jika ada duplikat, versi terbaru yang dipertahankan
                # Gabungkan dan pertahankan semua kolom (union)
                combined_df = pd.concat([df, existing_df], ignore_index=True, sort=False)
                # Nonaktifkan deduplikasi pada penyimpanan (tampilkan apa adanya) + regen NO di depan
                combined_df = combined_df.drop(columns=['NO'], errors='ignore')
                combined_df.insert(0, 'NO', range(1, len(combined_df) + 1))
            else:
                combined_df = df
        
        # Simpan ke CSV
        combined_df.to_csv(database_path, index=False)
        return True
        
    except Exception as e:
        print(f"Error menyimpan database: {str(e)}")
        return False

def load_database(database_path: str) -> pd.DataFrame:
    """
    Load database dari file CSV
    """
    try:
        # Jika menggunakan Google Sheets sebagai database
        if USE_GOOGLE_SHEETS and gs_load_sheet is not None:
            df = gs_load_sheet()
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

        if os.path.exists(database_path):
            return pd.read_csv(database_path)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error membaca database: {str(e)}")
        return pd.DataFrame()

def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Ambil opsi filter dari dataframe
    """
    options = {}
    
    for col in ['UP3', 'ULP', 'STATUS']:
        if col in df.columns:
            unique_vals = df[col].dropna().unique()
            unique_vals = [str(val).strip() for val in unique_vals if str(val).strip() != '']
            options[col] = sorted(list(set(unique_vals)))
        else:
            options[col] = []
    
    return options

def parse_coordinates(coord_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse string koordinat menjadi latitude, longitude
    Format yang didukung: 
    - "lat, lon"
    - "lat,lon" 
    - "lat lon"
    """
    if pd.isna(coord_str) or str(coord_str).strip() == "":
        return None, None
    
    try:
        coord_str = str(coord_str).strip()
        
        # Split berdasarkan koma atau spasi
        if ',' in coord_str:
            parts = coord_str.split(',')
        else:
            parts = coord_str.split()
        
        if len(parts) >= 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
        else:
            return None, None
            
    except (ValueError, IndexError):
        return None, None
