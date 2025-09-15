"""
Section extraction service for document text
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SectionExtractor:
    """Service for extracting sections from document text"""

    # Common section patterns
    SECTION_PATTERNS = {
        'abstract': [
            r'abstract\s*:?\s*\n',
            r'abstract\s*:?\s*$',
            r'^\s*abstract\s*$',
        ],
        'introduction': [
            r'introduction\s*:?\s*\n',
            r'introduction\s*:?\s*$',
            r'^\s*introduction\s*$',
        ],
        'methods': [
            r'methods?\s*:?\s*\n',
            r'methods?\s*:?\s*$',
            r'methodology\s*:?\s*\n',
            r'^\s*methods?\s*$',
            r'^\s*methodology\s*$',
        ],
        'results': [
            r'results?\s*:?\s*\n',
            r'results?\s*:?\s*$',
            r'^\s*results?\s*$',
        ],
        'discussion': [
            r'discussion\s*:?\s*\n',
            r'discussion\s*:?\s*$',
            r'^\s*discussion\s*$',
        ],
        'conclusion': [
            r'conclusions?\s*:?\s*\n',
            r'conclusions?\s*:?\s*$',
            r'^\s*conclusions?\s*$',
        ],
        'references': [
            r'references?\s*:?\s*\n',
            r'references?\s*:?\s*$',
            r'^\s*references?\s*$',
            r'bibliography\s*:?\s*\n',
            r'^\s*bibliography\s*$',
        ],
    }

    @staticmethod
    def extract_sections(content: str, document_id: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract sections from document content
        
        Args:
            content: Document text content
            document_id: Document ID for reference
            year: Publication year for sections
            
        Returns:
            List of section dictionaries
        """
        try:
            sections = []
            
            # Clean content
            cleaned_content = SectionExtractor._clean_content(content)
            
            # Find section boundaries
            section_boundaries = SectionExtractor._find_section_boundaries(cleaned_content)
            
            # Extract sections
            for i, (start, end, section_type) in enumerate(section_boundaries):
                section_text = cleaned_content[start:end].strip()
                
                if len(section_text) > 50:  # Minimum section length
                    section = {
                        "document_id": document_id,
                        "title": section_type,
                        "text": section_text,
                        "year": year,
                        "order": i,
                    }
                    sections.append(section)
            
            # If no sections found, create a single section
            if not sections:
                section = {
                    "document_id": document_id,
                    "title": "content",
                    "text": cleaned_content,
                    "year": year,
                    "order": 0,
                }
                sections.append(section)
            
            logger.info(f"Extracted {len(sections)} sections from document {document_id}")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            # Return single section with all content
            return [{
                "document_id": document_id,
                "title": "content",
                "text": content,
                "year": year,
                "order": 0,
            }]

    @staticmethod
    def _clean_content(content: str) -> str:
        """Clean document content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove page numbers and headers/footers
        content = re.sub(r'^\s*\d+\s*$', '', content, flags=re.MULTILINE)
        
        # Clean up line breaks
        content = re.sub(r'\r\n', '\n', content)
        content = re.sub(r'\r', '\n', content)
        
        return content.strip()

    @staticmethod
    def _find_section_boundaries(content: str) -> List[tuple]:
        """Find section boundaries in content"""
        boundaries = []
        
        # Find all section headers
        for section_type, patterns in SectionExtractor.SECTION_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                    start = match.start()
                    boundaries.append((start, section_type))
        
        # Sort by position
        boundaries.sort(key=lambda x: x[0])
        
        # Create section ranges
        section_ranges = []
        for i, (start, section_type) in enumerate(boundaries):
            # Find end position (next section or end of content)
            if i + 1 < len(boundaries):
                end = boundaries[i + 1][0]
            else:
                end = len(content)
            
            section_ranges.append((start, end, section_type))
        
        return section_ranges

    @staticmethod
    def split_into_chunks(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks
        
        Args:
            content: Text content to split
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings within the last 100 characters
                search_start = max(start, end - 100)
                sentence_end = content.rfind('.', search_start, end)
                
                if sentence_end > search_start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = content.rfind(' ', search_start, end)
                    if word_end > search_start:
                        end = word_end
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(content):
                break
        
        return chunks
