"""
Section models for document parts
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class Section(BaseModel):
    """Section model matching requirements JSON schema"""
    document_id: str = Field(..., description="ID of the parent document")
    title: str = Field(..., description="Section name like 'abstract', 'methods'")
    text: str = Field(..., min_length=1, description="Section content")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of section content")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="From parent document")


class SectionEmbeddingRequest(BaseModel):
    """Section model for embedding generation requests"""
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    section_id: str = Field(..., description="Unique identifier for the section")
    document_id: str = Field(..., description="ID of the parent document")
    title: str = Field(..., description="Section title")
    text: str = Field(default="", description="Section content")
    position: int = Field(..., description="Order of section in document")
    text_updated_at: Optional[datetime] = None
    user_id: str = Field(..., description="ID of user who owns the section")
    embeddings: List[float] = Field(default_factory=list, description="Vector embeddings array")
    meta: Optional[dict] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate text content - allow empty text for embedding generation requests"""
        if v is None:
            return ""
        if len(v) > 100000:  # 100KB limit per section
            raise ValueError('Section text too long (max 100KB)')
        return v.strip() if v else ""


class SectionResponse(Section):
    """Section response model with additional fields"""
    id: str = Field(..., alias="_id", description="Section ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )