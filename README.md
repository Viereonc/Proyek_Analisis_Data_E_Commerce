# 🛒 E-Commerce Brasil — Data Analysis Dashboard

Dashboard interaktif hasil analisis dataset publik **Brazilian E-Commerce (Olist)** yang mencakup periode 2016–2018. Proyek ini dibuat sebagai bagian dari submission kelas **Belajar Analisis Data dengan Python** di Dicoding.

---

## 📁 Struktur Proyek

```
submission/
├── dashboard/
│   └── dashboard.py
├── data/
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── products_dataset.csv
│   ├── customers_dataset.csv
│   ├── sellers_dataset.csv
│   ├── geolocation_dataset.csv
│   └── product_category_name_translation.csv
├── notebook.ipynb
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Environment

### Menggunakan Anaconda

```bash
conda create --name ecommerce-ds python=3.11
conda activate ecommerce-ds
pip install -r requirements.txt
```

### Menggunakan venv (pip)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## 🚀 Menjalankan Dashboard

Pastikan kamu sudah berada di direktori root proyek, lalu jalankan perintah berikut:

```bash
cd dashboard
streamlit run dashboard.py
```

Dashboard akan otomatis terbuka di browser pada alamat:

```
http://localhost:8501
```

---

## 📊 Fitur Dashboard

| Menu | Deskripsi |
|------|-----------|
| **Overview** | KPI utama (total order, revenue, avg order, avg skor ulasan) dan tren revenue bulanan beserta MoM growth |
| **Revenue & Kategori** | Top N kategori produk berdasarkan total revenue dengan filter slider |
| **Pengiriman & Ulasan** | Korelasi waktu pengiriman, keterlambatan, dan distribusi skor ulasan pelanggan |
| **Pembayaran** | Distribusi metode pembayaran dan rata-rata nilai transaksi per metode |
| **Analisis Lanjutan** | Segmentasi pelanggan, analisis keterlambatan, repeat purchase & retention, serta peta revenue per state |

Semua halaman mendukung **filter tahun** (2016–2018) melalui sidebar.

---

## 📬 Kontak

| | |
|---|---|
| **Nama** | *(Nama kamu)* |
| **Email** | *(Email kamu)* |
| **Dicoding** | *(Username Dicoding kamu)* |
