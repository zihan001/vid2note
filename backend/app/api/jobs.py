"""Job status and management endpoints"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import logging

from app.models import Job, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job_status(job_id: str):
    """
    Get the current status of a job
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status and progress information
    """
    # TODO: Query database for job
    # TODO: Return job details
    
    # Mock response for now
    return Job(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        video_filename="example.mp4",
        transcript_filename="example.txt",
        progress_percentage=45,
        current_stage="Verifying images"
    )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> Dict[str, str]:
    """
    Cancel a running job
    
    Args:
        job_id: Job identifier
    """
    # TODO: Cancel background task
    # TODO: Update job status to FAILED
    # TODO: Cleanup temporary files
    
    logger.info(f"Job {job_id} cancelled")
    
    return {"message": f"Job {job_id} cancelled successfully"}
