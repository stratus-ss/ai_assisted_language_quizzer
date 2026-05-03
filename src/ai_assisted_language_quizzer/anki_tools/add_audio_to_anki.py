#!/usr/bin/env python3
"""
Add audio files to Anki notes using AnkiConnect API.

Prerequisites:
1. Install AnkiConnect add-on in Anki (Code: 2055492159)
2. Anki must be running while this script executes
3. Audio files should exist in the specified directory

This script reads a word list and adds corresponding audio files to Anki notes.
"""
import json
import requests
import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional


class AnkiConnector:
    """Handle communication with Anki via AnkiConnect API."""
    
    def __init__(self, url: str = "http://localhost:8765"):
        """
        Initialize AnkiConnect connector.
        
        Args:
            url: AnkiConnect API endpoint (default: http://localhost:8765)
        """
        self.url = url
        self.version = 6
    
    def invoke(self, action: str, **params) -> Dict:
        """
        Send a request to AnkiConnect API.
        
        Args:
            action: The AnkiConnect action to perform
            **params: Parameters for the action
            
        Returns:
            Response from AnkiConnect API
            
        Raises:
            Exception: If the request fails or returns an error
        """
        payload = {
            "action": action,
            "version": self.version,
            "params": params
        }
        
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error") is not None:
                raise Exception(f"AnkiConnect error: {result['error']}")
            
            return result.get("result")
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to Anki. Make sure Anki is running and "
                "AnkiConnect add-on is installed."
            )
    
    def store_media_file(self, filename: str, file_path: str) -> str:
        """
        Store a media file in Anki's media collection.
        
        Args:
            filename: Name to store the file as in Anki
            file_path: Path to the local file
            
        Returns:
            Filename as stored in Anki
        """
        with open(file_path, "rb") as f:
            import base64
            data = base64.b64encode(f.read()).decode("utf-8")
        
        return self.invoke(
            "storeMediaFile",
            filename=filename,
            data=data
        )
    
    def find_notes(self, query: str) -> List[int]:
        """
        Find note IDs matching a query.
        
        Args:
            query: Anki search query
            
        Returns:
            List of note IDs
        """
        return self.invoke("findNotes", query=query)
    
    def notes_info(self, note_ids: List[int]) -> List[Dict]:
        """
        Get information about notes.
        
        Args:
            note_ids: List of note IDs
            
        Returns:
            List of note information dictionaries
        """
        return self.invoke("notesInfo", notes=note_ids)
    
    def update_note_fields(
        self, 
        note_id: int, 
        fields: Dict[str, str],
        audio: Optional[List[Dict]] = None
    ) -> None:
        """
        Update fields of an existing note.
        
        Args:
            note_id: ID of the note to update
            fields: Dictionary of field names to values
            audio: Optional list of audio objects to add
        """
        note = {
            "id": note_id,
            "fields": fields
        }
        
        if audio:
            note["audio"] = audio
        
        self.invoke("updateNoteFields", note=note)


