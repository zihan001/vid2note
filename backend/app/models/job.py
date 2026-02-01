"""Job management models"""

from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job information"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.UPLOADED)
    video_filename: str
    transcript_filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Progress tracking
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_stage: Optional[str] = None
    
    # Result
    pdf_version: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "video_filename": "lecture.mp4",
                "transcript_filename": "lecture.txt",
                "progress_percentage": 45,
                "current_stage": "Verifying images"
            }
        }
