"""
Document service for managing documents
"""

from typing import List, Optional
from fastapi import UploadFile
from datetime import datetime
import uuid
import os

from app.database.models import DocumentCollection
from app.models import Document, DocumentStatus


class DocumentService:
    """Service for document operations"""
    
    async def create_document(self, file: UploadFile) -> Document:
        """Create a new document from uploaded file"""
        # Extract title from filename
        title = file.filename or "Untitled Document"
        if title.endswith(('.pdf', '.txt', '.docx')):
            title = title.rsplit('.', 1)[0]  # Remove extension
        
        # Create document model
        document = Document(
            title=title,
            status=DocumentStatus.UPLOADED
        )
        
        # Insert document using our collection
        doc_id = await DocumentCollection.insert_document(document)
        
        # Retrieve and return the created document
        return await DocumentCollection.get_document(doc_id)
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return await DocumentCollection.get_document(document_id)
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """List documents with pagination"""
        return await DocumentCollection.get_documents(skip=skip, limit=limit)
    
    async def update_document_status(
        self, 
        document_id: str, 
        status: DocumentStatus
    ) -> bool:
        """Update document status"""
        return await DocumentCollection.update_document_status(document_id, status)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        return await DocumentCollection.delete_document(document_id)

