# app/routes/llm/llm.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.models import SessionLocal, LLMConfig

router = APIRouter()

class LLMConfigResponse(BaseModel):
    id: int
    provider_name: str
    api_key: str
    settings: str

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/providers", response_model=List[LLMConfigResponse])
def list_llm_providers(db: Session = Depends(get_db)):
    providers = db.query(LLMConfig).all()
    return providers

class LLMTestRequest(BaseModel):
    prompt: str

class LLMTestResponse(BaseModel):
    response_text: str

@router.post("/test", response_model=LLMTestResponse)
def test_llm(request: LLMTestRequest):
    # Dummy implementation: in a real scenario, you'd call the LLM API
    dummy_response = f"LLM response for prompt: {request.prompt}"
    return LLMTestResponse(response_text=dummy_response)
