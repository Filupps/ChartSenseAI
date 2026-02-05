from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    processings = relationship("Processing", back_populates="session")
    generations = relationship("DiagramGeneration", back_populates="session")


class Processing(Base):
    __tablename__ = "processings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    
    image_filename = Column(String(255))
    image_path = Column(String(512))
    image_size = Column(Integer)
    
    model_version = Column(String(64))
    processing_time_ms = Column(Float)
    
    detected_shapes = Column(Integer)
    detected_arrows = Column(Integer)
    detected_text_regions = Column(Integer)
    
    detection_result = Column(JSON)
    graph_result = Column(JSON)
    algorithm_result = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="processings")


class DiagramGeneration(Base):
    __tablename__ = "diagram_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    
    input_type = Column(String(32))
    input_text = Column(Text)
    input_file_name = Column(String(255), nullable=True)
    input_file_content = Column(Text, nullable=True)
    
    plantuml_code = Column(Text)
    diagram_url = Column(String(1024))
    
    llm_model = Column(String(64))
    generation_time_ms = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="generations")


class CodeGeneration(Base):
    __tablename__ = "code_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    processing_id = Column(Integer, ForeignKey("processings.id"))
    
    code_type = Column(String(32))
    generated_code = Column(Text)
    llm_model = Column(String(64))
    generation_time_ms = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

