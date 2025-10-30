from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ClaimLine(BaseModel):
    line_type: str  # 'PROC' or 'DRUG'
    code: str
    qty: float
    days: Optional[int] = None
    amount: Optional[int] = None


class Claim(BaseModel):
    provider_id: str
    patient_rid: str
    visit_date: date
    primary_dx: str
    sub_dx: List[str] = Field(default_factory=list)
    lines: List[ClaimLine] = Field(default_factory=list)
