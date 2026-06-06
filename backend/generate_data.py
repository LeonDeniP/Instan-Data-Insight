import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def create_massive_csv(filename="data_masif_10k.csv", n_rows=10000):
    print(f"Sedang membuat {n_rows} baris data simulasi...")
    
    # Set seed agar hasil random-nya konsisten tiap kali dijalankan
    np.random.seed(42)
    
    # Pilihan data dummy
    kategori_list = ['Elektronik', 'Pakaian', 'Makanan & Minuman', 'Kecantikan', 'Olahraga', 'Home & Living']
    metode_bayar = ['Transfer Bank', 'E-Wallet', 'Kartu Kredit', 'COD']
    kota_list = ['Jakarta', 'Semarang', 'Surabaya', 'Bandung', 'Medan']
    
    # Generate data secara acak menggunakan NumPy (sangat cepat)
    data = {
        'ID_Transaksi': range(100001, 100001 + n_rows),
        'Tanggal': [datetime(2026, 1, 1) + timedelta(minutes=int(x)) for x in np.random.randint(0, 200000, n_rows)],
        'Kota': np.random.choice(kota_list, n_rows),
        'Kategori': np.random.choice(kategori_list, n_rows),
        'Harga_Satuan_USD': np.random.uniform(5.0, 1500.0, n_rows).round(2),
        'Jumlah_Beli': np.random.randint(1, 20, n_rows),
        'Rating_Produk': np.random.uniform(1.0, 5.0, n_rows).round(1)
    }
    
    # Ubah menjadi Pandas DataFrame
    df = pd.DataFrame(data)
    
    # --- SIMULASI MISSING VALUES (Data Kosong) ---
    # Kita sengaja buat beberapa baris kosong untuk ngetes fitur 'missing values' di dashboard
    df.loc[df.sample(frac=0.02).index, 'Kategori'] = np.nan       # 2% data Kategori kosong
    df.loc[df.sample(frac=0.04).index, 'Jumlah_Beli'] = np.nan     # 4% data Jumlah Beli kosong
    df.loc[df.sample(frac=0.07).index, 'Rating_Produk'] = np.nan   # 7% data Rating kosong
    
    # Simpan ke CSV
    df.to_csv(filename, index=False)
    print(f"Sukses! File berhasil disimpan dengan nama: {os.path.abspath(filename)}")

if __name__ == "__main__":
    # Kamu bisa ganti angka 10000 di bawah ini menjadi 50000 atau 100000 jika ingin lebih ekstrem
    create_massive_csv(filename="data_masif_10k.csv", n_rows=10000)