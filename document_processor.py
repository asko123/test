"""
Document Processing Module
Handles document upload and management
"""

from goldmansachs.awm_genai import DocUtils
from typing import List, Dict, Any
import os
from pathlib import Path


class DocumentProcessor:
    """Handles document upload and management."""
    
    def __init__(self, app_id: str, env: str):
        """
        Initialize Document Processor.
        
        Args:
            app_id: Application ID
            env: Environment (uat or prod)
        """
        self.app_id = app_id
        self.env = env
        self.doc_utils = DocUtils(app_id=app_id, env=env)
        
    def upload_documents(self, file_paths: List[str]) -> List[Any]:
        """
        Upload multiple documents.
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            List of uploaded document objects
        """
        if not file_paths:
            raise ValueError("No file paths provided")
        
        # Validate files exist
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
        
        # Upload documents
        documents = self.doc_utils.upload(file_paths=file_paths)
        
        return documents
    
    def get_document_info(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Get information about documents.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of dictionaries with document information
        """
        info = []
        
        for file_path in file_paths:
            path = Path(file_path)
            info.append({
                "name": path.name,
                "path": str(path.absolute()),
                "size": path.stat().st_size if path.exists() else 0,
                "extension": path.suffix
            })
        
        return info

