"""Upload endpoint for video and transcript files"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=Dict[str, str])
async def upload_files(
    video: UploadFile = File(..., description="Video file (.mp4)"),
    transcript: UploadFile = File(..., description="Transcript file (.txt)")
):
    """
    Upload video and transcript files to start PDF generation
    
    Returns:
        job_id: Unique identifier for tracking processing status
    """
    # TODO: Validate file types and sizes
    # TODO: Save files to storage
    # TODO: Create job in database
    # TODO: Start background processing task
    
    job_id = str(uuid.uuid4())
    
    logger.info(f"Created job {job_id} for video: {video.filename}")
    
    return {
        "job_id": job_id,
        "message": "Files uploaded successfully. Processing started.",
        "video_filename": video.filename,
        "transcript_filename": transcript.filename
    }
