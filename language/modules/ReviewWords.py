from .FileHandling import HandleFileOperations
import random
import yaml

class Quiz(HandleFileOperations):
    def __init__(self, filepath: str = None) -> None:
        self.file_path = filepath
        self.word_dict = self.read_file()
    
    def random_word(self):
        # We don't want to ask the same question twice... how do we prevent this?
        # Mutate the dict?
        first_key = list(self.word_dict.keys())[0]
        random_word_index = random.randrange(1, (len(self.word_dict[first_key])))
        counter = 1
        for word in self.word_dict[first_key]:
            if counter == random_word_index:
                random_word_without_meaning = {word: self.word_dict[first_key][word]}
                correct_answer = self.word_dict[first_key][word]['meaning']
                random_word_without_meaning[word]['meaning'] = ''
                return(random_word_without_meaning, correct_answer)
            else:
                counter +=1
    
    
class Review:
    def __init__(self) -> None:
        pass

