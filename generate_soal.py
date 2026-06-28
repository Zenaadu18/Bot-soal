import os
import json
import time
import pandas as pd
# pyrefly: ignore [missing-import]
import google.generativeai as genai

# Konfigurasi API Key (Gunakan environment variable untuk keamanan, fallback ke key yang diberikan)
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBqJrI2wcqVDPm7gheeSdA4bS_fGRXBGWk")
genai.configure(api_key=API_KEY)

def read_guidelines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[Error] Gagal membaca kisi-kisi: {e}")
        return ""

def read_sample_questions(filepath, num_samples=3):
    try:
        df = pd.read_excel(filepath)
        df = df.fillna("")
        samples = df.head(num_samples).to_dict(orient='records')
        return json.dumps(samples, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error] Gagal membaca sampel: {e}")
        return "[]"

def generate_questions_batch(guidelines, sample_questions_json, category_name, category_desc, num_questions):
    prompt = f"""
Anda adalah ahli pembuat soal Try Out Sekolah Kedinasan (SKD) berstandar nasional BKN.
Tugas Anda adalah membuat {num_questions} soal BARU khusus untuk kategori: {category_name}.
Karakteristik materi {category_name}: {category_desc}

Berikut adalah panduan materi/kisi-kisi resmi (jadikan acuan utama):
[KISI-KISI SOAL]
{guidelines}

Berikut adalah referensi beberapa soal lama untuk meniru format, gaya bahasa, dan standar:
[CONTOH SOAL LAMA]
{sample_questions_json}

Buatlah {num_questions} soal baru untuk kategori {category_name}.
PENTING: Anda HARUS mengembalikan data murni dalam format JSON Array of Objects.
Setiap object soal HARUS persis menggunakan key/header berikut ini (jangan diubah):
"tipe", "pertanyaan", "opsi_a", "opsi_b", "opsi_c", "opsi_d", "opsi_e", "kunci", "pembahasan", "poin_a", "poin_b", "poin_c", "poin_d", "poin_e"

Nilai key "tipe" HARUS diisi dengan "{category_name}".
Jangan ada teks penjelasan apapun di luar format JSON.
"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"    [Error] Gagal parsing JSON dari respons model: {e}")
        return []
    except Exception as e:
        print(f"    [Error] Terjadi kesalahan API: {e}")
        return []

def save_to_excel(data_list, output_filepath):
    try:
        if not data_list:
            print("[Peringatan] Data kosong, tidak ada soal yang disimpan.")
            return

        df = pd.DataFrame(data_list)
        
        # Memastikan urutan kolom persis seperti file soal 2.xlsx
        expected_columns = ['tipe', 'pertanyaan', 'opsi_a', 'opsi_b', 'opsi_c', 'opsi_d', 'opsi_e', 'kunci', 'pembahasan', 'poin_a', 'poin_b', 'poin_c', 'poin_d', 'poin_e']
        for col in expected_columns:
            if col not in df.columns:
                df[col] = "" 
                
        df = df[expected_columns]
        df.to_excel(output_filepath, index=False)
        print(f"[Sukses] Berhasil menyusun total {len(df)} soal ke dalam file: '{output_filepath}'")
    except Exception as e:
        print(f"[Error] Gagal menyimpan ke Excel: {e}")

def main():
    print("="*50)
    print(" BOT OTOMATIS PENYUSUN 110 SOAL SKD (GEMINI API)")
    print("="*50)
    
    kisi_kisi_file = "kisi_kisi_soal.txt"
    sample_file = "soal 2.xlsx"
    output_file = "bank_soal_generated_110.xlsx"
    
    print("\n[Proses 1] Membaca instruksi kisi-kisi dan sampel...")
    guidelines = read_guidelines(kisi_kisi_file)
    sample_questions = read_sample_questions(sample_file, num_samples=3)
    
    if not guidelines:
        print("Program dihentikan karena kisi-kisi kosong.")
        return

    # Konfigurasi target soal SKD sesuai BKN
    skd_config = [
        {
            "kategori": "TWK",
            "jumlah": 30,
            "deskripsi": "Nasionalisme, Integritas, Bela Negara, Pilar Negara, Bahasa Indonesia."
        },
        {
            "kategori": "TIU",
            "jumlah": 35,
            "deskripsi": "Kemampuan Verbal (Silogisme/Analitis), Numerik (Hitungan/Soal Cerita), Figural (Gambar)."
        },
        {
            "kategori": "TKP",
            "jumlah": 45,
            "deskripsi": "Pelayanan Publik, Jejaring Kerja, Sosial Budaya, TIK, Profesionalisme, Anti Radikalisme."
        }
    ]
    
    all_questions = []
    batch_size = 10 # Kita pecah request menjadi batch per 10 soal agar AI tidak kelelahan/timeout
    
    print("\n[Proses 2] Mulai membuat soal per kategori secara bertahap...")
    
    for config in skd_config:
        kategori = config["kategori"]
        target_jumlah = config["jumlah"]
        deskripsi = config["deskripsi"]
        
        print(f"\n>> Memproses {kategori} ({target_jumlah} soal) - {deskripsi}")
        
        soal_terkumpul = 0
        while soal_terkumpul < target_jumlah:
            # Tentukan jumlah soal untuk batch ini (maksimal batch_size atau sisa yang dibutuhkan)
            sisa = target_jumlah - soal_terkumpul
            jumlah_batch = batch_size if sisa > batch_size else sisa
            
            print(f"   Mengirim request untuk {jumlah_batch} soal {kategori}...")
            
            batch_data = generate_questions_batch(
                guidelines, 
                sample_questions, 
                kategori, 
                deskripsi, 
                jumlah_batch
            )
            
            if batch_data:
                # Tambahkan data batch ke total list
                all_questions.extend(batch_data)
                soal_terkumpul += len(batch_data)
                print(f"   [+] Berhasil mendapatkan {len(batch_data)} soal {kategori}. Total smentara {kategori}: {soal_terkumpul}/{target_jumlah}")
            else:
                print("   [-] Gagal mendapat respons valid, mencoba lagi setelah jeda...")
                
            # Berikan jeda 5 detik antar request untuk menghindari pembatasan rate limit API gratis (Error 429)
            time.sleep(5) 

    print(f"\n[Proses 3] Menggabungkan hasil akhir dan mengekspor ke Excel...")
    if all_questions:
        save_to_excel(all_questions, output_file)
    else:
        print("[Gagal] Tidak ada soal yang berhasil dibuat.")
    
    print("\n" + "="*50)
    print(" PROGRAM SELESAI")
    print("="*50)

if __name__ == "__main__":
    main()
