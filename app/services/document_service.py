"""
Document service for managing documents
"""

from typing import List, Optional
from fastapi import UploadFile
from datetime import datetime
import uuid
import os

from database.connection import AsyncIOMotorDatabase
from database.models import DocumentCreate, DocumentResponse, DocumentStatus


class DocumentService:
    """Service for document operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.documents
    
    async def create_document(self, file: UploadFile) -> DocumentResponse:
        """Create a new document from uploaded file"""
        # Generate document ID
        doc_id = str(uuid.uuid4())
        
        # Create document record
        document_data = {
            "_id": doc_id,
            "title": file.filename or "Untitled Document",
            "status": DocumentStatus.UPLOADED,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "file_size": file.size if hasattr(file, 'size') else 0
        }
        
        # Insert document
        result = await self.collection.insert_one(document_data)
        
        # Return document response
        return DocumentResponse(**document_data)
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """Get a document by ID"""
        document = await self.collection.find_one({"_id": document_id})
        if document:
            return DocumentResponse(**document)
        return None
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DocumentResponse]:
        """List documents with pagination"""
        cursor = self.collection.find().skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            documents.append(DocumentResponse(**doc))
        return documents
    
    async def update_document(
        self, 
        document_id: str, 
        update_data: dict
    ) -> Optional[DocumentResponse]:
        """Update a document"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": document_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return await self.get_document(document_id)
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        result = await self.collection.delete_one({"_id": document_id})
        return result.deleted_count > 0

