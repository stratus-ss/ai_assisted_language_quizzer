#!/usr/bin/env python3
"""
Clean subtitle files by removing Amara.org credits and renumbering entries.
"""
import os
import re
from pathlib import Path
from typing import List, Tuple


class SubtitleCleaner:
    """Handles cleaning and renumbering of SRT subtitle files."""
    
    def __init__(self, subtitles_dir: str):
        self.subtitles_dir = Path(subtitles_dir)
        self.amara_patterns = [
            "Subtítulos realizados por la comunidad de Amara.org",
            "Subtítulos por la comunidad de Amara.org"
        ]
        
    def parse_srt_file(self, filepath: Path) -> List[Tuple[str, str, str]]:
        """
        Parse an SRT file into subtitle entries.
        
        Returns:
            List of tuples (index, timestamp, text)
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entries = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                index = lines[0].strip()
                timestamp = lines[1].strip()
                text = '\n'.join(lines[2:])
                entries.append((index, timestamp, text))
            elif len(lines) == 2:
                # Handle cases with just index and timestamp
                index = lines[0].strip()
                timestamp = lines[1].strip()
                entries.append((index, timestamp, ''))
        
        return entries
    
    def should_remove_entry(self, text: str) -> bool:
        """Check if an entry should be removed."""
        return any(pattern in text for pattern in self.amara_patterns)
    
    def clean_and_renumber(
        self, 
        entries: List[Tuple[str, str, str]]
    ) -> List[Tuple[str, str, str]]:
        """
        Remove Amara.org entries and renumber remaining entries.
        
        Returns:
            List of cleaned and renumbered entries
        """
        cleaned = []
        new_index = 1
        
        for _, timestamp, text in entries:
            if not self.should_remove_entry(text):
                cleaned.append((str(new_index), timestamp, text))
                new_index += 1
        
        return cleaned
    
    def write_srt_file(
        self, 
        filepath: Path, 
        entries: List[Tuple[str, str, str]]
    ) -> None:
        """Write entries back to an SRT file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, (index, timestamp, text) in enumerate(entries):
                f.write(f"{index}\n")
                f.write(f"{timestamp}\n")
                if text:
                    f.write(f"{text}\n")
                
                # Add blank line between entries (except after last entry)
                if i < len(entries) - 1:
                    f.write("\n")
    
    def process_file(self, filepath: Path) -> Tuple[int, int]:
        """
        Process a single subtitle file.
        
        Returns:
            Tuple of (original_count, removed_count)
        """
        print(f"Processing: {filepath.name}")
        
        entries = self.parse_srt_file(filepath)
        original_count = len(entries)
        
        cleaned_entries = self.clean_and_renumber(entries)
        removed_count = original_count - len(cleaned_entries)
        
        if removed_count > 0:
            self.write_srt_file(filepath, cleaned_entries)
            print(f"  Removed {removed_count} entries, kept {len(cleaned_entries)}")
        else:
            print(f"  No Amara.org entries found")
        
        return original_count, removed_count
    
    def process_all_files(self) -> None:
        """Process all SRT files in the subtitles directory."""
        srt_files = list(self.subtitles_dir.glob("*.srt"))
        
        if not srt_files:
            print(f"No SRT files found in {self.subtitles_dir}")
            return
        
        print(f"Found {len(srt_files)} SRT files\n")
        
        total_removed = 0
        files_modified = 0
        
        for filepath in sorted(srt_files):
            original_count, removed_count = self.process_file(filepath)
            total_removed += removed_count
            if removed_count > 0:
                files_modified += 1
        
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Total files processed: {len(srt_files)}")
        print(f"  Files modified: {files_modified}")
        print(f"  Total entries removed: {total_removed}")
        print(f"{'='*60}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    subtitles_dir = script_dir.parent / "subtitles"
    
    if not subtitles_dir.exists():
        print(f"Error: Subtitles directory not found: {subtitles_dir}")
        return
    
    cleaner = SubtitleCleaner(str(subtitles_dir))
    cleaner.process_all_files()


if __name__ == "__main__":
    main()
