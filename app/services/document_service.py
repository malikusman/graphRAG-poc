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
from app.tasks.processing_tasks import process_document
from app.services.file_parser import FileParser
from app.services.metadata_extractor import MetadataExtractor
from app.services.section_extractor import SectionExtractor


class DocumentService:
    """Service for document operations"""
    
    async def create_document(self, file: UploadFile) -> Document:
        """Create a new document from uploaded file and trigger background processing"""
        try:
            # Parse the uploaded file
            parsed_content = await FileParser.parse_file(file)
            
            # Extract metadata from content
            metadata = MetadataExtractor.extract_metadata(
                parsed_content["content"], 
                file.filename
            )
            
            # Create document model with extracted metadata
            document = Document(
                title=metadata["title"],
                doi=metadata["doi"],
                year=metadata["year"],
                status=DocumentStatus.UPLOADED
            )
            
            # Insert document using our collection
            doc_id = await DocumentCollection.insert_document(document)
            
            # Extract sections from content
            sections = SectionExtractor.extract_sections(
                parsed_content["content"],
                doc_id,
                metadata["year"]
            )
            
            # Store sections in database
            from app.database.models import SectionCollection
            for section in sections:
                await SectionCollection.insert_section(section)
            
            # Trigger background processing for embeddings and entity extraction
            job = process_document.delay(doc_id)
            
            # Update document with job_id
            await DocumentCollection.update_document_job_id(doc_id, job.id)
            
            # Retrieve and return the created document
            return await DocumentCollection.get_document(doc_id)
            
        except Exception as e:
            # Fallback to basic document creation if parsing fails
            title = file.filename or "Untitled Document"
            if title.endswith(('.pdf', '.txt', '.docx')):
                title = title.rsplit('.', 1)[0]  # Remove extension
            
            document = Document(
                title=title,
                status=DocumentStatus.UPLOADED
            )
            
            doc_id = await DocumentCollection.insert_document(document)
            job = process_document.delay(doc_id)
            await DocumentCollection.update_document_job_id(doc_id, job.id)
            
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