class AudioAttacher:
    """Attach audio files to Anki notes."""
    
    def __init__(
        self, 
        audio_directory: Optional[str],
        anki_connector: AnkiConnector,
        deck_name: Optional[str] = None
    ):
        """
        Initialize AudioAttacher.
        
        Args:
            audio_directory: Directory containing audio files (optional for missing-audio mode)
            anki_connector: AnkiConnector instance
            deck_name: Optional deck name to limit search
        """
        self.audio_dir = Path(audio_directory) if audio_directory else None
        self.anki = anki_connector
        self.deck_name = deck_name
    
    def find_audio_file(self, word: str) -> Optional[Path]:
        """
        Find an audio file for a word.
        
        Args:
            word: The word to find audio for
            
        Returns:
            Path to audio file if found, None otherwise
        """
        # Try exact match first
        for pattern in [f"{word}_female_*.wav", f"{word}.wav", f"{word}.mp3"]:
            matches = list(self.audio_dir.glob(pattern))
            if matches:
                return matches[0]  # Return first match
        
        return None
    
    def attach_audio_to_note(
        self, 
        word: str, 
        audio_field: str = "Audio",
        search_field: str = "Front"
    ) -> bool:
        """
        Attach audio to a note containing the specified word.
        
        Args:
            word: The word to search for
            audio_field: Name of the field to add audio to
            search_field: Field to search for the word in
            
        Returns:
            True if successful, False otherwise
        """
        # Find audio file
        audio_file = self.find_audio_file(word)
        if not audio_file:
            print(f"  ❌ No audio file found for: {word}")
            return False
        
        # Build search query
        if self.deck_name:
            query = f'deck:"{self.deck_name}" {search_field}:{word}'
        else:
            query = f'{search_field}:{word}'
        
        # Find notes
        note_ids = self.anki.find_notes(query)
        if not note_ids:
            print(f"  ⚠️  No notes found for: {word}")
            return False
        
        # Process each note
        success_count = 0
        for note_id in note_ids:
            try:
                # Get note info
                notes_info = self.anki.notes_info([note_id])
                if not notes_info:
                    continue
                
                note = notes_info[0]
                
                # Check if audio field exists
                if audio_field not in note["fields"]:
                    print(f"  ⚠️  Field '{audio_field}' not found in note")
                    continue
                
                # Check if audio already exists
                current_value = note["fields"][audio_field]["value"]
                if "[sound:" in current_value:
                    print(f"  ℹ️  Audio already exists for: {word}")
                    continue
                
                # Store audio file in Anki
                stored_filename = self.anki.store_media_file(
                    audio_file.name,
                    str(audio_file)
                )
                
                # Update note with audio tag
                audio_tag = f"[sound:{stored_filename}]"
                new_value = current_value + audio_tag
                
                self.anki.update_note_fields(
                    note_id,
                    {audio_field: new_value}
                )
                
                print(f"  ✓ Added audio to: {word} (Note ID: {note_id})")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing note {note_id}: {e}")
        
        return success_count > 0
    
    def find_notes_missing_audio(
        self,
        audio_field: str = "Audio",
        search_field: str = "Front"
    ) -> List[str]:
        """
        Find all words in the deck that don't have audio files.
        
        Args:
            audio_field: Name of the field that should contain audio
            search_field: Field containing the word
            
        Returns:
            List of words missing audio
        """
        # Build search query
        if self.deck_name:
            query = f'deck:"{self.deck_name}"'
        else:
            query = "*"
        
        # Find all notes
        note_ids = self.anki.find_notes(query)
        if not note_ids:
            print("⚠️  No notes found in the specified deck")
            return []
        
        print(f"Found {len(note_ids)} notes in deck")
        
        # Get note information
        notes_info = self.anki.notes_info(note_ids)
        
        # Find notes missing audio
        missing_audio = []
        for note in notes_info:
            if search_field not in note["fields"]:
                continue
            
            # Get the word from search field (may contain audio tags too)
            field_value = note["fields"][search_field]["value"]
            
            # Check if audio is missing (no [sound: tag present)
            has_audio = "[sound:" in field_value
            
            if not has_audio:
                # Extract the word (strip HTML tags)
                word = field_value.replace("<br>", " ").replace("<div>", " ").replace("</div>", " ")
                word = re.sub(r'<[^>]+>', '', word).strip()
                
                if word:
                    missing_audio.append(word)
        
        return missing_audio
    
    def process_word_list(
        self, 
        word_list_file: str,
        audio_field: str = "Audio",
        search_field: str = "Front"
    ) -> Dict[str, int]:
        """
        Process a list of words and attach audio to corresponding notes.
        
        Args:
            word_list_file: Path to file containing words (one per line)
            audio_field: Name of the field to add audio to
            search_field: Field to search for the word in
            
        Returns:
            Dictionary with statistics
        """
        with open(word_list_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        
        stats = {
            "total": len(words),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        print(f"\nProcessing {len(words)} words...")
        print(f"Audio directory: {self.audio_dir}")
        print(f"Target field: {audio_field}\n")
        
        for i, word in enumerate(words, 1):
            print(f"[{i}/{len(words)}] Processing: {word}")
            
            if self.attach_audio_to_note(word, audio_field, search_field):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        return stats


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Add audio files to Anki notes using AnkiConnect API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add audio to Spanish deck
  %(prog)s -a ./spanish_female01 -w lingq.txt -d "LingQ es 3810112"
  
  # Specify custom field names
  %(prog)s -a ./audio -w words.txt -d "Spanish" --audio-field "Audio" --search-field "Front"
  
  # Search all decks
  %(prog)s -a ./audio -w words.txt
  
  # Find words missing audio in a deck
  %(prog)s --missing-audio -d "LingQ es 3810112" --search-field "Front" --audio-field "Front"
  
  # Save missing words to file for use with other scripts
  %(prog)s --missing-audio -d "Subtitle_High_Frequency" --search-field "Front" -o missing_words.txt

Prerequisites:
  1. Install AnkiConnect add-on in Anki (Code: 2055492159)
  2. Anki must be running while this script executes
        """
    )
    
    parser.add_argument(
        "-a", "--audio-dir",
        default=None,
        help="Directory containing audio files"
    )
    
    parser.add_argument(
        "-w", "--word-list",
        default=None,
        help="Text file with words to process (one per line)"
    )
    
    parser.add_argument(
        "-d", "--deck",
        default=None,
        help="Anki deck name to search (searches all decks if not specified)"
    )
    
    parser.add_argument(
        "--audio-field",
        default="Front",
        help="Field name where audio should be added (default: term)"
    )
    
    parser.add_argument(
        "--search-field",
        default="Front",
        help="Field name containing the word to search for (default: term)"
    )
    
    parser.add_argument(
        "--anki-url",
        default="http://localhost:8765",
        help="AnkiConnect API URL (default: http://localhost:8765)"
    )
    
    parser.add_argument(
        "--missing-audio",
        action="store_true",
        help="Find and list words in the deck that are missing audio files"
    )
    
    parser.add_argument(
        "-o", "--output-file",
        default=None,
        help="Output file to save missing words list (only used with --missing-audio)"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments based on mode
    if not args.missing_audio:
        if not args.audio_dir:
            parser.error("--audio-dir is required when not using --missing-audio")
        if not args.word_list:
            parser.error("--word-list is required when not using --missing-audio")
    
    return args


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Check if Anki is running
    try:
        anki = AnkiConnector(url=args.anki_url)
        version = anki.invoke("version")
        print(f"✓ Connected to AnkiConnect (version: {version})")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Anki is running")
        print("2. AnkiConnect add-on is installed (Code: 2055492159)")
        return 1
    
    # Handle missing-audio mode
    if args.missing_audio:
        print("=" * 60)
        print("Find Words Missing Audio")
        print("=" * 60)
        print(f"Deck: {args.deck or 'All decks'}")
        print(f"Audio field: {args.audio_field}")
        print(f"Search field: {args.search_field}")
        print("=" * 60)
        
        attacher = AudioAttacher(
            audio_directory=None,
            anki_connector=anki,
            deck_name=args.deck
        )
        
        missing_words = attacher.find_notes_missing_audio(
            audio_field=args.audio_field,
            search_field=args.search_field
        )
        
        print("\n" + "=" * 60)
        print("WORDS MISSING AUDIO")
        print("=" * 60)
        if missing_words:
            unique_words = sorted(set(missing_words))
            
            # Save to file if specified
            if args.output_file:
                output_path = Path(args.output_file)
                with open(output_path, 'w', encoding='utf-8') as f:
                    for word in unique_words:
                        f.write(word + '\n')
                print(f"✓ Saved {len(unique_words)} words to: {output_path}\n")
            
            # Print to screen
            for word in unique_words:
                print(word)
            print("=" * 60)
            print(f"Total: {len(unique_words)} words missing audio")
        else:
            print("✓ All notes have audio!")
        print("=" * 60)
        
        return 0
    
    # Normal mode - add audio to notes
    # Validate paths
    audio_dir = Path(args.audio_dir)
    if not audio_dir.exists():
        print(f"❌ Error: Audio directory not found: {audio_dir}")
        return 1
    
    word_list = Path(args.word_list)
    if not word_list.exists():
        print(f"❌ Error: Word list file not found: {word_list}")
        return 1
    
    print("=" * 60)
    print("Anki Audio Attacher")
    print("=" * 60)
    print(f"Audio directory: {audio_dir}")
    print(f"Word list: {word_list}")
    print(f"Deck: {args.deck or 'All decks'}")
    print(f"Audio field: {args.audio_field}")
    print(f"Search field: {args.search_field}")
    print("=" * 60)
    
    # Create audio attacher
    attacher = AudioAttacher(
        audio_directory=str(audio_dir),
        anki_connector=anki,
        deck_name=args.deck
    )
    
    # Process word list
    stats = attacher.process_word_list(
        word_list_file=str(word_list),
        audio_field=args.audio_field,
        search_field=args.search_field
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total words processed: {stats['total']}")
    print(f"Successfully added audio: {stats['success']}")
    print(f"Failed/Not found: {stats['failed']}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
