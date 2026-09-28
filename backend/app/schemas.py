from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str


class AnalysisResult(BaseModel):
    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: list[str] = Field(default_factory=list)
    h2: list[str] = Field(default_factory=list)
    word_count: int = 0
    analyzed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
