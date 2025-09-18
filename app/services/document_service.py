"""
Document service for managing documents
"""

from typing import List, Optional
from fastapi import UploadFile
from datetime import datetime
import uuid
import os
import logging

from app.database.models import DocumentCollection
from app.models import Document, DocumentResponse, DocumentStatus
from app.tasks.processing_tasks import process_document
from app.services.file_parser import FileParser
from app.services.metadata_extractor import MetadataExtractor
from app.services.section_extractor import SectionExtractor

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document operations"""
    
    async def create_document(self, file: UploadFile) -> Document:
        """Create a new document from uploaded file and trigger background processing"""
        try:
            logger.info(f"Starting document creation for file: {file.filename}")
            
            # Parse the uploaded file
            logger.info("Parsing uploaded file...")
            parsed_content = await FileParser.parse_file(file)
            logger.info(f"File parsed successfully. Content length: {len(parsed_content['content'])}")
            
            # Extract metadata from content
            logger.info("Extracting metadata...")
            metadata = MetadataExtractor.extract_metadata(
                parsed_content["content"], 
                file.filename
            )
            logger.info(f"Metadata extracted: {metadata}")
            
            # Create document model with extracted metadata
            document = Document(
                title=metadata["title"],
                doi=metadata["doi"],
                year=metadata["year"],
                status=DocumentStatus.UPLOADED
            )
            
            # Insert document using our collection
            logger.info("Inserting document into database...")
            doc_id = await DocumentCollection.insert_document(document)
            logger.info(f"Document inserted with ID: {doc_id}")
            
            # Extract sections from content
            logger.info("Extracting sections...")
            sections = SectionExtractor.extract_sections(
                parsed_content["content"],
                doc_id,
                metadata["year"]
            )
            logger.info(f"Extracted {len(sections)} sections")
            
            # Store sections in database
            logger.info("Storing sections in database...")
            from app.database.models import SectionCollection
            from app.models import Section
            for i, section_dict in enumerate(sections):
                # Convert dictionary to Section model
                section = Section(
                    document_id=section_dict["document_id"],
                    title=section_dict["title"],
                    text=section_dict["text"],
                    year=section_dict["year"],
                    order=section_dict["order"]
                )
                await SectionCollection.insert_section(section)
                logger.info(f"Stored section {i+1}/{len(sections)}: {section.title}")
            
            # Trigger background processing for embeddings and entity extraction
            logger.info("Triggering background processing...")
            job = process_document.delay(doc_id)
            
            # Update document with job_id
            await DocumentCollection.update_document_job_id(doc_id, job.id)
            
            # Retrieve and return the created document
            return await DocumentCollection.get_document(doc_id)
            
        except Exception as e:
            import traceback
            logger.error(f"Error in document creation: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Falling back to basic document creation for file: {file.filename}")
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
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
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

