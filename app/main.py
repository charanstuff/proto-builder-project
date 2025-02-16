# app/main.py
from fastapi import FastAPI
from app.routes.campaigns.campaigns import router as campaigns_router
from app.routes.leads.leads import router as leads_router
from app.routes.llm.llm import router as llm_router
from app.routes.outreach.outreach import router as outreach_router
from app.routes.scoring.scoring import router as scoring_router
from app.routes.analytics.analytics import router as analytics_router
from app.routes.product_context.product_context import router as product_context_router

app = FastAPI(title="Sales Outreach AI Agent")

app.include_router(campaigns_router, prefix="/api/campaigns")
app.include_router(leads_router, prefix="/api/leads")
app.include_router(llm_router, prefix="/api/llm")
app.include_router(outreach_router, prefix="/api/outreach")
app.include_router(scoring_router, prefix="/api/scoring")
app.include_router(analytics_router, prefix="/api/analytics")
app.include_router(product_context_router, prefix="/api/product_context")
