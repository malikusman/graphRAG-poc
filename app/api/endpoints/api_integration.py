"""
API endpoints for external API integration with GraphRAG pipeline
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.tasks.api_processing_tasks import process_api_sections, process_api_sections_with_config
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-integration", tags=["API Integration"])


class APIProcessingRequest(BaseModel):
    """Request model for API processing"""
    endpoint: str = Field(default="/sections/for-mapping/", description="API endpoint to fetch sections from")
    token: Optional[str] = Field(default=None, description="Bearer token for API authentication")
    max_sections: int = Field(default=5, ge=1, le=20, description="Maximum number of sections to process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/sections/for-mapping/",
                "token": "eyJhbGciOiJSUzI1NilsInR5cCl6lkpXVCIsImtj...",
                "max_sections": 5
            }
        }


class APIProcessingResponse(BaseModel):
    """Response model for API processing"""
    task_id: str = Field(..., description="Celery task ID")
    message: str = Field(..., description="Status message")
    endpoint: str = Field(..., description="API endpoint being processed")
    max_sections: int = Field(..., description="Maximum sections to process")


@router.post("/process-sections", response_model=APIProcessingResponse)
async def process_api_sections_endpoint(
    request: APIProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process sections from external API through GraphRAG pipeline
    
    This endpoint fetches sections from an external API, filters them for valid content,
    and processes them through the GraphRAG pipeline to extract entities and relationships.
    
    - **endpoint**: API endpoint to fetch sections from (default: /sections/for-mapping/)
    - **token**: Bearer token for API authentication (optional, uses default if not provided)
    - **max_sections**: Maximum number of sections to process (1-20, default: 5)
    
    Returns a task ID for tracking the processing status.
    """
    try:
        logger.info(f"Starting API section processing for endpoint: {request.endpoint}")
        
        # Use provided token or fall back to settings
        api_token = request.token or getattr(settings, 'EXTERNAL_API_TOKEN', '')
        
        if not api_token:
            raise HTTPException(
                status_code=400,
                detail="API token is required. Provide token in request or set EXTERNAL_API_TOKEN in settings."
            )
        
        # Start background task
        task = process_api_sections.delay(
            api_endpoint=request.endpoint,
            api_token=api_token,
            max_sections=request.max_sections
        )
        
        logger.info(f"Started API processing task: {task.id}")
        
        return APIProcessingResponse(
            task_id=task.id,
            message=f"API processing started. Will process up to {request.max_sections} sections from {request.endpoint}",
            endpoint=request.endpoint,
            max_sections=request.max_sections
        )
        
    except Exception as e:
        logger.error(f"Error starting API processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start API processing: {str(e)}")


@router.post("/process-sections-sync")
async def process_api_sections_sync(request: APIProcessingRequest):
    """
    Process sections from external API synchronously (for testing)
    
    This endpoint processes API sections synchronously and returns the results immediately.
    Use this for testing or when you need immediate results.
    """
    try:
        logger.info(f"Starting synchronous API section processing for endpoint: {request.endpoint}")
        
        # Use provided token or fall back to settings
        api_token = request.token or getattr(settings, 'EXTERNAL_API_TOKEN', '')
        
        if not api_token:
            raise HTTPException(
                status_code=400,
                detail="API token is required. Provide token in request or set EXTERNAL_API_TOKEN in settings."
            )
        
        # Process synchronously
        result = process_api_sections(
            api_endpoint=request.endpoint,
            api_token=api_token,
            max_sections=request.max_sections
        )
        
        logger.info(f"Completed synchronous API processing: {result.get('success', False)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in synchronous API processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API processing failed: {str(e)}")


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of an API processing task
    
    - **task_id**: The Celery task ID returned from the process-sections endpoint
    
    Returns the current status and results of the processing task.
    """
    try:
        from celery.result import AsyncResult
        from app.tasks.celery_app import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task_result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Task is currently being processed",
                "progress": task_result.info
            }
        elif task_result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "completed",
                "message": "Task completed successfully",
                "result": task_result.result
            }
        else:  # FAILURE
            return {
                "task_id": task_id,
                "status": "failed",
                "message": "Task failed",
                "error": str(task_result.info)
            }
            
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for API integration service"""
    return {
        "status": "healthy",
        "service": "api-integration",
        "message": "API integration service is running"
    }


# Configuration endpoint
@router.get("/config")
async def get_config():
    """Get current API integration configuration"""
    return {
        "default_endpoint": "/sections/for-mapping/",
        "max_sections_limit": 20,
        "min_text_length": 50,
        "api_base_url": getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://writing-api.sagewrite.com'),
        "has_token": bool(getattr(settings, 'EXTERNAL_API_TOKEN', '')),
        "timeout_seconds": 30
    }

