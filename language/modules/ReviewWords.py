from .FileHandling import HandleFileOperations
import random


class Quiz(HandleFileOperations):
    def __init__(self, filepath: str = None) -> None:
        self.file_path = filepath
        self.word_dict = self.read_file()

    def random_word(self):
        """
        Description:
            Returns a random word from the word dictionary along with its correct answer, audio path, and image path.

        Args:
            self: The instance of the ReviewWords class.

        Returns:
            A tuple containing the random word without its meaning, the correct answer, the audio path, and the image path.
        """
        first_key = list(self.word_dict.keys())[0]
        if len(self.word_dict[first_key]) > 1:
            random_word_key = random.choice(list(self.word_dict[first_key].keys()))
        else:
            random_word_key = next(iter(self.word_dict[first_key]))
        random_word_details = self.word_dict[first_key][random_word_key]
        random_word_without_meaning = {random_word_key: random_word_details}
        correct_answer = random_word_details["meaning"]
        # We want to blank out the meaning so that it is not displayed by the chatbot
        random_word_without_meaning[random_word_key]["meaning"] = ""
        audio_path = random_word_details["audio"]
        image_path = random_word_details["image"]
        return (random_word_without_meaning, correct_answer, audio_path, image_path)


class Review:
    def __init__(self) -> None:
        pass
