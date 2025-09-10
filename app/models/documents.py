"""
Document models for GraphRAG system
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Document types"""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    UNKNOWN = "unknown"


class DocumentBase(BaseModel):
    """Base document model with common fields"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    doi: Optional[str] = Field(None, max_length=100, description="Digital Object Identifier")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Publication year")
    abstract: Optional[str] = Field(None, max_length=10000, description="Document abstract")
    authors: Optional[List[str]] = Field(default_factory=list, description="List of authors")
    journal: Optional[str] = Field(None, max_length=200, description="Journal or publication name")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Document keywords")
    language: str = Field(default="en", max_length=10, description="Document language")
    
    @field_validator('doi')
    @classmethod
    def validate_doi(cls, v):
        """Validate DOI format"""
        if v is not None:
            # Basic DOI validation - should start with 10.
            if not v.startswith('10.'):
                raise ValueError('DOI must start with "10."')
        return v
    
    @field_validator('authors')
    @classmethod
    def validate_authors(cls, v):
        """Validate authors list"""
        if v is not None:
            # Remove empty strings and limit number of authors
            v = [author.strip() for author in v if author.strip()]
            if len(v) > 50:  # Reasonable limit
                raise ValueError('Too many authors (max 50)')
        return v


class DocumentCreate(DocumentBase):
    """Document creation model"""
    file_path: Optional[str] = Field(None, description="Path to uploaded file")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_type: Optional[DocumentType] = Field(None, description="File type")
    
    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v):
        """Validate file size (max 50MB)"""
        if v is not None and v > 50 * 1024 * 1024:  # 50MB
            raise ValueError('File size too large (max 50MB)')
        return v


class DocumentUpdate(BaseModel):
    """Document update model - only updatable fields"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    doi: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    abstract: Optional[str] = Field(None, max_length=10000)
    authors: Optional[List[str]] = None
    journal: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = None
    language: Optional[str] = Field(None, max_length=10)
    status: Optional[DocumentStatus] = None
    
    @field_validator('doi')
    @classmethod
    def validate_doi(cls, v):
        """Validate DOI format"""
        if v is not None:
            if not v.startswith('10.'):
                raise ValueError('DOI must start with "10."')
        return v


class DocumentResponse(DocumentBase):
    """Document response model with additional fields"""
    id: str = Field(..., alias="_id", description="Document ID")
    status: DocumentStatus = Field(..., description="Processing status")
    file_path: Optional[str] = Field(None, description="Path to uploaded file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[DocumentType] = Field(None, description="File type")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of documents per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class DocumentStats(BaseModel):
    """Document statistics model"""
    total_documents: int = Field(..., description="Total number of documents")
    processed_documents: int = Field(..., description="Number of processed documents")
    processing_documents: int = Field(..., description="Number of documents being processed")
    failed_documents: int = Field(..., description="Number of failed documents")
    uploaded_documents: int = Field(..., description="Number of uploaded documents")
    total_size: int = Field(..., description="Total size of all documents in bytes")
    average_size: float = Field(..., description="Average document size in bytes")
    documents_by_type: Dict[str, int] = Field(..., description="Count of documents by type")
    documents_by_year: Dict[int, int] = Field(..., description="Count of documents by year")
