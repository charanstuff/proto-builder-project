# app/routes/product_context/product_context.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import SessionLocal, ProductContext

router = APIRouter()

class ProductContextRequest(BaseModel):
    user_id: int
    context_data: dict  # JSON object representing product context

class ProductContextResponse(BaseModel):
    id: int
    user_id: int
    context_data: dict
    updated_at: datetime

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=ProductContextResponse)
def get_product_context(user_id: int, db: Session = Depends(get_db)):
    context = db.query(ProductContext).filter(ProductContext.user_id == user_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="Product context not found")
    return context

@router.post("/", response_model=ProductContextResponse)
def update_product_context(req: ProductContextRequest, db: Session = Depends(get_db)):
    context = db.query(ProductContext).filter(ProductContext.user_id == req.user_id).first()
    if context:
        context.context_data = str(req.context_data)  # store as string; in production, consider a JSON type
        context.updated_at = datetime.utcnow()
    else:
        context = ProductContext(
            user_id=req.user_id,
            context_data=str(req.context_data),
            updated_at=datetime.utcnow()
        )
        db.add(context)
    db.commit()
    db.refresh(context)
    return context
