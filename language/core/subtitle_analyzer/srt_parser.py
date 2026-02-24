"""
SRT Parser Module

Handles parsing of SubRip (.srt) subtitle files and extracting text content.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


class SRTParser:
    """Parse SubRip (.srt) subtitle files and extract text content."""
    
    # Regex pattern for timestamp lines (e.g., "00:00:05,000 --> 00:00:09,720")
    TIMESTAMP_PATTERN = re.compile(
        r'^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
    )
    
    def __init__(self):
        """Initialize SRT parser."""
        self.files_processed = []
        self.parse_errors = []
    
    def is_timestamp_line(self, line: str) -> bool:
        """Check if a line is a timestamp."""
        return bool(self.TIMESTAMP_PATTERN.match(line.strip()))
    
    def is_index_line(self, line: str) -> bool:
        """Check if a line is a subtitle index number."""
        return line.strip().isdigit()
    
    def parse_file(self, filepath: Path) -> List[str]:
        """
        Parse a single SRT file and extract subtitle text.
        
        Args:
            filepath: Path to the .srt file
            
        Returns:
            List of subtitle text lines
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file encoding is not supported
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        text_lines = []
        
        try:
            # Try UTF-8 first, fallback to latin-1
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise UnicodeDecodeError(
                    "Unable to decode file with supported encodings"
                )
            
            for line in content:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip index numbers
                if self.is_index_line(line):
                    continue
                
                # Skip timestamp lines
                if self.is_timestamp_line(line):
                    continue
                
                # This is subtitle text
                text_lines.append(line)
            
            self.files_processed.append(str(filepath))
            
        except Exception as e:
            error_msg = f"Error parsing {filepath}: {str(e)}"
            self.parse_errors.append(error_msg)
            raise
        
        return text_lines
    
    def parse_directory(
        self, 
        dirpath: Path, 
        pattern: str = "*.srt"
    ) -> Dict[str, List[str]]:
        """
        Parse all SRT files in a directory.
        
        Args:
            dirpath: Path to directory containing .srt files
            pattern: File pattern to match (default: "*.srt")
            
        Returns:
            Dictionary mapping filename to list of subtitle text lines
        """
        if not dirpath.exists():
            raise FileNotFoundError(f"Directory not found: {dirpath}")
        
        if not dirpath.is_dir():
            raise ValueError(f"Path is not a directory: {dirpath}")
        
        results = {}
        srt_files = sorted(dirpath.glob(pattern))
        
        if not srt_files:
            raise ValueError(f"No files matching '{pattern}' found in {dirpath}")
        
        for srt_file in srt_files:
            try:
                text_lines = self.parse_file(srt_file)
                results[srt_file.name] = text_lines
            except Exception as e:
                # Log error but continue processing other files
                error_msg = f"Failed to parse {srt_file.name}: {str(e)}"
                self.parse_errors.append(error_msg)
                print(f"⚠️  {error_msg}")
        
        return results
    
    def get_all_text(self, parsed_data: Dict[str, List[str]]) -> str:
        """
        Combine all subtitle text from parsed data into single string.
        
        Args:
            parsed_data: Dictionary from parse_directory()
            
        Returns:
            All subtitle text combined
        """
        all_text = []
        for lines in parsed_data.values():
            all_text.extend(lines)
        return " ".join(all_text)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get parsing statistics.
        
        Returns:
            Dictionary with processing stats
        """
        return {
            "files_processed": len(self.files_processed),
            "parse_errors": len(self.parse_errors)
        }
