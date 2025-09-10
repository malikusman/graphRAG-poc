"""
Document models for GraphRAG system
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(BaseModel):
    """Document model - minimal as per requirements"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    doi: Optional[str] = Field(None, max_length=100, description="Digital Object Identifier")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Publication year")
    status: DocumentStatus = Field(..., description="Processing status")
    
    @field_validator('doi')
    @classmethod
    def validate_doi(cls, v):
        """Validate DOI format"""
        if v is not None:
            # Basic DOI validation - should start with 10.
            if not v.startswith('10.'):
                raise ValueError('DOI must start with "10."')
        return v


class DocumentResponse(Document):
    """Document response model with additional fields"""
    id: str = Field(..., alias="_id", description="Document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )