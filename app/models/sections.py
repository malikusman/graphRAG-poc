"""
Section models for document parts
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SectionType(str, Enum):
    """Section types in scientific documents"""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    FIGURES = "figures"
    TABLES = "tables"
    APPENDIX = "appendix"
    ACKNOWLEDGMENTS = "acknowledgments"
    AUTHOR_INFO = "author_info"
    TITLE = "title"
    OTHER = "other"


class SectionBase(BaseModel):
    """Base section model"""
    document_id: str = Field(..., description="ID of the parent document")
    section_type: SectionType = Field(..., description="Type of section")
    title: Optional[str] = Field(None, max_length=500, description="Section title")
    content: str = Field(..., min_length=1, description="Section content")
    order: int = Field(..., ge=0, description="Order of section in document")
    page_number: Optional[int] = Field(None, ge=1, description="Page number where section starts")
    word_count: Optional[int] = Field(None, ge=0, description="Number of words in section")
    char_count: Optional[int] = Field(None, ge=0, description="Number of characters in section")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content length"""
        if len(v.strip()) == 0:
            raise ValueError('Section content cannot be empty')
        if len(v) > 100000:  # 100KB limit per section
            raise ValueError('Section content too long (max 100KB)')
        return v.strip()
    
    @model_validator(mode='after')
    def calculate_counts(self):
        """Calculate word and character counts if not provided"""
        if self.word_count is None and self.content:
            self.word_count = len(self.content.split())
        if self.char_count is None and self.content:
            self.char_count = len(self.content)
        return self


class SectionCreate(SectionBase):
    """Section creation model"""
    pass


class SectionUpdate(BaseModel):
    """Section update model"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    order: Optional[int] = Field(None, ge=0)
    page_number: Optional[int] = Field(None, ge=1)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content length"""
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError('Section content cannot be empty')
            if len(v) > 100000:
                raise ValueError('Section content too long (max 100KB)')
            return v.strip()
        return v


class SectionResponse(SectionBase):
    """Section response model with additional fields"""
    id: str = Field(..., alias="_id", description="Section ID")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of section content")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class SectionListResponse(BaseModel):
    """Response model for section listing"""
    sections: List[SectionResponse] = Field(..., description="List of sections")
    total: int = Field(..., description="Total number of sections")
    document_id: str = Field(..., description="Parent document ID")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of sections per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class SectionStats(BaseModel):
    """Section statistics model"""
    total_sections: int = Field(..., description="Total number of sections")
    sections_by_type: Dict[str, int] = Field(..., description="Count of sections by type")
    average_word_count: float = Field(..., description="Average word count per section")
    average_char_count: float = Field(..., description="Average character count per section")
    total_words: int = Field(..., description="Total words across all sections")
    total_chars: int = Field(..., description="Total characters across all sections")
    sections_with_embeddings: int = Field(..., description="Number of sections with embeddings")


class SectionSearchRequest(BaseModel):
    """Request model for section search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    document_id: Optional[str] = Field(None, description="Filter by document ID")
    section_types: Optional[List[SectionType]] = Field(None, description="Filter by section types")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    include_content: bool = Field(default=True, description="Whether to include full content in results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class SectionSearchResult(BaseModel):
    """Search result model for sections"""
    section: SectionResponse = Field(..., description="Section information")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    matched_content: Optional[str] = Field(None, description="Highlighted matched content")
    context_before: Optional[str] = Field(None, description="Context before match")
    context_after: Optional[str] = Field(None, description="Context after match")
