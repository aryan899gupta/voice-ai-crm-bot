# mock_crm.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional
from datetime import datetime

app = FastAPI(title="Mock CRM")

class LeadCreate(BaseModel):
    name: str
    phone: str
    city: str
    source: Optional[str] = None

class VisitCreate(BaseModel):
    lead_id: str
    visit_time: datetime
    notes: Optional[str] = None

class LeadStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(NEW|IN_PROGRESS|FOLLOW_UP|WON|LOST)$')
    notes: Optional[str] = None

# In-memory stores
LEADS = {}
VISITS = {}

@app.post("/crm/leads")
def create_lead(payload: LeadCreate):
    lead_id = str(uuid4())
    LEADS[lead_id] = {**payload.dict(), "lead_id": lead_id, "status": "NEW"}
    return {"lead_id": lead_id, "status": "NEW"}

@app.post("/crm/visits")
def create_visit(payload: VisitCreate):
    if payload.lead_id not in LEADS:
        raise HTTPException(status_code=404, detail="Lead not found")
    visit_id = str(uuid4())
    VISITS[visit_id] = {**payload.dict(), "visit_id": visit_id, "status": "SCHEDULED"}
    return {"visit_id": visit_id, "status": "SCHEDULED"}

@app.post("/crm/leads/{lead_id}/status")
def update_lead_status(lead_id: str, payload: LeadStatusUpdate):
    if lead_id not in LEADS:
        raise HTTPException(status_code=404, detail="Lead not found")
    LEADS[lead_id]["status"] = payload.status
    return {"lead_id": lead_id, "status": payload.status}