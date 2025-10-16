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
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate text content"""
        if len(v.strip()) == 0:
            raise ValueError('Section text cannot be empty')
        if len(v) > 100000:  # 100KB limit per section
            raise ValueError('Section text too long (max 100KB)')
        return v.strip()


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