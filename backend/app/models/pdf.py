"""PDF version models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PDFVersion(BaseModel):
    """PDF version information"""
    version_id: str = Field(..., description="Version identifier (v1, v2, v3...)")
    job_id: str = Field(..., description="Associated job ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: str = Field(..., description="Path to PDF file")
    file_size_bytes: int = Field(..., ge=0)
    
    # Version metadata
    parent_version: Optional[str] = None
    change_description: Optional[str] = None
    edited_by: Optional[str] = None
    
    # Content metrics
    num_pages: int = Field(..., ge=1)
    num_images: int = Field(..., ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "v1",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_path": "storage/pdfs/550e8400-e29b-41d4-a716-446655440000_v1.pdf",
                "file_size_bytes": 2048576,
                "num_pages": 15,
                "num_images": 12
            }
        }
