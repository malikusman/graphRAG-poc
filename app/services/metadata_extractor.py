"""
Metadata extraction service for documents
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Service for extracting metadata from documents"""

    # DOI regex pattern
    DOI_PATTERN = re.compile(r'10\.\d+/[^\s]+', re.IGNORECASE)
    
    # Year patterns
    YEAR_PATTERNS = [
        r'\b(19|20)\d{2}\b',  # 1900-2099
        r'\((\d{4})\)',       # (2023)
        r'\[(\d{4})\]',       # [2023]
    ]

    @staticmethod
    def extract_metadata(content: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract metadata from document content and filename
        
        Args:
            content: Document text content
            filename: Original filename
            
        Returns:
            Dict containing extracted metadata
        """
        try:
            metadata = {
                "title": MetadataExtractor._extract_title(content, filename),
                "doi": MetadataExtractor._extract_doi(content),
                "year": MetadataExtractor._extract_year(content),
            }
            
            logger.info(f"Extracted metadata: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {
                "title": filename or "Untitled Document",
                "doi": None,
                "year": None,
            }

    @staticmethod
    def _extract_title(content: str, filename: Optional[str] = None) -> str:
        """Extract document title"""
        # Try to find title in content first
        title_patterns = [
            r'^(.+?)(?:\n|$)',  # First line
            r'Title:\s*(.+?)(?:\n|$)',  # Title: pattern
            r'#\s*(.+?)(?:\n|$)',  # Markdown header
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content.strip(), re.MULTILINE | re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 10 and len(title) < 200:  # Reasonable title length
                    return title
        
        # Fallback to filename
        if filename:
            # Remove extension
            title = filename.rsplit('.', 1)[0] if '.' in filename else filename
            return title
        
        return "Untitled Document"

    @staticmethod
    def _extract_doi(content: str) -> Optional[str]:
        """Extract DOI from content"""
        # Look for DOI patterns
        doi_matches = MetadataExtractor.DOI_PATTERN.findall(content)
        
        if doi_matches:
            # Return the first valid DOI
            for doi in doi_matches:
                if MetadataExtractor._validate_doi(doi):
                    return doi
        
        return None

    @staticmethod
    def _extract_year(content: str) -> Optional[int]:
        """Extract publication year from content"""
        years = []
        
        # Search for year patterns
        for pattern in MetadataExtractor.YEAR_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    year = int(match) if isinstance(match, str) else int(match)
                    if 1900 <= year <= datetime.now().year + 1:
                        years.append(year)
                except ValueError:
                    continue
        
        if years:
            # Return the most recent year (likely publication year)
            return max(years)
        
        return None

    @staticmethod
    def _validate_doi(doi: str) -> bool:
        """Validate DOI format"""
        if not doi:
            return False
        
        # Basic DOI validation
        if not doi.startswith('10.'):
            return False
        
        # Check for valid DOI structure
        parts = doi.split('/')
        if len(parts) != 2:
            return False
        
        # Check prefix and suffix are not empty
        if not parts[0] or not parts[1]:
            return False
        
        return True
