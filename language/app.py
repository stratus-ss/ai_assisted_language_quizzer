import contextlib
import os
import yaml
import string
import random
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import deepl
import soundfile
import contractions
from dotenv import load_dotenv


from modules.FileHandling import HandleFileOperations, GenerateAudio
from modules.ReviewWords import Quiz

load_dotenv()
deepl_api = os.getenv("DEEPL_API_KEY")
translator = deepl.Translator(deepl_api)
print(sys.version)
print(f"The current gradio version is: {gr.__version__}")

gr.Button

with gr.Blocks() as demo:

    session_id = gr.State("")
    drop_down_choices = []
    all_languages_list = gr.State([])
    path_to_audio_file = gr.State("")
    path_to_image_file = gr.State("")
    # language_to_quiz = gr.State('')

    def create_new_word(
        new_word: str,
        session_id: gr.State,
        current_language: str,
        native_language: str,
        generate_audio: bool = True,
        generate_image: bool = False,
    ):
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
        audio_path = None
        image_path = None
        if native_language == "English":
            native_language_code = "EN"
        else:
            native_language_code = get_deepl_language_code(
                current_language=native_language
            )
        language_code = get_deepl_language_code(current_language=current_language)
        translated_word = lookup_word(
            translate_this=new_word,
            language_code=language_code,
            native_language=native_language_code,
        )
        word_lists_info = return_file_path(
            session_id=session_id["gsession_id"], language_directory=current_language
        )
        # Instanciate the HandleFileOperations class so we can write the file
        file_ops = HandleFileOperations(filepath=word_lists_info)

        if generate_audio:
            audio_ops = GenerateAudio()
            audio_path = audio_ops.request_audio_generation(
                word_language=language_code, sentence=translated_word
            )
        if generate_image:
            # call the generate image, should return file path..
            # this could be complicated
            pass
        new_word_dict = {
            current_language: {
                translated_word: {
                    "meaning": new_word,
                    "audio": audio_path,
                    "image": image_path,
                    "type": None,
                }
            }
        }
        file_ops.write_file(new_word=new_word_dict)

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
        user_answer = contractions.fix(user_message).lower()
        correct_answer = contractions.fix(quiz_with_answer.answer.lower())
        print(user_answer)
        print(correct_answer)
        if user_answer in correct_answer:
            bot_response = "Correct! 🤗"
        else:
            bot_response = "Try again 🥶"
        updated_history[-1][1] = bot_response
        return updated_history

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
                return language.code
        return None

    def get_cookies(request: gr.Request, session_id: gr.State) -> dict:
        """
        Description:
            Returns the current session ID stored in cookies.
        Args:
            request (gr.Request): The request object containing the cookies.
            session_id (gr.State): The state variable containing the session ID.

        Returns:
            (dict): A dictionary containing the current session ID.

        """
        current_session = request.cookies["gsession_id"]
        return {"gsession_id": current_session}

    def lookup_word(
        translate_this: str, language_code: str = None, native_language: str = None
    ) -> str:
        """
        Description:
            Uses Deepl to translate the text captured at the text box
        Args:
            translate_this (str): _description_
            language_code (str, optional): _description_. Defaults to None.
            native_language (str, optional): _description_. Defaults to None.
        """
        if native_language:
            result = translator.translate_text(
                translate_this, target_lang=language_code, source_lang=native_language
            )
        else:
            # If for some reason we dont have a native language, use deepl's autodetect
            result = translator.translate_text(
                translate_this, target_lang=language_code
            )
        return result.text

    def load_word_list(drop_down_selection, file_name, all_languages_list: gr.State):
        """
        Description:
            Loads the word list for a selected dropdown option.
        Args:
            drop_down_selection: The selected option from the dropdown.
            file_name: The name of the file to load the word list from.
            all_languages_list (gr.State): The state variable containing the list of all languages in the list.
        Returns:
            The word list for the selected dropdown option.
        """

        for entry in all_languages_list:
            if entry == drop_down_selection:
                return entry

    def quiz(
        word_list_name: str, session_id: gr.State, language: str
    ) -> tuple[str, str]:
        """
        Description:
            Generates a quiz question and answer based on the specified word list.
        Args:
            word_list_name (str): The name of the word list to generate the quiz from.
        Returns:
            Tuple[str, str]: A tuple containing the quiz question and its corresponding answer.
        """
        quiz = Quiz(
            filepath=return_file_path(
                session_id=session_id["gsession_id"], language_directory=language
            )
        )
        test_word, answer, audio_path, image_path = quiz.random_word()
        if "german" in word_list_name.lower():
            question = f"Welche Bedeutung hat das Wort: {next(iter(test_word))}"
        elif "spanish" in word_list_name.lower():
            question = f"¿Cuál es el significado de la palabra: {next(iter(test_word))}"
        else:
            question = f"What is the meaning of the word: {next(iter(test_word))}"
        return question, answer, audio_path, image_path

    def quiz_with_answer(
        word_list_name: str = None, session_id: gr.State = None, language: str = None
    ):
        """
        Description:
            Generates a quiz question with its corresponding answer, audio path, and image path based on the specified word list name, session ID, and language.

        Args:
            word_list_name: The name of the word list to generate the quiz from.
            session_id: The ID of the session.
            language: The language to use for the quiz.

        Returns:
            A list containing the quiz question, audio path, and image path.
        """
        if word_list_name is not None:
            question, answer, audio_path, image_path = quiz(
                word_list_name, session_id=session_id, language=language
            )
            image_path = "" if image_path is None else image_path
            quiz_with_answer.answer = answer
        return [[["", question]], audio_path, image_path]

    def return_file_path(
        session_id: str,
        language_directory: str,
        word_list_folder_name: str = "word_lists",
    ) -> str:
        """
        Description:
            This function gets the full path to files on disk so that we don't have
            to rely on relative pathing
        Args:
            word_list_folder_name (str, optional): The folder where all previous word_lists are stored.
                                                    Defaults to "word_lists".
            session_id (str): The session ID as retrieved from the browser
        Returns:
            (str): The full path to the word list file
        """
        word_list_dir = os.path.join(os.path.dirname(__file__), word_list_folder_name)
        file_name = f"{session_id}.yaml"
        return word_list_dir + os.sep + language_directory + os.sep + file_name

    def return_word_list(word_list: gr.Dropdown, session_id: gr.State, language: str):
        """
        Description:
            Returns the word list stored in a YAML file.
        Args:
            word_list (gr.Dropdown): The dropdown widget used to select a word list.
            session_id (gr.State): The state variable containing the session ID.
        Returns:
            (dict): The contents of the word list file as a dictionary.
        """
        world_list_path = return_file_path(
            session_id=session_id["gsession_id"], language_directory=language
        )
        try:
            with open(world_list_path) as f:
                file_contents = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print(f"Could not find file {world_list_path}")
            return None
        return file_contents

    def populate_drop_down(all_words_list: gr.State) -> gr.Dropdown:
        """
        Description:
            Populates a dropdown widget with choices based on the provided list of words.
        Args:
            all_words_list (gr.State): The state variable containing the list of all words.
        Returns:
            gr.Dropdown: A dropdown widget populated with choices based on the list of words.
                        Overwrites the current gradio object in the outputs= section of the
                        gradio function call
        """
        if all_words_list is None:
            return gr.Dropdown(label="Saved Word List", show_label=True, choices=None)
        # Only update the drop_down_choices when the file exists on disk
        with contextlib.suppress(FileNotFoundError):
            for language in all_words_list:
                if language not in drop_down_choices:
                    drop_down_choices.append(language)
        return gr.Dropdown(
            label="Saved Word Lists", show_label=True, choices=drop_down_choices
        )

    def play_audio(file_name: gr.State):
        """
        Description:
            Plays the audio file specified by the file name and returns the sample rate and data.

        Args:
            file_name: The name of the audio file to be played.

        Returns:
            A tuple containing the sample rate and data of the audio file.
        """
        data, samplerate = soundfile.read(file_name)
        return (samplerate, data)

    def unhide_audio():
        return gr.Audio(scale=0.25, visible=True)

    ################## UI Definitions
    # Initialize Gradio components
    with gr.Tab("Word Entry"):
        side_bar = gr.Column(elem_id="sidebar", scale=1, min_width=100, visible=True)
        # with side_bar:
        #     saved_word_lists_dropdown = gr.Dropdown(label="Saved Word Lists", show_label=True, choices=drop_down_choices)
        with gr.Row():
            target_language = gr.Radio(
                label="Target language", choices=["German", "Spanish"], scale=0.5
            )
            add_audio = gr.Checkbox(label="Generate Audio")
            word_entry = gr.Textbox(
                label="Enter New Word Dict", scale=3
            )  # Create a text box component for user input
            create_word = gr.Button("Create Word Entry", scale=0.5)
        with gr.Row():
            native_language = gr.Radio(
                label="Native language", choices=["English"], scale=0.2, value="English"
            )
            gr.Textbox(visible=False, scale=3)
    with gr.Tab("Quiz"):
        with gr.Row():
            with gr.Column():
                quiz_language = gr.Radio(
                    label="Quiz language", choices=["German", "Spanish"], scale=0.5
                )
                quiz_button = gr.Button(
                    "Next Question", scale=0.5
                )  # Create a button component to clear the text box
                audio_player = gr.Audio(scale=0.25, visible=False)
            quiz_question = gr.Chatbot(label="Quiz Question", scale=2.5)
        with gr.Row():
            quiz_answer = gr.Textbox(label="Quiz Answer")  # Create a chatbot component
            submit_answer_btn = gr.Button("Submit Answer")
    #
    ################ End UI

    ################ Event Handlers
    #

    ### Tab 1 Handlers

    create_word.click(fn=get_cookies, outputs=session_id).then(
        fn=create_new_word,
        inputs=[word_entry, session_id, target_language, native_language, add_audio],
        outputs=None,
    )
    word_entry.submit(fn=get_cookies, outputs=session_id).then(
        fn=create_new_word,
        inputs=[word_entry, session_id, target_language, native_language, add_audio],
        outputs=None,
    )

    # create_word.click(fn=get_cookies, inputs=saved_word_lists_dropdown, outputs=session_id).then(fn=create_new_word,
    #                   inputs=[word_entry ,session_id, target_language, native_language, add_audio],
    #                   outputs=None)
    # word_entry.submit(fn=get_cookies, inputs=saved_word_lists_dropdown, outputs=session_id).then(fn=create_new_word,
    #                   inputs=[word_entry ,session_id, target_language, native_language, add_audio],
    #                   outputs=None)

    ### Tab 2 Handlers
    quiz_language.select(fn=get_cookies, inputs=quiz_language, outputs=session_id).then(
        fn=return_word_list,
        inputs=[quiz_language, session_id, quiz_language],
        outputs=all_languages_list,
    )
    quiz_button.click(
        fn=quiz_with_answer,
        inputs=[quiz_language, session_id, quiz_language],
        outputs=[quiz_question, path_to_audio_file, path_to_image_file],
    ).then(fn=unhide_audio, outputs=audio_player).then(
        fn=play_audio, inputs=path_to_audio_file, outputs=audio_player
    )
    submit_answer_btn.click(
        fn=check_answer, inputs=[quiz_answer, quiz_question], outputs=quiz_question
    ).then(fn=lambda: "", outputs=quiz_answer)
    quiz_answer.submit(
        fn=check_answer, inputs=[quiz_answer, quiz_question], outputs=quiz_question
    ).then(fn=lambda: "", outputs=quiz_answer)

