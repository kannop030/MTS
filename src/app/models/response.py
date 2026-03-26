from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class JobCreated(BaseModel):
    job_id: str
    status: str
    filename: str
    created_at: datetime


class StepStatus(BaseModel):
    transcribing: Literal["pending", "in_progress", "completed", "skipped", "failed"] = "pending"
    extracting:   Literal["pending", "in_progress", "completed", "skipped", "failed"] = "pending"
    summarizing:  Literal["pending", "in_progress", "completed", "skipped", "failed"] = "pending"
    minutes:      Literal["pending", "in_progress", "completed", "skipped", "failed"] = "pending"


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: int = 0
    current_step: Optional[str] = None
    steps: StepStatus = StepStatus()
    error: Optional[str] = None


class ResultFiles(BaseModel):
    transcript:   Optional[str] = None
    slides:       list[str] = []
    slides_text:  Optional[str] = None
    summary:      Optional[str] = None
    minutes:      Optional[str] = None


class JobResult(BaseModel):
    job_id: str
    status: str
    files: ResultFiles


class HealthResponse(BaseModel):
    status: str
    ollama: str
    whisper_model: str
