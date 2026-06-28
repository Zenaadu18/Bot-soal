import os
import json
import time
import pandas as pd
import streamlit as st
import google.generativeai as genai

# --- CONFIG DASHBOARD UTAMA & RESPONSIVE ---
st.set_page_config(
    page_title="Patriot CAT Bot Gen", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SENTUHAN UI/UX MODERN (KUSTOM CSS) ---
st.markdown("""
    <style>
    /* Mengatur latar belakang utama dan font modern */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Desain Glassmorphism untuk Container/Card */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #38bdf8 !important;
        font-weight: 700;
    }
    
    /* Custom Styling untuk Kolom Input & Kontainer */
    .css-1r6g72t, .stForm, div[data-testid="column"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        padding: 24px;
        margin-bottom: 20px;
    }
    
    /* Membuat Tombol Menjadi Modern dengan Efek Gradient */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
        background: linear-gradient(90deg, #60a5fa 0%, #2563eb 100%) !important;
    }
    
    /* Tombol Download Sukses Gede & Menarik */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(90deg, #10b981 0%, #047857 100%) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(90deg, #34d399 0%, #059669 100%) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
    }
    
    /* Responsivitas Teks */
    h1 {
        font-weight: 800 !important;
        background: linear-gradient(90deg, #38bdf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MANAJEMEN API KEY SECARA AMAN ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

# --- FUNGSI UTAMA LOGIKA BOT ---
def read_guidelines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def read_sample_questions(filepath, num_samples=3):
    try:
        df = pd.read_excel(filepath)
        df = df.fillna("")
        samples = df.head(num_samples).to_dict(orient='records')
        return json.dumps(samples, indent=2, ensure_ascii=False)
    except:
        return "[]"

def generate_questions_batch(guidelines, sample_questions_json, category_name, category_desc, num_questions):
    prompt = f"""
Anda adalah ahli pembuat soal Try Out Sekolah Kedinasan (SKD) berstandar nasional BKN.
Tugas Anda adalah membuat {num_questions} soal BARU khusus untuk kategori: {category_name}.
Karakteristik materi {category_name}: {category_desc}

Berikut adalah panduan materi/kisi-kisi resmi:
{guidelines}

Berikut adalah referensi beberapa soal lama:
{sample_questions_json}

Buatlah {num_questions} soal baru untuk kategori {category_name}.
Kembalikan data murni dalam format JSON Array of Objects dengan key:
"tipe", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "opsi_e", "kunci", "pembahasan", "poin_a", "poin_b", "poin_c", "poin_d", "poin_e"
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except:
        return []

# --- TAMPILAN HEADER ---
st.title("⚡ CAT Try Out Generator Pro")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Platform cerdas pembuat paket soal ujian SKD Kedinasan berbasis AI secara otomatis, cepat, dan terstandarisasi BKN.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- GRID CARD RINGKASAN STRUKTUR SOAL ---
st.subheader("📊 Rencana Komposisi Soal")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="Total Soal", value="110 Soal")
with m2:
    st.metric(label="Materi TWK", value="30 Soal")
with m3:
    st.metric(label="Materi TIU", value="35 Soal")
with m4:
    st.metric(label="Materi TKP", value="45 Soal")

st.markdown("<br>", unsafe_allow_html=True)

# --- KONTROL UTAMA & RESPONSIVE LAYOUT ---
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown("### 📂 Pengaturan Berkas Sumber")
    kisi_kisi_file = st.text_input("📁 File Kisi-kisi (.txt)", value="kisi_kisi_soal.txt")
    sample_file = st.text_input("📊 File Sampel Bank Soal (.xlsx)", value="soal 2.xlsx")
    
    st.markdown("### ⚙️ Mode Eksekusi")
    test_mode = st.checkbox("🧪 Aktifkan Mode Testing (Cepat - Hanya 3 Soal/Kategori)", value=False)

skd_config = [
    {"kategori": "TWK", "jumlah": 3 if test_mode else 30, "deskripsi": "Nasionalisme, Integritas, Bela Negara, Pilar Negara, Bahasa Indonesia."},
    {"kategori": "TIU", "jumlah": 3 if test_mode else 35, "deskripsi": "Kemampuan Verbal, Numerik (Hitungan), Figural (Gambar)."},
    {"kategori": "TKP", "jumlah": 3 if test_mode else 45, "deskripsi": "Pelayanan Publik, Jejaring Kerja, Sosial Budaya, TIK, Profesionalisme, Anti Radikalisme."}
]

with col2:
    st.markdown("### 🚀 Konsol Monitor Proses")
    
    if st.button("✨ Mulai Produksi Soal Sekarang", type="primary"):
        guidelines = read_guidelines(kisi_kisi_file)
        sample_questions = read_sample_questions(sample_file, num_samples=3)
        
        if not guidelines:
            st.error("❌ Gagal memulai! Berkas kisi-kisi kosong atau tidak ditemukan.")
        else:
            all_questions = []
            batch_size = 5 # Diperkecil menjadi 5 demi kestabilan maksimal API
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_target_soal = sum([c["jumlah"] for c in skd_config])
            
            for config in skd_config:
                kategori = config["kategori"]
                target_jumlah = config["jumlah"]
                deskripsi = config["deskripsi"]
                
                st.markdown(f"⏳ **Sedang memproses kategori {kategori}...**")
                
                soal_terkumpul = 0
                while soal_terkumpul < target_jumlah:
                    sisa = target_jumlah - soal_terkumpul
                    jumlah_batch = batch_size if sisa > batch_size else sisa
                    
                    status_text.text(f"📡 Mengirim request batch: {jumlah_batch} soal {kategori} ke Gemini API...")
                    
                    batch_data = generate_questions_batch(
                        guidelines, sample_questions, kategori, deskripsi, jumlah_batch
                    )
                    
                    if batch_data:
                        all_questions.extend(batch_data)
                        soal_terkumpul += len(batch_data)
                    else:
                        status_text.text("⚠️ Mengalami kendala jaringan, mencoba ulang...")
                    
                    current_progress = min(len(all_questions) / total_target_soal, 1.0)
                    progress_bar.progress(current_progress)
                    time.sleep(12) # Menghindari error rate limit API Gratis
            
            status_text.text("⚙️ Memfinalisasi berkas Excel dalam memori cloud...")
            
            if all_questions:
                df = pd.DataFrame(all_questions)
                expected_columns = ['tipe', 'pertanyaan', 'opsi_a', 'opsi_b', 'opsi_c', 'opsi_d', 'opsi_e', 'kunci', 'pembahasan', 'poin_a', 'poin_b', 'poin_c', 'poin_d', 'poin_e']
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = ""
                df = df[expected_columns]
                
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.balloons()
                status_text.empty()
                st.success("🎉 Luar Biasa! Berhasil memproduksi seluruh rangkaian paket soal.")
                
                # TOMBOL DOWNLOAD DESIGN BESAR KHUSUS
                st.download_button(
                    label="📥 DOWNLOAD BERKAS BANK SOAL EXCEL",
                    data=buffer.getvalue(),
                    file_name="bank_soal_generated_110.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Gagal mengekstrak struktur soal dari AI.")
