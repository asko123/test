"""
PDF Extraction Module
Handles extraction of text, tables, and JSON data from PDF documents using pdfplumber
"""

import pdfplumber
import pandas as pd
from typing import List, Dict, Tuple
import json
import re


class PDFExtractor:
    """Extract text and tables from PDF documents with proper structure preservation."""
    
    def __init__(self):
        self.extracted_content = []
    
    def extract_from_file(self, file_path: str, filename: str = None) -> str:
        """
        Extract text, tables, and JSON data from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            filename: Optional display name for the file
            
        Returns:
            Formatted string with all content including tables and JSON
        """
        if filename is None:
            filename = file_path
        
        content_parts = [f"\n\n{'='*80}\nDocument: {filename}\n{'='*80}\n"]
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                content_parts.append(f"\n[Page {page_num}]\n")
                
                # Extract tables on this page
                tables = page.extract_tables()
                
                # Get bounding boxes of tables to exclude from text extraction
                table_bboxes = []
                if tables:
                    for table in page.find_tables():
                        table_bboxes.append(table.bbox)
                
                # Extract text excluding table areas
                if table_bboxes:
                    # Extract text outside of tables
                    text = page.filter(lambda obj: not any(
                        self._is_within_bbox(obj, bbox) for bbox in table_bboxes
                    )).extract_text()
                else:
                    text = page.extract_text()
                
                # Check for JSON/JSONL content in the text
                if text and text.strip():
                    # Detect and format JSON content
                    json_objects = self._extract_json_content(text)
                    
                    if json_objects:
                        # Add regular text (non-JSON parts)
                        non_json_text = self._remove_json_from_text(text)
                        if non_json_text.strip():
                            content_parts.append(f"{non_json_text}\n")
                        
                        # Add formatted JSON objects
                        for json_idx, json_obj in enumerate(json_objects, 1):
                            formatted_json = self._format_json_object(
                                json_obj, 
                                page_num, 
                                json_idx,
                                filename
                            )
                            content_parts.append(f"\n{formatted_json}\n")
                    else:
                        # No JSON found, add as regular text
                        content_parts.append(f"{text}\n")
                
                # Add tables with proper formatting
                if tables:
                    for table_idx, table in enumerate(tables, 1):
                        if table and len(table) > 0:
                            formatted_table = self._format_table(
                                table, 
                                page_num, 
                                table_idx,
                                filename
                            )
                            content_parts.append(f"\n{formatted_table}\n")
        
        return "\n".join(content_parts)
    
    def _is_within_bbox(self, obj: Dict, bbox: Tuple) -> bool:
        """Check if an object is within a bounding box."""
        x0, y0, x1, y1 = bbox
        obj_x0 = obj.get('x0', 0)
        obj_y0 = obj.get('top', 0)
        obj_x1 = obj.get('x1', 0)
        obj_y1 = obj.get('bottom', 0)
        
        return (obj_x0 >= x0 and obj_x1 <= x1 and 
                obj_y0 >= y0 and obj_y1 <= y1)
    
    def _format_table(self, table: List[List], page_num: int, table_idx: int, filename: str) -> str:
        """
        Format a table for better readability and LLM understanding.
        
        Args:
            table: Table data as list of lists
            page_num: Page number where table appears
            table_idx: Index of table on the page
            filename: Name of the source document
            
        Returns:
            Formatted table string
        """
        if not table or len(table) == 0:
            return ""
        
        # Clean the table data
        cleaned_table = []
        for row in table:
            cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
            # Skip completely empty rows
            if any(cleaned_row):
                cleaned_table.append(cleaned_row)
        
        if not cleaned_table:
            return ""
        
        # Build table representation
        table_parts = []
        table_parts.append(f"--- TABLE {table_idx} (Document: {filename}, Page {page_num}) ---")
        
        # Assume first row is header
        headers = cleaned_table[0]
        data_rows = cleaned_table[1:]
        
        # Create DataFrame for better formatting
        try:
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Convert to string representation
            table_parts.append("\nColumn Headers:")
            table_parts.append(" | ".join(headers))
            table_parts.append("-" * 80)
            
            table_parts.append("\nTable Data:")
            for idx, row in df.iterrows():
                row_str = " | ".join([str(val) for val in row])
                table_parts.append(row_str)
            
            # Also add a markdown-style table for better LLM understanding
            table_parts.append("\nMarkdown Format:")
            table_parts.append("| " + " | ".join(headers) + " |")
            table_parts.append("|" + "|".join(["---" for _ in headers]) + "|")
            for idx, row in df.iterrows():
                table_parts.append("| " + " | ".join([str(val) for val in row]) + " |")
            
        except Exception as e:
            # Fallback to simple formatting if DataFrame creation fails
            table_parts.append("\nRaw Table Data:")
            for row in cleaned_table:
                table_parts.append(" | ".join(row))
        
        table_parts.append(f"--- END TABLE {table_idx} ---\n")
        
        return "\n".join(table_parts)
    
    def extract_from_multiple_files(self, file_paths: List[str], filenames: List[str] = None) -> str:
        """
        Extract content from multiple PDF files.
        
        Args:
            file_paths: List of file paths
            filenames: Optional list of display names
            
        Returns:
            Combined extracted content from all files
        """
        all_content = []
        
        if filenames is None:
            filenames = file_paths
        
        for file_path, filename in zip(file_paths, filenames):
            try:
                content = self.extract_from_file(file_path, filename)
                all_content.append(content)
            except Exception as e:
                all_content.append(f"\n\n[ERROR] Failed to extract from {filename}: {str(e)}\n")
        
        return "\n\n".join(all_content)
    
    def _extract_json_content(self, text: str) -> List[Dict]:
        """
        Extract JSON or JSONL objects from text.
        
        Args:
            text: Text that may contain JSON data
            
        Returns:
            List of parsed JSON objects
        """
        json_objects = []
        
        # Try to find JSON objects using regex
        # Pattern for JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        matches = re.finditer(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                json_str = match.group(0)
                json_obj = json.loads(json_str)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                # Try to handle JSONL (one JSON per line)
                lines = match.group(0).split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            json_obj = json.loads(line)
                            json_objects.append(json_obj)
                        except:
                            pass
        
        return json_objects
    
    def _remove_json_from_text(self, text: str) -> str:
        """Remove JSON objects from text to get only regular text."""
        # Remove JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        cleaned_text = re.sub(json_pattern, '', text, flags=re.DOTALL)
        return cleaned_text
    
    def _format_json_object(self, json_obj: Dict, page_num: int, json_idx: int, filename: str) -> str:
        """
        Format a JSON object for better LLM understanding.
        
        Args:
            json_obj: Parsed JSON object
            page_num: Page number where JSON appears
            json_idx: Index of JSON object on the page
            filename: Name of the source document
            
        Returns:
            Formatted JSON string
        """
        json_parts = []
        json_parts.append(f"--- JSON OBJECT {json_idx} (Document: {filename}, Page {page_num}) ---")
        
        # Add formatted key-value pairs
        json_parts.append("\nStructured Data:")
        for key, value in json_obj.items():
            # Clean up the value for better readability
            if isinstance(value, str):
                # Remove extra whitespace
                value = ' '.join(value.split())
            json_parts.append(f"  {key}: {value}")
        
        # Add JSON format for reference
        json_parts.append("\nJSON Format:")
        json_parts.append(json.dumps(json_obj, indent=2))
        
        json_parts.append(f"--- END JSON OBJECT {json_idx} ---\n")
        
        return "\n".join(json_parts)
    
    def extract_tables_only(self, file_path: str) -> List[pd.DataFrame]:
        """
        Extract only tables from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of DataFrames, one for each table
        """
        tables_list = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        try:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df['_source_page'] = page_num
                            tables_list.append(df)
                        except:
                            pass
        
        return tables_list