demo.queue()
CUSTOM_PATH = "/gradio"
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CookieSetterMiddleware:
    """
    Description:
        Middleware class to set a cookie on the response for Gradio app requests.
        This middleware sets a cookie with the key 'gsession_id' and a random string value on the response for requests made to the Gradio app.
    Args:
        request (Request): The incoming request object.
        call_next: The next middleware callable in the stack.
    Returns:
        Response: The response object.
    """

    # Define the asynchronous callable middleware.
    # It receives the next middleware callable as a parameter, which it calls later.
    async def __call__(self, request: Request, call_next):
        global session_id
        # Call the next middleware in the stack and store the response.
        response = await call_next(request)
        # Check if the requested URL path starts with '/gradio'.
        # If it does, it means the request was made to the Gradio app.
        if request.url.path.startswith("/gradio"):
            # Set a cookie on the response.
            # The key of the cookie is 'gsession_id', and the value is a random string.
            try:
                request.cookies["gsession_id"]
            # Only set the cookie if it doesn't exist
            except Exception:
                response.set_cookie(
                    key="gsession_id",
                    value="".join(
                        random.choice(string.ascii_letters + string.digits)
                        for _ in range(16)
                    ),
                )
        # Return the response.
        return response


app.middleware("http")(CookieSetterMiddleware())

app = gr.mount_gradio_app(app, demo, path=CUSTOM_PATH)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
