from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import io
import time
import uuid
from PIL import Image

from app.services.inference import process_diagram
from app.db.database import get_db
from app.db import crud, schemas
from app.models.yolo_model import get_model_info
from app.api.auth import verify_api_key

router = APIRouter()


def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    return x_session_id or str(uuid.uuid4())


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        start_time = time.time()
        
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        result = await process_diagram(image)
        
        processing_time = (time.time() - start_time) * 1000
        
        result["session_id"] = session_id
        result["processing_time_ms"] = processing_time
        
        # Сохранение в БД (опционально, не блокирует основной функционал)
        try:
            model_info = get_model_info()
            
            # Получаем bounding_boxes правильно
            bboxes = result.get("bounding_boxes", {})
            if isinstance(bboxes, dict):
                all_boxes = bboxes.get("all", [])
                arrows = bboxes.get("arrows", [])
            else:
                all_boxes = bboxes if isinstance(bboxes, list) else []
                arrows = [b for b in all_boxes if b.get("class_name") == "arrow"]
            
            processing_data = schemas.ProcessingCreate(
                session_id=session_id,
                image_filename=file.filename or "unknown",
                image_path="",
                image_size=len(contents),
                model_version=model_info.get("model_name", "unknown"),
                processing_time_ms=processing_time,
                detected_shapes=len(result.get("shape_texts", {})),
                detected_arrows=len(arrows),
                detected_text_regions=len(result.get("text_regions", {})),
                detection_result=all_boxes,
                graph_result=result.get("graph"),
                algorithm_result=result.get("algorithm")
            )
            
            db_processing = crud.create_processing(db, processing_data)
            result["processing_id"] = db_processing.id
            print(f" Saved to DB: processing_id={db_processing.id}")
        except Exception as db_error:
            print(f" DB save failed (non-critical): {db_error}")
            result["processing_id"] = None
        
        return JSONResponse(content=result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/diagram-generation")
async def save_diagram_generation(
    data: schemas.DiagramGenerationCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    try:
        db_gen = crud.create_diagram_generation(db, data)
        return {"id": db_gen.id, "status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-generation")
async def save_code_generation(
    data: schemas.CodeGenerationCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    try:
        db_gen = crud.create_code_generation(db, data)
        return {"id": db_gen.id, "status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    history = crud.get_session_history(db, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session": {
            "id": history["session"].id,
            "session_id": history["session"].session_id,
            "created_at": history["session"].created_at.isoformat()
        },
        "processings": [
            {
                "id": p.id,
                "image_filename": p.image_filename,
                "model_version": p.model_version,
                "processing_time_ms": p.processing_time_ms,
                "detected_shapes": p.detected_shapes,
                "detected_arrows": p.detected_arrows,
                "created_at": p.created_at.isoformat()
            }
            for p in history["processings"]
        ],
        "generations": [
            {
                "id": g.id,
                "input_type": g.input_type,
                "plantuml_code": g.plantuml_code,
                "diagram_url": g.diagram_url,
                "created_at": g.created_at.isoformat()
            }
            for g in history["generations"]
        ]
    }


@router.get("/sessions")
async def get_all_sessions(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    sessions = crud.get_all_sessions(db, limit)
    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]


@router.get("/processing/{processing_id}")
async def get_processing(
    processing_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    processing = crud.get_processing_by_id(db, processing_id)
    if not processing:
        raise HTTPException(status_code=404, detail="Processing not found")
    
    return {
        "id": processing.id,
        "image_filename": processing.image_filename,
        "model_version": processing.model_version,
        "processing_time_ms": processing.processing_time_ms,
        "detected_shapes": processing.detected_shapes,
        "detected_arrows": processing.detected_arrows,
        "detected_text_regions": processing.detected_text_regions,
        "detection_result": processing.detection_result,
        "graph_result": processing.graph_result,
        "algorithm_result": processing.algorithm_result,
        "created_at": processing.created_at.isoformat()
    }
