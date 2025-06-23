#!/usr/bin/python
import requests
import string
import unicodedata
import re
import time


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
    def __init__(self) -> None:
        self.all_talk_base_url = "http://ask-gpt.example.com:7851"
        self.all_talk_url = self.all_talk_base_url + "/api/tts-generate"

    def request_audio_generation(
        self,
        word_language: str,
        sentence: str,
        audio_backend_url: str = None,
        character_voice: str = "female_02",
    ) -> str:
        """
        Description:
            Requests audio generation using the specified word language and sentence.

        Args:
            word_language (str): The language of the word.
            sentence (str): The sentence to generate audio for.
            audio_backend_url (str, optional): The URL of the audio generation backend. Defaults to None.

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
            "output_file_name": file_name,
            "output_file_timestamp": "false",
            "autoplay": "true",
            "autoplay_volume": "0.8",
        }
        response = requests.post(audio_backend_url, data=data)
        file_url = self.all_talk_base_url + self.parse_audio_url(response)
        print(file_url)
        if not file_url:
            print("Problem with parsing the URL from All Talk")
            return
        return self.retrieve_audio_file(
            file_url=file_url, language_code=word_language, filename=file_name
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

    def retrieve_audio_file(self, file_url: str, language_code: str, filename: str):
        """
        Description:
            Retrieves an audio file from the specified URL and saves it locally.

        Args:
            file_url: The URL of the audio file.
            language_code: The language code associated with the audio file.
            filename: The desired filename for the downloaded audio file.

        Returns:
            The file path of the downloaded audio file, or None if the download fails.
        """
        response = requests.get(file_url)
        file_output_location = f"./{filename}.wav"
        # file_output_location = f"{filename}.wav"
        if response.status_code == 200:
            with open(file_output_location, "wb") as file:
                file.write(response.content)
                print("File downloaded successfully.")
            return file_output_location
        else:
            print("Failed to download the file.")
            return None


with open("language/spanish_words.txt", "r") as file:
    lines = file.readlines()

audio_ops = GenerateAudio()

counter = 2
while counter <= 7:
    for line in lines:
        if line.strip():
            word = line.strip().strip(".")
            audio_path = audio_ops.request_audio_generation(
                word_language="es",
                sentence=remove_special_chars(word),
                character_voice=f"female_0{counter}",
            )
        time.sleep(0.25)
    counter += 1
