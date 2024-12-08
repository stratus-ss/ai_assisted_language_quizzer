#!/usr/bin/python
import contextlib
import yaml
import logging
import requests
import string
from dotenv import load_dotenv
import os

load_dotenv()


class HandleFileOperations:
    def __init__(self, filepath: str = None):
        # Make a list of the keys that are required in the word dict
        # required for input validation before writing the file
        # Assume the dict should be the following format
        # {<word or phrase>: {<meaning>: <val>, <image path>: <val>, <audio path>: <val>, <grammar type>: <val>}}
        self.required_keys = ["meaning", "image", "audio", "type"]
        self.file_path = filepath

    def write_file(self, new_word: dict = None):
        """
        Description:
            Checks the current list to see if exact word or phrase exists
            If not and the new word or phrase has all the required information
            add it to the dict and write it back out to a file
        Args:
            filepath (str, optional): The path to the file to read/write. Defaults to None.
            new_word (dict, optional): A dict that contains the word or phrase as its key
                                       and then a nested dict with other attributes. Defaults to None.
        """
        current_dict = None
        with contextlib.suppress(FileNotFoundError):
            current_dict = self.read_file()
        if not isinstance(current_dict, dict):
            if current_dict is None:
                logging.info("File on disk is empty... working with empty list")
            else:
                logging.error(
                    f"Cannot add {current_dict} to config file. It is not a dict"
                )
                exit(1)
        for language_name, value_ in new_word.items():
            for key in value_:
                if any(
                    value not in new_word[language_name][key]
                    for value in self.required_keys
                ):
                    logging.error(
                        "Attempted to insert a word/phrase but it's missing required keys"
                    )
                    logging.error(f"Expected keys are {self.required_keys}")
                    return
        if current_dict is not None:
            for language_name, value__ in new_word.items():
                for key in value__:
                    if key not in current_dict:
                        current_dict[language_name][key] = new_word[language_name][key]
        else:
            current_dict = new_word
        with open(self.file_path, "w") as file:
            file.write(yaml.dump(current_dict))
            file.close()

    def read_file(self):
        word_dict = {}
        with open(self.file_path, "r") as file:
            word_dict = file.read()
        file.close()
        return yaml.load(word_dict, Loader=yaml.FullLoader)
        # read the file and return the results


class GenerateAudio:
    def __init__(self) -> None:
        self.all_talk_url = os.getenv("ALL_TALK_URL")

    def request_audio_generation(
        self, word_language: str, sentence: str, audio_backend_url: str = None
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
        file_name = sentence
        if len(sentence.split()) > 3:
            file_name = (
                " ".join(sentence.split()[:3])
                .translate(str.maketrans("", "", string.punctuation))
                .replace(" ", "_")
            )
        data = {
            "text_input": sentence,
            "text_filtering": "standard",
            "character_voice_gen": "female_01.wav",
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
        file_url = self.parse_audio_url(response)
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
        file_output_location = f"./language/audio/{language_code}/{filename}.wav"
        if response.status_code == 200:
            with open(file_output_location, "wb") as file:
                file.write(response.content)
                print("File downloaded successfully.")
            return file_output_location
        else:
            print("Failed to download the file.")
            return None
