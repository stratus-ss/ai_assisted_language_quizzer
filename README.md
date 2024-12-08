# AI Assisted Language Quizzzer

This project is an AI-powered language learning tool that allows users to create custom word lists, generate quizzes, and interact with a chatbot for language practice.

## Project Structure

The project consists of the following main files and directories:

- `language/`: Main package directory
  - `app.py`: Contains the main application logic, including the Flask API, Gradio interface, and core functionality.
  - `modules/`: Directory containing additional modules
    - `FileHandling.py`: Handles file operations and audio generation.
    - `ReviewWords.py`: Responsible for the review and quiz logic.
  - `word_lists/`: Directory containing word lists for different languages
    - `german/`, `spanish/`: Directories for German and Spanish word lists, each containing a `word_list.yaml` file.
- `pyproject.toml`: Defines the project metadata and dependencies using Poetry.

## Setting Up the Project

To set up and run this project, follow these steps:

### 1. Install Poetry

If you haven't already installed Poetry, you can do so by running:
```
bash curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Clone the Repository

Clone the repository to your local machine:
```
bash git clone https://github.com/your-username/ai-assisted-language-quizzzer.git 
cd ai-assisted-language-quizzzer
```

### 3. Install Dependencies

Use Poetry to install the project dependencies:
```
bash poetry install
```

This command will install all the required packages listed in the `pyproject.toml` file, including:

- Python 3.11
- deepl
- gradio
- soundfile
- contractions

### 4. Configure Environment Variables

Set up the following environment variables:

- `DEEPL_API_KEY`: Your DeepL API key (required for translation services)

You can set these variables in your shell or create a `.env` file in the project root.

### 5. Update Configuration Files

Update the following configuration files:

1. In `language/app.py`:
   - Update the `deepl_api` variable with your actual DeepL API key.

2. In `language/modules/FileHandling.py`:
   - Update the `all_talk_url` variable in the `GenerateAudio` class constructor with your All-Talk AI server URL.

### 6. Run the Application

Activate the Poetry virtual environment and start the application:
```
bash poetry shell python language/app.py
```

The application will start on `http://localhost:8002`.

## Key Components

### 1. Word List Management

- Create new words using the Gradio interface
- Save word lists to YAML files in the `word_lists` directory

### 2. Quiz Generation

- Generate quiz questions based on saved word lists
- Include audio and image options for enhanced learning

### 3. Chatbot Integration

- Interact with a chatbot for language practice
- Submit answers and receive feedback

### 4. Language Translation

- Uses DeepL for translating words and phrases
- Supports automatic language detection and translation

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html)
