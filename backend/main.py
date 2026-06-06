import os
import io
import warnings
from datetime import datetime
from typing import Dict, List

# Dependensi Pihak Ketiga
import pandas as pd
import uvicorn
import google.generativeai as genai
from dotenv import load_dotenv

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. KONFIGURASI DAN ENVIRONMENT
# ==========================================
# Redam FutureWarning dari google.api_core agar log terminal bersih
warnings.simplefilter(action='ignore', category=FutureWarning)
load_dotenv()

STORAGE_DIR = "./stored_files"
os.makedirs(STORAGE_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/db_instant_insight")

# Masukkan API Key Anda di sini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6IiBJgyxgxO8PPuFocI9AAh_RCSgRLK5TqBssC5FCEoUw")

# PERBAIKAN: Langsung configure tanpa pengecekan string yang memblokir
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Tambahkan ini tepat setelah genai.configure
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model tersedia: {m.name}")

# ==========================================
# 2. KONFIGURASI DATABASE (SQLAlchemy)
# ==========================================
engine = create_engine(DATABASE_URL, echo=False, pool_size=15, max_overflow=25)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UploadRecord(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    saved_path = Column(String(500))
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    ai_conclusion = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    columns = relationship("ColumnInsight", back_populates="upload", cascade="all, delete")
    statistics = relationship("StatisticalInsight", back_populates="upload", cascade="all, delete")

class ColumnInsight(Base):
    __tablename__ = "column_insights"
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"))
    name = Column(String(255))
    type = Column(String(50))
    missing_values = Column(Integer)
    anomaly_count = Column(Integer, default=0)
    
    upload = relationship("UploadRecord", back_populates="columns")

class StatisticalInsight(Base):
    __tablename__ = "statistical_insights"
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"))
    column_name = Column(String(255))
    mean = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    min = Column(Float, nullable=True)
    max = Column(Float, nullable=True)
    skewness = Column(Float, nullable=True)
    
    upload = relationship("UploadRecord", back_populates="statistics")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. SERVICES (Analytics & AI)
# ==========================================
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
        # PERBAIKAN: Hapus pengecekan '!= AQ.Ab8...' agar API tidak diblokir
        if not GEMINI_API_KEY: 
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
            Anda adalah Chief Data Scientist di sebuah firma konsultan strategi global. Tugas Anda adalah memberikan "Executive Briefing" berdasarkan analisis data berikut untuk para pemangku kepentingan tingkat C-Suite (CEO/COO/CFO).

            Data yang dianalisis:
            - Nama Berkas: {filename}
            - Dimensi: {rows} baris x {cols} kolom
            - Ringkasan Statistik: {stats_summary}

            Instruksi Penulisan:
            1. GAYA BAHASA: Profesional, analitis, objektif, dan persuasif. Hindari jargon teknis yang tidak perlu tanpa penjelasan singkat. Gunakan gaya bahasa "Bottom Line Up Front" (BLUF)—sampaikan kesimpulan utama terlebih dahulu sebelum detail pendukung.
            2. FORMAT STRUKTUR:
            - BAGIAN 1: KESEHATAN & KARAKTERISTIK DATA (Evaluasi integritas data. Identifikasi apakah data bersifat sintetik/bersih/kotor, dan apa implikasi dari distribusi tersebut terhadap validitas analisis).
            - BAGIAN 2: TEMUAN STRATEGIS & ANOMALI (Jangan hanya membaca angka. Analisis apa arti angka tersebut bagi efisiensi bisnis, risiko operasional, atau peluang pasar).
            - BAGIAN 3: REKOMENDASI TAKTIS & DAMPAK (Berikan setidaknya 3 langkah konkret yang dapat diimplementasikan dalam 30-90 hari ke depan. Kaitkan setiap rekomendasi dengan potensi dampak terhadap KPI atau laba bersih).

            3. BATASAN:
            - Jangan gunakan salam pembuka/penutup yang basa-basi.
            - Gunakan format Markdown (bolding, list, header) yang rapi untuk keterbacaan tinggi.
            - Jika data terlihat memiliki bias atau pola buatan (misal: simetri sempurna), soroti itu sebagai catatan kritis bagi pengambilan keputusan.
            """
        try:
            # Gunakan gemini-1.5-flash (sangat cepat untuk teks & statistik)
            model = genai.GenerativeModel('gemini-3.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"**[Gagal Memanggil Gemini API]**\nDetail Kesalahan: {str(e)}"

# ==========================================
# 4.INISIALISASI FASTAPI & MIDDLEWARE
# ==========================================
print("[DATABASE] Membangun skema tabel relasional relokasi MySQL...")
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Instant Data Insight - Modular Suite", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================
# 5. CORE PIPELINE FUNCTION
# ==========================================
def core_pipeline_processor(df: pd.DataFrame, filename: str, saved_path: str, db: Session):
    rows, cols = df.shape
    
    column_insights = []
    for col in df.columns:
        anomaly_cnt = 0
        if pd.api.types.is_numeric_dtype(df[col]):
            anomaly_cnt = AnalyticsEngine.detect_anomalies(df[col])
        column_insights.append(ColumnInsight(
            name=col, type=str(df[col].dtype),
            missing_values=int(df[col].isnull().sum()), anomaly_count=anomaly_cnt
        ))
        
    statistical_insights = []
    numeric_df = df.select_dtypes(include=['number'])
    if not numeric_df.empty:
        for col in numeric_df.columns:
            skew = df[col].skew()
            statistical_insights.append(StatisticalInsight(
                column_name=col,
                mean=None if pd.isna(df[col].mean()) else float(df[col].mean()),
                median=None if pd.isna(df[col].median()) else float(df[col].median()),
                min=None if pd.isna(df[col].min()) else float(df[col].min()),
                max=None if pd.isna(df[col].max()) else float(df[col].max()),
                skewness=0.0 if pd.isna(skew) else float(skew)
            ))
            
    stats_payload = [{
        "column": s.column_name, "mean": s.mean, "median": s.median,
        "min": s.min, "max": s.max, "skewness": s.skewness
    } for s in statistical_insights]
    
    ai_text = AIService.generate_executive_summary(filename, rows, cols, stats_payload)
    correlation_data = AnalyticsEngine.calculate_correlation(df)
    
    db_upload = UploadRecord(
        filename=filename, saved_path=saved_path, total_rows=rows, total_columns=cols, ai_conclusion=ai_text
    )
    db_upload.columns = column_insights
    db_upload.statistics = statistical_insights
    
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    
    return {
        "id": db_upload.id, "filename": db_upload.filename,
        "summary": {"total_rows": rows, "total_columns": cols},
        "ai_conclusion": db_upload.ai_conclusion,
        "columns": [{"name": c.name, "type": c.type, "missing_values": c.missing_values, "anomaly_count": c.anomaly_count} for c in db_upload.columns],
        "statistics": stats_payload,
        "correlation": correlation_data
    }

# ==========================================
# 6. ROUTERS (API Endpoints)
# ==========================================
analyze_router = APIRouter(prefix="/api", tags=["Data Analysis Pipeline"])
history_router = APIRouter(prefix="/api", tags=["History Repository"])

# --- Endpoint Analyze ---
@analyze_router.post("/analyze")
def analyze_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Wajib berkas berekstensi .csv")
    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        saved_path = os.path.join(STORAGE_DIR, safe_filename)
        
        with open(saved_path, "wb") as f:
            f.write(contents)
            
        return core_pipeline_processor(df, file.filename, saved_path, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eror Analisis: {str(e)}")

@analyze_router.post("/clean/{record_id}")
def clean_dataset(record_id: int, strategy: str = Body(embed=True), db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record or not os.path.exists(record.saved_path):
        raise HTTPException(status_code=404, detail="Berkas tidak ditemukan untuk dibersihkan")
        
    df = pd.read_csv(record.saved_path)
    
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                fill_val = df[col].mean() if strategy == "mean" else df[col].median()
                df[col] = df[col].fillna(fill_val)
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "UNKNOWN")
                
    if strategy == "drop_outliers":
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            
    cleaned_filename = f"Cleaned_{strategy}_{record.filename}"
    cleaned_path = os.path.join(STORAGE_DIR, f"cleaned_{datetime.now().strftime('%Y%m%d%H%M%S')}_{record.filename}")
    df.to_csv(cleaned_path, index=False)
    
    return core_pipeline_processor(df, cleaned_filename, cleaned_path, db)

# --- Endpoint History ---
@history_router.get("/history")
def get_upload_history(db: Session = Depends(get_db)):
    records = db.query(UploadRecord).order_by(UploadRecord.uploaded_at.desc()).all()
    return [{
        "id": r.id, "filename": r.filename, "total_rows": r.total_rows,
        "total_columns": r.total_columns, "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
    } for r in records]

@history_router.get("/history/{record_id}")
def get_single_history(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record: raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    if not os.path.exists(record.saved_path):
        raise HTTPException(status_code=404, detail="Berkas fisik CSV hilang di server.")
        
    df = pd.read_csv(record.saved_path)
    correlation_data = AnalyticsEngine.calculate_correlation(df)
    
    return {
        "id": record.id, "filename": record.filename,
        "summary": {"total_rows": record.total_rows, "total_columns": record.total_columns},
        "ai_conclusion": record.ai_conclusion,
        "columns": [{"name": c.name, "type": c.type, "missing_values": c.missing_values, "anomaly_count": c.anomaly_count} for c in record.columns],
        "statistics": [{"column": s.column_name, "mean": s.mean, "median": s.median, "min": s.min, "max": s.max, "skewness": s.skewness} for s in record.statistics],
        "correlation": correlation_data
    }

@history_router.get("/export-pdf/{record_id}")
def export_pdf_report(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record: raise HTTPException(status_code=404, detail="Data insight tidak ditemukan")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1E3A8A'), spaceAfter=15)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=25)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0F766E'), spaceBefore=15, spaceAfter=10)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=10)
    
    story.append(Paragraph("OFFICIAL EXECUTIVE DATA INSIGHT REPORT", title_style))
    story.append(Paragraph(f"Dibuat Otomatis pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ID Dokumen: #{record.id}", subtitle_style))
    
    story.append(Paragraph("1. Metadata Ringkasan Dataset", h2_style))
    meta_data = [
        [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Nilai Informasi</b>", body_style)],
        [Paragraph("Nama Berkas Asal", body_style), Paragraph(record.filename, body_style)],
        [Paragraph("Total Baris Data", body_style), Paragraph(str(record.total_rows), body_style)],
        [Paragraph("Total Variabel (Kolom)", body_style), Paragraph(str(record.total_columns), body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[150, 350])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. Kesimpulan Naratif Strategis AI", h2_style))
    clean_ai_text = record.ai_conclusion.replace("**", "").replace("*", "-") if record.ai_conclusion else "Tidak ada konklusi AI."
    for para in clean_ai_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
            
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Insight_Report_{record.id}.pdf"})

# Tambahkan ini ke dalam routers di main.py

@history_router.delete("/history/{record_id}")
def delete_history(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    
    # Hapus file fisik
    if os.path.exists(record.saved_path):
        os.remove(record.saved_path)
    
    # Hapus dari DB
    db.delete(record)
    db.commit()
    return {"message": "Data berhasil dihapus"}

# ==========================================
# 7. MENAMBAHKAN ROUTER KE APLIKASI
# ==========================================
app.include_router(analyze_router)
app.include_router(history_router)

@app.get("/")
def read_root():
    return {"status": "Online", "engine": "FastAPI Threads Optimized"}

# ==========================================
# 8. MENJALANKAN SERVER
# ==========================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)