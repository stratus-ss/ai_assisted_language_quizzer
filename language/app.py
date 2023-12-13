from modules.FileHandling import HandleFileOperations
from modules.ReviewWords import Quiz
import os
import gradio as gr
import deepl

deepl_api = ""
translator = deepl.Translator(deepl_api)


with gr.Blocks() as demo:
    def get_deepl_language_code(current_language: str = None) -> str:
        """
        Description:
            Calls Deepl to find out which language codes are currently supported.
            If the translation we are looking for, return the code, otherwise
            return nothing
        Args:
            current_language (str, optional): The language to check Deepl against. Defaults to None.
        Returns:
            The language code, if the language is supported. Otherwise return None
        """
        for language in translator.get_target_languages():
            if current_language.lower() in language.name.lower():
                return(language.code)
        return None
        
    def lookup_word(translate_this: str, language_code: str = None, native_language: str = None) -> str:
        """
        Description:
            Uses Deepl to translate the text captured at the text box
        Args:
            translate_this (str): _description_
            language_code (str, optional): _description_. Defaults to None.
            native_language (str, optional): _description_. Defaults to None.
        """
        if native_language:
            result = translator.translate_text(translate_this, target_lang=language_code, source_lang=native_language)
        else:
            # If for some reason we dont have a native language, use deepl's autodetect
            result = translator.translate_text(translate_this, target_lang=language_code)
        return(result.text)
        
    def create_new_word(new_word: str, word_list_name: str, current_language: str, native_language: str):
        """
        Description:
            Adds a new word or phrase to the list indicated by the dropdown in the UI
        Args:
            new_word (str): This is the input from the textbox in the UI
            word_list_name (str): This is the word list that is selected in the dropdown.
                                    It's determined based on the files/folder structure
            current_language (str): The target language you want the translation to appear in
                                       This is a radio button selection in the UI
            native_language (str): The user's native language. This is a radio button selection
                                    in the UI
        Returns:
            Nothing. It writes to a file
        """
        if native_language == "English":
            native_language_code = "EN"
        else:
            native_language_code = get_deepl_language_code(current_language=native_language)
        language_code = get_deepl_language_code(current_language=current_language)
        translated_word = lookup_word(translate_this=new_word, 
                                      language_code=language_code, 
                                      native_language=native_language_code)
        # Instanciate the HandleFileOperations class so we can write the file
        file_ops = HandleFileOperations(filepath=word_lists_info[word_list_name])
        new_word_dict = {current_language: {translated_word: {'meaning': new_word, 
                                                              "audio": None, "image": None, 
                                                              "type": None}}}
        file_ops.write_file(new_word=new_word_dict)

    def quiz(word_list_name: str) -> tuple[str,str]:
        """
    Description:
        Generates a quiz question and answer based on the specified word list.
    Args:
        word_list_name (str): The name of the word list to generate the quiz from.
    Returns:
        Tuple[str, str]: A tuple containing the quiz question and its corresponding answer.
    """
        quiz = Quiz(filepath=word_lists_info[word_list_name])
        test_word, answer = quiz.random_word()
        if "german" in word_list_name.lower():
            question = f"Welche Bedeutung hat das Wort: {next(iter(test_word))}"
        elif "spanish" in word_list_name.lower():
            question = f"¿Cuál es el significado de la palabra: {next(iter(test_word))}"
        else:
            question = f"What is the meaning of the word: {next(iter(test_word))}"
        return question, answer

    def quiz_with_answer(word_list_name: str=None):
        """
        Description:
            This generates a list of responses appropriate for the chatbot object
        Args:
            word_list_name (str): The name of the word list to generate the quiz from.

        Returns:
            list: A list where the first item is null representing the user's history, the 
                  second item is the question to ask the user (bot response)
        """
        if word_list_name != None:
            question, answer = quiz(word_list_name)
            quiz_with_answer.answer = answer
        return [["",question]]

    def check_answer(user_message: str, history: list):
        """
        Description:
            This checks the answer passed in by the user. It is formatted for the chatbox object
        Args:
            user_message (str): A string that the user has typed in
            history (_type_): The previous chatbot history

        Returns:
            list: The updated history to display in the chatbot. Includes user's response and bot's answer
        """
        updated_history = history + [[user_message, None]]
        if user_message in quiz_with_answer.answer:
            bot_response = "Correct! 🤗"
        else:
            bot_response = "Try again 🥶"
        updated_history[-1][1] = bot_response
        return updated_history     
    
    def get_word_list_paths(word_list_folder_name: str = "word_lists") -> str:
        """
        Description:
            This function gets the full path to files on disk so that we don't have
            to rely on relative pathing
        Args:
            word_list_folder_name (str, optional): The folder where all word lists are stored. 
                                                    Defaults to "word_lists".

        Returns:
            A dict with the name of the folder as the key and the full path as the value.
            The folder name is displayed in the drop down menu in the UI
        """
        word_list_dir = os.path.join(os.path.dirname(__file__), word_list_folder_name)
        word_list_paths = {}
        for root, _, files in os.walk(word_list_dir):
            for filename in files:
                if filename == 'word_list.yaml':
                    full_path = os.path.join(root, filename)
                    word_list_name = root.split("/")[-1]
                    word_list_paths[word_list_name] = (full_path)
        return word_list_paths
    
    
    word_lists_info = get_word_list_paths()
    drop_down_choices = []
    for key in word_lists_info:
        drop_down_choices.append(key)
        
    ################## UI Definitions
    # Initialize Gradio components
    with gr.Tab("Word Entry"):
        side_bar = gr.Column(elem_id="sidebar", scale=1, min_width=100, visible=True)
        with side_bar:
            saved_word_lists = gr.Dropdown(label="Saved Word Lists", show_label=True, choices=drop_down_choices)
        with gr.Row():
            target_language = gr.Radio(label="Target language", choices=["German"], scale=0.5)
            word_entry = gr.Textbox(label="Enter New Word Dict", scale=3)  # Create a text box component for user input   
            create_word = gr.Button("Create Word Entry", scale=0.5)
        with gr.Row():
            native_language = gr.Radio(label="Native language", choices=["English"], scale=0.2, value="English")
            gr.Textbox(visible=False, scale=3)
    with gr.Tab("Quiz"):
        with gr.Row():
            with gr.Column():
                saved_word_lists = gr.Dropdown(label="Saved Word Lists", show_label=True, choices=drop_down_choices)
                quiz_button = gr.Button("Next Question", scale=0.5)  # Create a button component to clear the text box
            quiz_question = gr.Chatbot(label="Quiz Question", interactive=True, scale=2)
            
        with gr.Row():
            quiz_answer = gr.Textbox(label="Quiz Answer")  # Create a chatbot component
            quiz_check_button = gr.Button("Submit Answer")
    #
    ################ End UI
    
    ################ Event Handlers
    #
    create_word.click(fn=create_new_word, 
                      inputs=[word_entry ,saved_word_lists, target_language, native_language], 
                      outputs=None)
    word_entry.submit(fn=create_new_word, 
                      inputs=[word_entry ,saved_word_lists, target_language, native_language], 
                      outputs=None)

    quiz_button.click(fn=quiz_with_answer, inputs=saved_word_lists, outputs=quiz_question)
    quiz_check_button.click(fn=check_answer, inputs=[quiz_answer,quiz_question], outputs=quiz_question).then(fn=lambda: '', outputs=quiz_answer)
    

    
if __name__ == "__main__":
    
    demo.launch()