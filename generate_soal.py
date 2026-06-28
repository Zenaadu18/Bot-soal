import os
import json
import time
import pandas as pd
import streamlit as st
import google.generativeai as genai

# --- CONFIG DASHBOARD UTAMA ---
st.set_page_config(page_title="CAT Gen Soal", page_icon="🤖", layout="wide")
st.title("🤖 CAT Try Out Generator Soal (Standar SKD Kedinasan)")
st.write("Aplikasi otomatis pembuat 110 paket soal SKD berbasis Google Gemini API.")

# --- MANAJEMEN API KEY SECARA AMAN ---
# Ambil API Key murni dari Secrets Streamlit (Lebih Aman)
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

# --- FUNGSI UTAMA ---
def read_guidelines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Gagal membaca kisi-kisi: {e}")
        return ""

def read_sample_questions(filepath, num_samples=3):
    try:
        df = pd.read_excel(filepath)
        df = df.fillna("")
        samples = df.head(num_samples).to_dict(orient='records')
        return json.dumps(samples, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Gagal membaca sampel: {e}")
        return "[]"

def generate_questions_batch(guidelines, sample_questions_json, category_name, category_desc, num_questions):
    # Kita buat definisi struktur data (Schema) agar Gemini WAJIB patuh 100%
    # Ini mencegah format JSON rusak atau terpotong
    prompt = f"""
Anda adalah ahli pembuat soal Try Out Sekolah Kedinasan (SKD) berstandar nasional BKN.
Tugas Anda adalah membuat {num_questions} soal BARU yang unik dan berkualitas tinggi khusus untuk kategori: {category_name}.
Karakteristik materi {category_name}: {category_desc}

Berikut adalah panduan materi/kisi-kisi resmi (jadikan acuan utama):
[KISI-KISI SOAL]
{guidelines}

Berikut adalah referensi beberapa soal lama untuk meniru format, gaya bahasa, dan standar:
[CONTOH SOAL LAMA]
{sample_questions_json}

Buatlah {num_questions} soal baru untuk kategori {category_name}. 
Kembalikan data dalam bentuk JSON Array of Objects dengan key:
"tipe", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "opsi_e", "kunci", "pembahasan", "poin_a", "poin_b", "poin_c", "poin_d", "poin_e"
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7 # Membuat variasi soal menjadi lebih kreatif namun tetap patuh struktur
            )
        )
        return json.loads(response.text)
    except Exception as e:
        # Menampilkan eror asli dari Google ke layar Streamlit Anda agar mudah dilacak
        st.warning(f"Detail Eror Internal: {e}")
        return []

# --- ANTARMUKA WEB (UI) ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📂 Kelola File Sumber")
    kisi_kisi_file = st.text_input("Nama File Kisi-kisi", value="kisi_kisi_soal.txt")
    sample_file = st.text_input("Nama File Sampel Excel", value="soal 2.xlsx")
    
    st.subheader("⚙️ Konfigurasi Paket Soal")
    test_mode = st.checkbox("Mode Testing (Hanya buat total 3 soal cepat)", value=False)

skd_config = [
    {"kategori": "TWK", "jumlah": 3 if test_mode else 30, "deskripsi": "Nasionalisme, Integritas, Bela Negara, Pilar Negara, Bahasa Indonesia."},
    {"kategori": "TIU", "jumlah": 3 if test_mode else 35, "deskripsi": "Kemampuan Verbal (Silogisme/Analitis), Numerik (Hitungan/Soal Cerita), Figural (Gambar)."},
    {"kategori": "TKP", "jumlah": 3 if test_mode else 45, "deskripsi": "Pelayanan Publik, Jejaring Kerja, Sosial Budaya, TIK, Profesionalisme, Anti Radikalisme."}
]

with col2:
    st.header("🚀 Generator Konsol")
    
    if st.button("Mulai Jalankan Bot Pembuat Soal", type="primary"):
        guidelines = read_guidelines(kisi_kisi_file)
        sample_questions = read_sample_questions(sample_file, num_samples=3)
        
        if not guidelines:
            st.warning("Proses dihentikan karena isi file kisi-kisi kosong.")
        else:
            all_questions = []
            batch_size = 5
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_target_soal = sum([c["jumlah"] for c in skd_config])
            
            for config in skd_config:
                kategori = config["kategori"]
                target_jumlah = config["jumlah"]
                deskripsi = config["deskripsi"]
                
                st.write(f"**Menjalankan Kategori {kategori} ({target_jumlah} Soal)...**")
                
                soal_terkumpul = 0
                while soal_terkumpul < target_jumlah:
                    sisa = target_jumlah - soal_terkumpul
                    jumlah_batch = batch_size if sisa > batch_size else sisa
                    
                    status_text.text(f"Mengirim request batch: {jumlah_batch} soal {kategori}...")
                    
                    batch_data = generate_questions_batch(
                        guidelines, sample_questions, kategori, deskripsi, jumlah_batch
                    )
                    
                    if batch_data:
                        all_questions.extend(batch_data)
                        soal_terkumpul += len(batch_data)
                        st.success(f"✓ Berhasil menarik {len(batch_data)} soal {kategori}. ({soal_terkumpul}/{target_jumlah})")
                    else:
                        st.error("⚠️ Gagal mendapat respons valid dari Gemini API, mencoba ulang...")
                    
                    current_progress = min(len(all_questions) / total_target_soal, 1.0)
                    progress_bar.progress(current_progress)
                    time.sleep(5)
            
            status_text.text("Menyusun struktur tabel dan finalisasi berkas...")
            
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
                st.subheader("🎉 Proses Selesai Semuanya!")
                
                st.download_button(
                    label="📥 DOWNLOAD FILE EXCEL HASIL GENERATE",
                    data=buffer.getvalue(),
                    file_name="bank_soal_generated_110.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Gagal total memproses pembuatan seluruh paket soal.")
