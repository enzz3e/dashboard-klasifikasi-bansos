# Dashboard Klasifikasi Kelayakan Penerima Bantuan Sosial

Aplikasi dashboard berbasis web yang menerapkan algoritma **Decision Tree C4.5** untuk membantu klasifikasi status kesejahteraan rumah tangga dan menyajikan informasi pendukung terkait penyaluran bantuan sosial.

Project ini dikembangkan sebagai implementasi tugas akhir dengan studi kasus Kelurahan Tanjung Perak, Kota Surabaya.

## Fitur Utama

- **Dashboard Overview** — Menampilkan ringkasan data dan distribusi klasifikasi kesejahteraan.
- **Peta Wilayah RW** — Visualisasi wilayah berdasarkan kategori hasil klasifikasi.
- **Analisis Data** — Menampilkan distribusi pendidikan, pekerjaan, dan pendapatan.
- **Prediksi Klasifikasi** — Formulir untuk melakukan prediksi menggunakan model Decision Tree C4.5.
- **Rekomendasi Prioritas** — Menampilkan daftar rumah tangga berdasarkan hasil klasifikasi.
- **Direktori Data** — Fitur pencarian dan penyaringan data rumah tangga.
- **Ringkasan Wilayah** — Menyajikan rekapitulasi klasifikasi pada setiap RW.

## Teknologi yang Digunakan

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Plotly
- Folium
- Streamlit-Folium
- Shapely
- Joblib

## Algoritma

Algoritma utama yang digunakan adalah **Decision Tree C4.5** dengan pendekatan klasifikasi berdasarkan atribut sosial ekonomi rumah tangga.

Kategori klasifikasi:
- Miskin
- Pra Sejahtera
- Sejahtera

## Struktur Repository

```text
dashboard-klasifikasi-bansos/
├── app.py
├── hasil_prediksi_c45.csv
├── model_c45.joblib
├── le_pekerjaan.joblib
├── PetaRW.geojson
├── notebook_public.ipynb
├── requirements.txt
└── README.md
```

## Instalasi dan Menjalankan Aplikasi

1. Clone repository:

```bash
git clone https://github.com/enzz3e/dashboard-klasifikasi-bansos.git
```

2. Masuk ke direktori project:

```bash
cd dashboard-klasifikasi-bansos
```

3. Instal dependency:

```bash
pip install -r requirements.txt
```

4. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Catatan Data

Repository ini menggunakan data sintetis untuk keperluan demonstrasi dan portofolio. Data tersebut bukan data identitas maupun data aktual rumah tangga. Batas wilayah RW pada peta digunakan sebagai referensi visualisasi wilayah studi kasus.

## Pengembangan

Project ini dikembangkan sebagai prototipe sistem pendukung keputusan untuk membantu proses klasifikasi dan penyajian informasi sosial ekonomi rumah tangga. Hasil klasifikasi merupakan rekomendasi berbasis model dan bukan keputusan resmi penetapan penerima bantuan sosial.
