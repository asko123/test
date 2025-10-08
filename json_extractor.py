"""
JSON/JSONL File Extraction Module
Handles extraction and formatting of JSON and JSONL files
"""

import json
from typing import List, Dict


class JSONExtractor:
    """Extract and format JSON/JSONL files for LLM context."""
    
    def extract_from_json_file(self, file_path: str, filename: str = None) -> str:
        """
        Extract and format JSON file content.
        
        Args:
            file_path: Path to JSON file
            filename: Display name for the file
            
        Returns:
            Formatted JSON content
        """
        if filename is None:
            filename = file_path
        
        content_parts = [f"\n\n{'='*80}\nDocument: {filename}\n{'='*80}\n"]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of JSON objects
                content_parts.append("\nThis file contains a list of JSON objects:\n")
                for idx, obj in enumerate(data, 1):
                    formatted = self._format_json_object(obj, idx, filename)
                    content_parts.append(f"\n{formatted}\n")
            elif isinstance(data, dict):
                # Single JSON object
                formatted = self._format_json_object(data, 1, filename)
                content_parts.append(f"\n{formatted}\n")
            else:
                content_parts.append(f"\nJSON Value: {data}\n")
                
        except Exception as e:
            content_parts.append(f"\n[ERROR] Failed to parse JSON: {str(e)}\n")
        
        return "\n".join(content_parts)
    
    def extract_from_jsonl_file(self, file_path: str, filename: str = None) -> str:
        """
        Extract and format JSONL file content (one JSON per line).
        
        Args:
            file_path: Path to JSONL file
            filename: Display name for the file
            
        Returns:
            Formatted JSONL content
        """
        if filename is None:
            filename = file_path
        
        content_parts = [f"\n\n{'='*80}\nDocument: {filename}\n{'='*80}\n"]
        content_parts.append("\nThis file contains multiple JSON objects (one per line):\n")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            formatted = self._format_json_object(obj, idx, filename)
                            content_parts.append(f"\n{formatted}\n")
                        except json.JSONDecodeError:
                            content_parts.append(f"\n[Line {idx}] Invalid JSON: {line[:100]}...\n")
                            
        except Exception as e:
            content_parts.append(f"\n[ERROR] Failed to parse JSONL: {str(e)}\n")
        
        return "\n".join(content_parts)
    
    def _format_json_object(self, json_obj: Dict, obj_idx: int, filename: str) -> str:
        """
        Format a JSON object for LLM understanding.
        
        Args:
            json_obj: Parsed JSON object
            obj_idx: Index of this object
            filename: Source filename
            
        Returns:
            Formatted JSON string
        """
        json_parts = []
        json_parts.append(f"--- JSON OBJECT {obj_idx} (Document: {filename}) ---")
        
        # Add formatted key-value pairs
        json_parts.append("\nStructured Data Fields:")
        for key, value in json_obj.items():
            # Clean up the value for better readability
            if isinstance(value, str):
                # Remove extra whitespace and truncate if very long
                value = ' '.join(value.split())
                if len(value) > 500:
                    value = value[:500] + "..."
            json_parts.append(f"  {key}: {value}")
        
        # Add JSON format for reference (compact for readability)
        json_parts.append("\nJSON Format:")
        json_parts.append(json.dumps(json_obj, indent=2))
        
        json_parts.append(f"--- END JSON OBJECT {obj_idx} ---\n")
        
        return "\n".join(json_parts)

