from typing import List, Dict, Optional
import os
import tempfile
from pathlib import Path

import streamlit as st
import requests
from loguru import logger

from open_notebook.domain.models import Source, Notebook
from open_notebook.exceptions import ProcessingError, InvalidInputError


class ContentProcessor:
    """Handles content processing for various file types and URLs."""
    
    @staticmethod
    def process_url(url: str, notebook_id: str, title: Optional[str] = None) -> Source:
        """Process a URL and create a source."""
        if not url or not url.startswith(('http://', 'https://')):
            raise InvalidInputError("Invalid URL provided")
        
        try:
            # Try to fetch URL content
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'OpenNotebook/1.0'
            })
            response.raise_for_status()
            
            # Create source
            source = Source(
                title=title or url,
                url=url,
                content=response.text[:10000],  # Limit content size
                full_text=response.text,
                metadata={
                    'content_type': response.headers.get('content-type', ''),
                    'status_code': response.status_code,
                    'url': url
                },
                is_processed=True
            )
            
            source.save()
            
            # Add to notebook
            notebook = Notebook.get(notebook_id)
            notebook.add_source(source)
            
            return source
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            raise ProcessingError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            raise ProcessingError(f"Failed to process URL: {str(e)}")
    
    @staticmethod
    def process_file(uploaded_file, notebook_id: str, title: Optional[str] = None) -> Source:
        """Process an uploaded file and create a source."""
        try:
            # Get file info
            filename = uploaded_file.name
            file_title = title or filename
            
            # Read file content
            content = uploaded_file.read()
            
            # Process based on file type
            if filename.lower().endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
                # Text files
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    text_content = content.decode('latin-1')
                
                source = Source(
                    title=file_title,
                    content=text_content[:10000],  # Preview
                    full_text=text_content,
                    metadata={
                        'filename': filename,
                        'file_size': len(content),
                        'file_type': 'text'
                    },
                    has_document=True,
                    is_processed=True
                )
            
            elif filename.lower().endswith(('.pdf', '.doc', '.docx')):
                # Document files - would need additional processing libraries
                source = Source(
                    title=file_title,
                    content=f"Document: {filename}",
                    metadata={
                        'filename': filename,
                        'file_size': len(content),
                        'file_type': 'document'
                    },
                    has_document=True,
                    is_processed=False  # Requires additional processing
                )
            
            else:
                # Other file types
                source = Source(
                    title=file_title,
                    content=f"File: {filename}",
                    metadata={
                        'filename': filename,
                        'file_size': len(content),
                        'file_type': 'binary'
                    },
                    has_document=True,
                    is_processed=False
                )
            
            source.save()
            
            # Add to notebook
            notebook = Notebook.get(notebook_id)
            notebook.add_source(source)
            
            return source
            
        except Exception as e:
            logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
            raise ProcessingError(f"Failed to process file: {str(e)}")
    
    @staticmethod
    def process_text(text: str, notebook_id: str, title: str) -> Source:
        """Process raw text and create a source."""
        if not text.strip():
            raise InvalidInputError("Text content cannot be empty")
        
        try:
            source = Source(
                title=title,
                content=text[:10000],  # Preview
                full_text=text,
                metadata={
                    'content_length': len(text),
                    'content_type': 'text/plain'
                },
                is_processed=True
            )
            
            source.save()
            
            # Add to notebook
            notebook = Notebook.get(notebook_id)
            notebook.add_source(source)
            
            return source
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise ProcessingError(f"Failed to process text: {str(e)}")


class EsperantoProcessor:
    """Handles content processing via Esperanto API."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        from open_notebook.domain.models import Settings
        settings = Settings.load()
        
        self.base_url = base_url or settings.esperanto_base_url
        self.api_key = api_key or settings.esperanto_api_key
        
        if not self.base_url:
            logger.warning("Esperanto base URL not configured")
    
    def is_available(self) -> bool:
        """Check if Esperanto service is available."""
        return bool(self.base_url)
    
    def process_url(self, url: str) -> Dict:
        """Process URL via Esperanto service."""
        if not self.is_available():
            raise ProcessingError("Esperanto service not configured")
        
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.post(
                f"{self.base_url}/process/url",
                json={"url": url},
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Esperanto URL processing failed: {str(e)}")
            raise ProcessingError(f"Failed to process URL via Esperanto: {str(e)}")
    
    def process_file(self, file_path: str) -> Dict:
        """Process file via Esperanto service."""
        if not self.is_available():
            raise ProcessingError("Esperanto service not configured")
        
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/process/file",
                    files=files,
                    headers=headers,
                    timeout=120
                )
                response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Esperanto file processing failed: {str(e)}")
            raise ProcessingError(f"Failed to process file via Esperanto: {str(e)}")


def get_content_processor() -> ContentProcessor:
    """Get the content processor instance."""
    return ContentProcessor()


def get_esperanto_processor() -> EsperantoProcessor:
    """Get the Esperanto processor instance."""
    return EsperantoProcessor()
