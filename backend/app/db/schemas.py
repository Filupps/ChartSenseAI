from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class SessionCreate(BaseModel):
    session_id: str


class SessionResponse(BaseModel):
    id: int
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProcessingCreate(BaseModel):
    session_id: str
    image_filename: str
    image_path: str
    image_size: int
    model_version: str
    processing_time_ms: float
    detected_shapes: int
    detected_arrows: int
    detected_text_regions: int
    detection_result: Optional[Any] = None
    graph_result: Optional[Any] = None
    algorithm_result: Optional[Any] = None


class ProcessingResponse(BaseModel):
    id: int
    image_filename: str
    model_version: str
    processing_time_ms: float
    detected_shapes: int
    detected_arrows: int
    detected_text_regions: int
    algorithm_result: Optional[Any] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiagramGenerationCreate(BaseModel):
    session_id: str
    input_type: str
    input_text: str
    input_file_name: Optional[str] = None
    input_file_content: Optional[str] = None
    plantuml_code: str
    diagram_url: str
    llm_model: str
    generation_time_ms: float


class DiagramGenerationResponse(BaseModel):
    id: int
    input_type: str
    plantuml_code: str
    diagram_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CodeGenerationCreate(BaseModel):
    processing_id: int
    code_type: str
    generated_code: str
    llm_model: str
    generation_time_ms: float


class CodeGenerationResponse(BaseModel):
    id: int
    code_type: str
    generated_code: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionHistory(BaseModel):
    session: SessionResponse
    processings: list[ProcessingResponse]
    generations: list[DiagramGenerationResponse]

