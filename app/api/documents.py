"""
Document management API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List

from app.models import Document, DocumentStatus
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=Document)
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document for processing"""
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(('.pdf', '.txt', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF, TXT, and DOCX files are supported"
            )
        
        # Create document service
        doc_service = DocumentService()
        
        # Process the uploaded file
        document = await doc_service.create_document(file)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/", response_model=List[Document])
async def list_documents(skip: int = 0, limit: int = 100):
    """List all documents"""
    try:
        doc_service = DocumentService()
        documents = await doc_service.list_documents(skip=skip, limit=limit)
        return documents
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Get a specific document by ID"""
    try:
        doc_service = DocumentService()
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


@router.patch("/{document_id}/status", response_model=Document)
async def update_document_status(document_id: str, status: DocumentStatus):
    """Update document status"""
    try:
        doc_service = DocumentService()
        success = await doc_service.update_document_status(document_id, status)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        # Return updated document
        document = await doc_service.get_document(document_id)
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update document status: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        doc_service = DocumentService()
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

