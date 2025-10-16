"""
API Data Adapter for external API integration with GraphRAG pipeline
"""

import logging
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class APISection(BaseModel):
    """Model for API section data"""
    section_id: str
    document_id: str
    title: str
    text: Optional[str] = ""  # Allow None/empty text
    position: int
    created_at: Optional[str] = ""
    updated_at: Optional[str] = ""
    deleted_at: Optional[str] = None
    text_updated_at: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class APIDataAdapter:
    """Service for fetching and transforming API data for GraphRAG pipeline"""
    
    def __init__(self, api_base_url: str = None, api_token: str = None):
        self.api_base_url = api_base_url or getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://writing-api.sagewrite.com')
        self.api_token = api_token or getattr(settings, 'EXTERNAL_API_TOKEN', '')
        self.max_sections_to_process = 5  # Process only first 5 sections
        self.min_text_length = 50  # Minimum text length to consider valid
        
    async def fetch_sections_from_api(self, endpoint: str = "/sections/for-mapping/") -> List[APISection]:
        """Fetch sections from external API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}{endpoint}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched {len(data)} sections from API")
                        return [APISection(**section_data) for section_data in data]
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching sections from API: {str(e)}")
            return []
    
    def filter_valid_sections(self, sections: List[APISection]) -> List[APISection]:
        """Filter sections to keep only those with meaningful text content"""
        valid_sections = []
        
        for section in sections:
            # Skip if text is empty or too short
            if not section.text or len(section.text.strip()) < self.min_text_length:
                logger.debug(f"Skipping section {section.section_id} - text too short or empty")
                continue
                
            # Skip if marked as deleted
            if section.deleted_at:
                logger.debug(f"Skipping section {section.section_id} - marked as deleted")
                continue
                
            valid_sections.append(section)
            
        logger.info(f"Filtered {len(sections)} sections to {len(valid_sections)} valid sections")
        return valid_sections
    
    def limit_sections(self, sections: List[APISection]) -> List[APISection]:
        """Limit to first N sections for processing"""
        limited_sections = sections[:self.max_sections_to_process]
        logger.info(f"Limited processing to first {len(limited_sections)} sections")
        return limited_sections
    
    def extract_year_from_timestamp(self, timestamp_str: str) -> int:
        """Extract year from timestamp string"""
        try:
            # Parse timestamp and extract year
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.year
        except Exception as e:
            logger.warning(f"Could not extract year from timestamp {timestamp_str}: {str(e)}")
            return datetime.now().year
    
    def transform_to_internal_format(self, api_sections: List[APISection]) -> List[Dict[str, Any]]:
        """Transform API sections to internal GraphRAG pipeline format"""
        internal_sections = []
        
        for api_section in api_sections:
            # Extract year from created_at timestamp
            year = self.extract_year_from_timestamp(api_section.created_at)
            
            # Transform to internal format
            internal_section = {
                "_id": api_section.section_id,  # Use section_id as _id
                "document_id": api_section.document_id,
                "title": api_section.title,
                "text": api_section.text.strip(),
                "position": api_section.position,
                "year": year,
                "created_at": api_section.created_at,
                "updated_at": api_section.updated_at,
                "source": "external_api",
                "api_metadata": {
                    "original_section_id": api_section.section_id,
                    "text_updated_at": api_section.text_updated_at,
                    "meta": api_section.meta
                }
            }
            
            internal_sections.append(internal_section)
            
        logger.info(f"Transformed {len(api_sections)} API sections to internal format")
        return internal_sections
    
    async def get_sections_for_graphrag(self, endpoint: str = "/sections/for-mapping/") -> List[Dict[str, Any]]:
        """Main method to fetch and prepare sections for GraphRAG pipeline"""
        try:
            logger.info("Starting API data fetch for GraphRAG pipeline")
            
            # Step 1: Fetch sections from API
            api_sections = await self.fetch_sections_from_api(endpoint)
            if not api_sections:
                logger.warning("No sections fetched from API")
                return []
            
            # Step 2: Filter valid sections
            valid_sections = self.filter_valid_sections(api_sections)
            if not valid_sections:
                logger.warning("No valid sections found after filtering")
                return []
            
            # Step 3: Limit sections for processing
            limited_sections = self.limit_sections(valid_sections)
            
            # Step 4: Transform to internal format
            internal_sections = self.transform_to_internal_format(limited_sections)
            
            logger.info(f"Successfully prepared {len(internal_sections)} sections for GraphRAG pipeline")
            return internal_sections
            
        except Exception as e:
            logger.error(f"Error preparing sections for GraphRAG: {str(e)}")
            return []


# Configuration for external API
class ExternalAPIConfig(BaseModel):
    """Configuration for external API integration"""
    base_url: str = Field(default="https://writing-api.sagewrite.com")
    token: str = Field(default="")
    endpoint: str = Field(default="/sections/for-mapping/")
    max_sections: int = Field(default=5, description="Maximum sections to process")
    min_text_length: int = Field(default=50, description="Minimum text length for valid sections")
    timeout_seconds: int = Field(default=30, description="API request timeout")
    
    class Config:
        env_prefix = "EXTERNAL_API_"
