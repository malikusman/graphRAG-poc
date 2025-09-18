"""
File parsing service for PDF and DOCX documents
"""

import io
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile
import fitz  # PyMuPDF
from docx import Document as DocxDocument
# import magic
# import chardet

logger = logging.getLogger(__name__)


class FileParser:
    """Service for parsing uploaded files"""

    @staticmethod
    async def parse_file(file: UploadFile) -> Dict[str, Any]:
        """
        Parse uploaded file and extract text content
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dict containing parsed content and metadata
        """
        try:
            logger.info(f"Starting file parsing for: {file.filename}")
            
            # Read file content
            content = await file.read()
            logger.info(f"Read {len(content)} bytes from file")
            
            # Detect file type
            file_type = FileParser._detect_file_type(content, file.filename)
            logger.info(f"Detected file type: {file_type}")
            
            # Parse based on file type
            if file_type == "pdf":
                result = await FileParser._parse_pdf(content)
            elif file_type == "docx":
                result = await FileParser._parse_docx(content)
            elif file_type == "txt":
                result = await FileParser._parse_txt(content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            logger.info(f"File parsing successful. Content length: {len(result['content'])}")
            return result
                
        except Exception as e:
            logger.error(f"Error parsing file {file.filename}: {str(e)}")
            raise ValueError(f"Failed to parse file: {str(e)}")

    @staticmethod
    def _detect_file_type(content: bytes, filename: Optional[str]) -> str:
        """Detect file type from content and filename"""
        # First try magic detection (disabled for now)
        # try:
        #     mime_type = magic.from_buffer(content, mime=True)
        #     if mime_type == "application/pdf":
        #         return "pdf"
        #     elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
        #                       "application/msword"]:
        #         return "docx"
        #     elif mime_type.startswith("text/"):
        #         return "txt"
        # except Exception:
        #     pass
        
        # Fallback to filename extension
        if filename:
            ext = filename.lower().split('.')[-1]
            if ext == "pdf":
                return "pdf"
            elif ext in ["docx", "doc"]:
                return "docx"
            elif ext == "txt":
                return "txt"
        
        raise ValueError("Unable to determine file type")

    @staticmethod
    async def _parse_pdf(content: bytes) -> Dict[str, Any]:
        """Parse PDF file"""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_content = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc[page_num]
                text_content += page.get_text()
            
            doc.close()
            
            return {
                "content": text_content,
                "page_count": page_count,
                "file_type": "pdf",
                "metadata": {
                    "total_pages": page_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    async def _parse_docx(content: bytes) -> Dict[str, Any]:
        """Parse DOCX file"""
        try:
            doc = DocxDocument(io.BytesIO(content))
            text_content = ""
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text_content += cell.text + " "
                    text_content += "\n"
            
            return {
                "content": text_content,
                "file_type": "docx",
                "metadata": {
                    "paragraph_count": len(doc.paragraphs),
                    "table_count": len(doc.tables)
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    @staticmethod
    async def _parse_txt(content: bytes) -> Dict[str, Any]:
        """Parse TXT file"""
        try:
            # Detect encoding (simplified for now)
            # detected = chardet.detect(content)
            # encoding = detected.get('encoding', 'utf-8')
            encoding = 'utf-8'
            
            # Decode content
            text_content = content.decode(encoding)
            
            return {
                "content": text_content,
                "file_type": "txt",
                "metadata": {
                    "encoding": encoding,
                    "confidence": 1.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing TXT: {str(e)}")
            raise ValueError(f"Failed to parse TXT: {str(e)}")
