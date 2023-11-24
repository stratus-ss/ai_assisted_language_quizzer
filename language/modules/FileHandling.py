#!/usr/bin/python
import ast
import yaml
import logging

class HandleFileOperations:
    def __init__(self, filepath: str = None):
        # Make a list of the keys that are required in the word dict
        # required for input validation before writing the file
        # Assume the dict should be the following format
        # {<word or phrase>: {<meaning>: <val>, <image path>: <val>, <audio path>: <val>, <grammar type>: <val>}}
        self.required_keys = ["meaning", "image", "audio", "type"]
        self.file_path = filepath
    def write_file(self, new_word: dict = None ):
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
        current_dict = self.read_file()
        if not isinstance(current_dict, dict):
            if current_dict is None:
                logging.info("File on disk is empty... working with empty list")
            else:
                logging.error(f"Cannot add {current_dict} to config file. It is not a dict")
                exit(1)
        for language_name in new_word:
            for key in new_word[language_name]:
                if not all(value in new_word[language_name][key] for value in self.required_keys):
                    logging.error("Attempted to insert a word/phrase but it's missing required keys")
                    logging.error(f"Expected keys are {self.required_keys}")
                    return
        if current_dict is not None:
            for language_name in new_word:
                for key in new_word[language_name]:
                    if not key in current_dict:
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
        return(yaml.load(word_dict, Loader=yaml.FullLoader))
        # read the file and return the results
        