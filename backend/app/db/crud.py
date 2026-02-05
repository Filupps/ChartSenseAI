from sqlalchemy.orm import Session
from . import models, schemas


def get_or_create_session(db: Session, session_id: str) -> models.Session:
    db_session = db.query(models.Session).filter(
        models.Session.session_id == session_id
    ).first()
    
    if not db_session:
        db_session = models.Session(session_id=session_id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    
    return db_session


def create_processing(db: Session, data: schemas.ProcessingCreate) -> models.Processing:
    session = get_or_create_session(db, data.session_id)
    
    db_processing = models.Processing(
        session_id=session.id,
        image_filename=data.image_filename,
        image_path=data.image_path,
        image_size=data.image_size,
        model_version=data.model_version,
        processing_time_ms=data.processing_time_ms,
        detected_shapes=data.detected_shapes,
        detected_arrows=data.detected_arrows,
        detected_text_regions=data.detected_text_regions,
        detection_result=data.detection_result,
        graph_result=data.graph_result,
        algorithm_result=data.algorithm_result
    )
    db.add(db_processing)
    db.commit()
    db.refresh(db_processing)
    return db_processing


def create_diagram_generation(db: Session, data: schemas.DiagramGenerationCreate) -> models.DiagramGeneration:
    session = get_or_create_session(db, data.session_id)
    
    db_gen = models.DiagramGeneration(
        session_id=session.id,
        input_type=data.input_type,
        input_text=data.input_text,
        input_file_name=data.input_file_name,
        input_file_content=data.input_file_content,
        plantuml_code=data.plantuml_code,
        diagram_url=data.diagram_url,
        llm_model=data.llm_model,
        generation_time_ms=data.generation_time_ms
    )
    db.add(db_gen)
    db.commit()
    db.refresh(db_gen)
    return db_gen


def create_code_generation(db: Session, data: schemas.CodeGenerationCreate) -> models.CodeGeneration:
    db_gen = models.CodeGeneration(
        processing_id=data.processing_id,
        code_type=data.code_type,
        generated_code=data.generated_code,
        llm_model=data.llm_model,
        generation_time_ms=data.generation_time_ms
    )
    db.add(db_gen)
    db.commit()
    db.refresh(db_gen)
    return db_gen


def get_session_history(db: Session, session_id: str) -> dict:
    session = db.query(models.Session).filter(
        models.Session.session_id == session_id
    ).first()
    
    if not session:
        return None
    
    processings = db.query(models.Processing).filter(
        models.Processing.session_id == session.id
    ).order_by(models.Processing.created_at.desc()).all()
    
    generations = db.query(models.DiagramGeneration).filter(
        models.DiagramGeneration.session_id == session.id
    ).order_by(models.DiagramGeneration.created_at.desc()).all()
    
    return {
        "session": session,
        "processings": processings,
        "generations": generations
    }


def get_all_sessions(db: Session, limit: int = 50):
    return db.query(models.Session).order_by(
        models.Session.created_at.desc()
    ).limit(limit).all()


def get_processing_by_id(db: Session, processing_id: int) -> models.Processing:
    return db.query(models.Processing).filter(
        models.Processing.id == processing_id
    ).first()

