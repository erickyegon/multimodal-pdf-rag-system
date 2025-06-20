import os
import asyncio
from typing import List, Dict, Any, Tuple
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdfplumber import PDF
import camelot
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class MultimodalPDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tesseract_path = 'tesseract'  # Default path, will be updated by _check_tesseract_available
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to process PDF and extract all content types"""
        try:
            logger.info(f"Starting PDF processing: {pdf_path}")
            
            # Extract different content types
            text_content = await self._extract_text_content(pdf_path)
            table_content = await self._extract_tables(pdf_path)
            image_content = await self._extract_images(pdf_path)
            
            # Process and chunk content
            processed_content = {
                "text_chunks": self._chunk_text_content(text_content),
                "tables": table_content,
                "images": image_content,
                "metadata": await self._extract_metadata(pdf_path)
            }
            
            logger.info(f"PDF processing completed. Text chunks: {len(processed_content['text_chunks'])}, Tables: {len(table_content)}, Images: {len(image_content)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    async def _extract_text_content(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text content from PDF"""
        text_content = []
        
        # Use PyMuPDF for text extraction
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text
            text = page.get_text()
            
            if text.strip():
                text_content.append({
                    "content": text,
                    "page_number": page_num + 1,
                    "content_type": "text",
                    "bbox": None
                })
        
        doc.close()
        return text_content
    
    async def _extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF using multiple methods"""
        tables = []
        
        try:
            # Method 1: Camelot for lattice and stream detection
            camelot_tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            
            for i, table in enumerate(camelot_tables):
                if table.df is not None and not table.df.empty:
                    # Fix duplicate columns
                    df = self._fix_duplicate_columns(table.df)

                    tables.append({
                        "content": df.to_dict('records'),
                        "raw_df": df,
                        "page_number": table.page,
                        "content_type": "table",
                        "extraction_method": "camelot_lattice",
                        "table_id": f"table_{i}",
                        "confidence": table.accuracy if hasattr(table, 'accuracy') else None
                    })
            
            # Method 2: Try stream flavor for tables without clear borders
            stream_tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            
            for i, table in enumerate(stream_tables):
                if table.df is not None and not table.df.empty:
                    # Fix duplicate columns
                    df = self._fix_duplicate_columns(table.df)

                    tables.append({
                        "content": df.to_dict('records'),
                        "raw_df": df,
                        "page_number": table.page,
                        "content_type": "table",
                        "extraction_method": "camelot_stream",
                        "table_id": f"stream_table_{i}",
                        "confidence": table.accuracy if hasattr(table, 'accuracy') else None
                    })
        
        except Exception as e:
            logger.warning(f"Camelot table extraction failed: {str(e)}")
        
        # Method 3: pdfplumber as fallback
        try:
            with PDF.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for i, table in enumerate(page_tables):
                        if table:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            # Fix duplicate columns
                            df = self._fix_duplicate_columns(df)

                            tables.append({
                                "content": df.to_dict('records'),
                                "raw_df": df,
                                "page_number": page_num + 1,
                                "content_type": "table",
                                "extraction_method": "pdfplumber",
                                "table_id": f"pdfplumber_table_{page_num}_{i}"
                            })
        
        except Exception as e:
            logger.warning(f"pdfplumber table extraction failed: {str(e)}")
        
        return tables
    
    async def _extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF with graceful OCR fallback"""
        images = []

        # Check if tesseract is available
        tesseract_available = self._check_tesseract_available()

        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        
                        # Convert to base64 for storage
                        img_base64 = base64.b64encode(img_data).decode()

                        # Try OCR if available, otherwise use placeholder
                        if tesseract_available:
                            try:
                                img_pil = Image.open(BytesIO(img_data))
                                # Configure pytesseract to use the correct path
                                if hasattr(self, 'tesseract_path') and self.tesseract_path != 'tesseract':
                                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
                                ocr_text = pytesseract.image_to_string(img_pil)
                            except Exception as e:
                                logger.warning(f"OCR failed for image {img_index} on page {page_num}: {str(e)}")
                                ocr_text = "[OCR not available]"
                        else:
                            ocr_text = "[OCR not available - Tesseract not installed]"
                        
                        images.append({
                            "content": img_base64,
                            "ocr_text": ocr_text,
                            "page_number": page_num + 1,
                            "content_type": "image",
                            "image_id": f"img_{page_num}_{img_index}",
                            "size": (pix.width, pix.height)
                        })
                    
                    pix = None
                
                except Exception as e:
                    logger.warning(f"Error extracting image {img_index} from page {page_num}: {str(e)}")
        
        doc.close()
        return images
    
    async def _extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(doc),
            "file_size": os.path.getsize(pdf_path)
        }
    
    def _chunk_text_content(self, text_content: List[Dict[str, Any]]) -> List[Document]:
        """Chunk text content for vector storage"""
        documents = []
        
        for content in text_content:
            if content["content"].strip():
                chunks = self.text_splitter.split_text(content["content"])
                
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "page_number": content["page_number"],
                            "content_type": content["content_type"],
                            "chunk_index": i,
                            "source": "pdf_text"
                        }
                    )
                    documents.append(doc)
        
        return documents

    def _fix_duplicate_columns(self, df) -> pd.DataFrame:
        """Fix duplicate column names in DataFrame"""
        # Get column names
        cols = df.columns.tolist()

        # Track seen column names and their counts
        seen = {}
        new_cols = []

        for col in cols:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)

        # Create new DataFrame with fixed column names
        df.columns = new_cols

        return df

    def _check_tesseract_available(self) -> bool:
        """Check if tesseract is available"""
        try:
            import subprocess

            # Common Tesseract paths on different systems
            tesseract_paths = [
                'tesseract',  # If in PATH
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows default
                '/usr/bin/tesseract',  # Linux
                '/usr/local/bin/tesseract',  # macOS/Linux
                '/opt/homebrew/bin/tesseract'  # macOS with Homebrew
            ]

            for tesseract_path in tesseract_paths:
                try:
                    result = subprocess.run([tesseract_path, '--version'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Store the working path for later use
                        self.tesseract_path = tesseract_path
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    continue

            return False
        except Exception:
            return False