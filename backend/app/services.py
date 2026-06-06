import pandas as pd
from typing import Dict, List
import google.generativeai as genai
from app.config import GEMINI_API_KEY

if GEMINI_API_KEY and GEMINI_API_KEY != "AQ.Ab8RN6JDN8u1_0oDyK2B2UnT_fGIkTskNhFP0dpnrYjzp4OIqA":
    genai.configure(api_key=GEMINI_API_KEY)

class AnalyticsEngine:
    @staticmethod
    def detect_anomalies(series: pd.Series) -> int:
        if series.dropna().empty: return 0
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        anomalies = series[(series < lower_bound) | (series > upper_bound)]
        return int(anomalies.count())

    @staticmethod
    def calculate_correlation(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty: return {}
        return numeric_df.corr().fillna(0).round(2).to_dict()

class AIService:
    @staticmethod
    def generate_executive_summary(filename: str, rows: int, cols: int, stats: List[Dict]) -> str:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "AQ.Ab8RN6JDN8u1_0oDyK2B2UnT_fGIkTskNhFP0dpnrYjzp4OIqA":
            return (
                "**[MODE SIMULASI - GEMINI API KEY BELUM DIKONFIGURASI]**\n\n"
                f"Sistem Enterprise mendeteksi berkas `{filename}` berkuran {rows}x{cols}.\n"
                "Saran tindakan: Masukkan API Key valid di backend untuk mengaktifkan AI Insight Analyst."
            )
        
        stats_summary = "\n".join([
            f"- '{s['column']}': Mean={s['mean']}, Min={s['min']}, Max={s['max']}, Skew={s['skewness']}"
            for s in stats[:10]
        ])

        prompt = f"""
Anda adalah Chief Data Scientist di Perusahaan Korporat Besar. Berikan "Executive Insight Narrative" dari data berikut:
Nama Berkas: {filename}
Dimensi: {rows} baris x {cols} kolom
Ringkasan Statistik Deskriptif:
{stats_summary}

Berikan analisis mendalam dalam Bahasa Indonesia dengan format terstruktur:
1. **Kesehatan & Karakteristik Data**: Evaluasi kebersihan data, distribusi, dan struktur umumnya.
2. **Temuan Utama & Pola Kunci**: Jabarkan korelasi dan tren data yang paling menonjol dari statistik deskriptif di atas.
3. **Rekomendasi Bisnis & Aksi Lanjutan**: Berikan minimal 2 poin langkah taktis bagi manajemen puncak untuk mengambil keputusan berdasarkan pola data ini.

Gunakan bahasa profesional, objektif, tajam, dan langsung tanpa salam pembuka.
"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"**[Gagal Memanggil Gemini API]**\nDetail Kesalahan: {str(e)}"