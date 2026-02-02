#!/usr/bin/python
import requests
import string
import unicodedata
import re
import time
import argparse
from pathlib import Path


def remove_special_chars(input_string):
    # Normalize the string and remove accents
    normalized = unicodedata.normalize("NFD", input_string)

    # Remove non-Latin characters and non-spacing marks
    cleaned = "".join(
        c for c in normalized if c.isascii() and not unicodedata.combining(c)
    )

    # Remove special characters like @#$%^&*()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    cleaned = cleaned.replace(" ", "_")
    return cleaned


class GenerateAudio:
    def __init__(self, base_url: str = "http://localhost:7851") -> None:
        """
        Initialize GenerateAudio class.
        
        Args:
            base_url: Base URL for AllTalk server (default: http://localhost:7851)
        """
        self.all_talk_base_url = base_url
        self.all_talk_url = self.all_talk_base_url + "/api/tts-generate"

    def request_audio_generation(
        self,
        word_language: str,
        sentence: str,
        audio_backend_url: str = None,
        character_voice: str = "female_02",
        output_dir: str = ".",
    ) -> str:
        """
        Description:
            Requests audio generation using the specified word language and sentence.

        Args:
            word_language (str): The language of the word.
            sentence (str): The sentence to generate audio for.
            audio_backend_url (str, optional): The URL of the audio generation backend. Defaults to None.
            character_voice (str, optional): The voice to use. Defaults to "female_02".
            output_dir (str, optional): Directory to save audio files. Defaults to ".".

        Returns:
            str: The file output location of the generated audio.

        Examples:
            >>> request_audio_generation("english", "Hello, world!")
            './audio/english/Hello.wav'
        """
        word_language = word_language.lower()
        if audio_backend_url:
            audio_backend_url = audio_backend_url
        else:
            audio_backend_url = self.all_talk_url
        # file name needs to be adjusted as it doesn't like the special chars of german
        if not sentence:
            return ()
        file_name = sentence + f"_{character_voice}"
        if len(sentence.split()) > 3:
            file_name = (
                " ".join(sentence.split()[:3])
                .translate(str.maketrans("", "", string.punctuation))
                .replace(" ", "_")
            )
        data = {
            "text_input": sentence,
            "text_filtering": "standard",
            "character_voice_gen": f"{character_voice}.wav",
            "narrator_enabled": "false",
            "narrator_voice_gen": "male_01.wav",
            "text_not_inside": "character",
            "language": word_language,
            "output_file_name": f"{file_name}",
            "output_file_timestamp": "true",
            "autoplay": "false",
            "autoplay_volume": "0.8",
        }
        response = requests.post(audio_backend_url, data=data)
        url_context = self.parse_audio_url(response)
        file_url = self.all_talk_base_url + url_context
        print(file_url)
        if not file_url:
            print("Problem with parsing the URL from All Talk")
            return
        return self.retrieve_audio_file(
            file_url=file_url, language_code=word_language, filename=file_name, output_dir=output_dir
        )

    def parse_audio_url(self, response):
        """
        Description:
            Parses the audio URL from the response.

        Args:
            response: The response object.

        Returns:
            The audio URL extracted from the response, or None if it cannot be parsed.
        """
        try:
            return response.json()["output_file_url"]
        except KeyError:
            print("Problem parsing response from AllTalk Server")
            return None

    def retrieve_audio_file(self, file_url: str, language_code: str, filename: str, output_dir: str = "."):
        """
        Description:
            Retrieves an audio file from the specified URL and saves it locally.

        Args:
            file_url: The URL of the audio file.
            language_code: The language code associated with the audio file.
            filename: The desired filename for the downloaded audio file.
            output_dir: Directory to save the audio file (default: current directory).

        Returns:
            The file path of the downloaded audio file, or None if the download fails.
        """
        response = requests.get(file_url)
        output_path = Path(output_dir)
        file_output_location = output_path / f"{filename}.wav"
        
        if response.status_code == 200:
            with open(file_output_location, "wb") as file:
                file.write(response.content)
                print(f"  ✓ File downloaded: {file_output_location}")
            return str(file_output_location)
        else:
            print("  ❌ Failed to download the file.")
            return None


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate audio files from word list using AllTalk TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Spanish audio for words in a file
  %(prog)s -w words.txt -l es -v female_03-female_07
  
  # Generate single voice
  %(prog)s -w words.txt -l es -v female_03
  
  # Use custom AllTalk server
  %(prog)s -w words.txt -l es -v female_03 --server http://192.168.1.100:7851
  
  # Adjust delay between requests
  %(prog)s -w words.txt -l es -v female_03-female_05 --delay 0.5
        """
    )
    
    parser.add_argument(
        "-w", "--word-list",
        required=True,
        help="Text file containing words to generate audio for (one per line)"
    )
    
    parser.add_argument(
        "-l", "--language",
        required=True,
        help="Language code (e.g., 'es' for Spanish, 'de' for German)"
    )
    
    parser.add_argument(
        "-v", "--voice",
        required=True,
        help="Voice(s) to use. Single voice (e.g., 'female_03') or range (e.g., 'female_03-female_07')"
    )
    
    parser.add_argument(
        "-s", "--server",
        default="http://localhost:7851",
        help="AllTalk server URL (default: http://localhost:7851)"
    )
    
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.25,
        help="Delay in seconds between audio generation requests (default: 0.25)"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Output directory for audio files (default: current directory)"
    )
    
    return parser.parse_args()


def parse_voice_range(voice_str: str):
    """
    Parse voice argument into a list of voice names.
    
    Args:
        voice_str: Voice string (e.g., 'female_03' or 'female_03-female_07')
        
    Returns:
        List of voice names
    """
    if "-" in voice_str:
        # Parse range like "female_03-female_07"
        start_voice, end_voice = voice_str.split("-")
        
        # Extract prefix and numbers
        # Assumes format like "female_03"
        start_num = int(start_voice.split("_")[-1])
        end_num = int(end_voice.split("_")[-1])
        prefix = "_".join(start_voice.split("_")[:-1])
        
        # Generate list
        voices = [f"{prefix}_{i:02d}" for i in range(start_num, end_num + 1)]
        return voices
    else:
        # Single voice
        return [voice_str]


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Validate word list file
    word_list_path = Path(args.word_list)
    if not word_list_path.exists():
        print(f"❌ Error: Word list file not found: {word_list_path}")
        return 1
    
    # Create output directory if needed
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse voice range
    voices = parse_voice_range(args.voice)
    
    # Read word list
    with open(word_list_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    words = [line.strip().strip(".") for line in lines if line.strip()]
    
    print("=" * 60)
    print("AllTalk Audio Generator")
    print("=" * 60)
    print(f"Word list: {word_list_path}")
    print(f"Total words: {len(words)}")
    print(f"Language: {args.language}")
    print(f"Voices: {', '.join(voices)}")
    print(f"Server: {args.server}")
    print(f"Output directory: {output_dir}")
    print(f"Delay: {args.delay}s")
    print("=" * 60)
    
    # Initialize audio generator
    audio_ops = GenerateAudio(base_url=args.server)
    
    # Process each voice
    total_generated = 0
    total_failed = 0
    
    for voice in voices:
        print(f"\n🎤 Processing with voice: {voice}")
        print("-" * 60)
        
        for i, word in enumerate(words, 1):
            print(f"[{i}/{len(words)}] Generating: {word}")
            
            try:
                audio_path = audio_ops.request_audio_generation(
                    word_language=args.language,
                    sentence=remove_special_chars(word),
                    character_voice=voice,
                    output_dir=str(output_dir),
                )
                
                if audio_path:
                    total_generated += 1
                else:
                    total_failed += 1
                    print(f"  ⚠️  Failed to generate audio for: {word}")
                    
            except Exception as e:
                total_failed += 1
                print(f"  ❌ Error generating audio for '{word}': {e}")
            
            # Delay between requests to avoid overwhelming server
            time.sleep(args.delay)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total words: {len(words)}")
    print(f"Voices used: {len(voices)}")
    print(f"Total audio files generated: {total_generated}")
    print(f"Failed: {total_failed}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
