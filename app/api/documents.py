"""
Document management API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import uuid
from datetime import datetime

from database.connection import get_database
from database.models import DocumentCreate, DocumentResponse
from services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db=Depends(get_database)
):
    """Upload a new document for processing"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF, TXT, and DOCX files are supported"
            )
        
        # Create document service
        doc_service = DocumentService(db)
        
        # Process the uploaded file
        document = await doc_service.create_document(file)
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_database)
):
    """List all documents"""
    try:
        doc_service = DocumentService(db)
        documents = await doc_service.list_documents(skip=skip, limit=limit)
        return documents
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db=Depends(get_database)
):
    """Get a specific document by ID"""
    try:
        doc_service = DocumentService(db)
        document = await doc_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db=Depends(get_database)
):
    """Delete a document"""
    try:
        doc_service = DocumentService(db)
        success = await doc_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

