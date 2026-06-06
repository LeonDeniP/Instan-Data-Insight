from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from app.config import DATABASE_URL

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