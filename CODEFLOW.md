# AI Assisted Language Quizzer - Code Flow Documentation

This document provides comprehensive code flow diagrams using Mermaid -->help you understand how the project works. Each section covers a major workflow with detailed steps.

---

## Table of Contents

1. [Subtitle Word Frequency Analysis Pipeline](#1-subtitle-word-frequency-analysis-pipeline)
2. [Translation Workflow](#2-translation-workflow)
3. [Anki Integration Flows](#3-anki-integration-flows)
4. [Audio Generation Flow](#4-audio-generation-flow)
5. [Complete Data Flow Summary](#5-complete-data-flow-summary)
6. [Key Classes and Responsibilities](#6-key-classes-and-responsibilities)
7. [Configuration & Environment](#7-configuration--environment)
8. [Common Workflows](#8-common-workflows)
9. [Error Handling Summary](#9-error-handling-summary)
This is the core workflow that extracts vocabulary from subtitle files.

### 1.1 Main Entry Point Flow

```mermaid
flowchart TD
    A["PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency"] --> B["parse_arguments()"]
    B --> C["SubtitleFrequencyAnalyzer.analyze()"]
    
    B --> D["CLI Arguments"]
    D --> D1["--subtitles-dir"]
    D --> D2["--curate"]
    D --> D3["--translate"]
    D --> D4["--target-lang"]
    D --> D5["--source-lang"]
    D --> D6["--add-stopwords"]
    D --> D7["--remove-stopwords"]
    D --> D8["--min-freq"]
    
    C --> C1["Step 1: Parse Subtitles"]
    C1 --> C2["Step 2: Process & Filter Words"]
    C2 --> C3["Step 3: Filter Stopwords"]
    C3 --> C4["Step 4: Analyze Frequencies"]
    C4 --> C4a["Step 4a: Lemmatization (optional)"]
    C4a --> C5["Step 5: Apply Threshold"]
    C5 --> C5a["Step 5a: LLM Curation (optional)"]
    C5a --> C6["Step 6: Generate Reports"]
```

### 1.2 Analysis Pipeline Steps

```mermaid
flowchart TD
    subgraph STEP1 ["STEP 1: Parse Subtitles"]
        A1["SRTParser.parse_directory(subtitles_dir)"] --> A2["For each *.srt file"]
        A2 --> A3["Extract text lines<br/>Skip: timestamps, indices"]
        A3 --> A4["Output: Dict[filename, List[text_lines]]"]
    end
    
    subgraph STEP2 ["STEP 2: Process Words"]
        B1["WordProcessor.process_lines()"] --> B2["tokenize_text()"]
        B2 --> B3["normalize_word()"]
        B3 --> B4["Keep if len >= min_word_length"]
        B4 --> B5["Output: List[str] normalized words"]
    end
    
    subgraph STEP3 ["STEP 3: Filter Stopwords"]
        C1["StopWordManager.filter_words()"] --> C2["Compare against stopwords_*.txt"]
        C2 --> C3["Remove common words, character names"]
        C3 --> C4["Output: filtered_words"]
    end
    
    subgraph STEP4 ["STEP 4: Analyze Frequencies"]
        D1["FrequencyAnalyzer.analyze()"] --> D2["Counter(words)"]
        D2 --> D3["Calculate: total, unique, avg, median"]
        D3 --> D4["Output: {word: frequency}"]
    end
    
    STEP1 --> STEP2
    STEP2 --> STEP3
    STEP3 --> STEP4
```

### 1.3 Lemmatization (Optional)

```mermaid
flowchart LR
    subgraph Input ["Input: surface forms"]
        A1["habia: 45"]
        A2["ire: 12"]
        A3["fue: 55"]
        A4["voy: 20"]
    end
    
    subgraph Process ["Lemmatization Process"]
        P1["For each word:<br/>spacy.doc(word).lemma_"]
        P1 --> P2["Group by lemma"]
    end
    
    subgraph Output ["Output: LemmaGroups"]
        O1["ir: total_freq=75<br/>forms: {fue:55, voy:20}"]
        O2["haber: total_freq=75<br/>forms: {habia:75}"]
    end
    
    Input --> Process
    Process --> Output
    
    note1["Example:<br/>habia - haber<br/>fui - ir<br/>voy - ir"]:::note
    classDef note fill:#f9f,stroke:#333
```

### 1.4 LLM Curation (Optional --curate flag)

```mermaid
flowchart TD
    A["LLMCurator.curate(lemma_groups)"] --> B["Batch Processing"]
    B --> C["40 lemma groups per API call"]
    
    C --> D["Build JSON payload"]
    D --> E["POST -->Minimax API"]
    E --> F["Parse JSON response"]
    
    F --> G["CuratedWord output"]
    G --> G1["keep: true/false"]
    G --> G2["best_form: recommended form"]
    G --> G3["difficulty: A1/A2/B1/B2"]
    G --> G4["note: max 5-word hint"]
    G --> G5["translation: pronoun-aware"]
    
    F -->|On Failure| H["Use defaults<br/>keep=True, difficulty=A2"]
    
    note2["Spanish verbs get subject pronouns:<br/>se - I know<br/>van - they go<br/>dijo - he said"]:::note
    classDef note fill:#f9f,stroke:#333
```

### 1.5 Complete Analysis Pipeline (Detailed)

```mermaid
flowchart TD
    subgraph parse ["Parse Subtitles"]
        P1["SRTParser.parse_directory()"] --> P2["*.srt files in subtitles/"]
        P2 --> P3["Skip timestamps & indices"]
        P3 --> P4["Return Dict[filename, text_lines]"]
    end
    
    subgraph process ["Process & Filter"]
        PF1["WordProcessor.process_lines()"] --> PF2["Tokenize, normalize, filter"]
        PF2 --> PF3["StopWordManager.filter_words()"]
        PF3 --> PF4["filtered_words"]
    end
    
    subgraph analyze ["Analyze Frequencies"]
        AF1["FrequencyAnalyzer.analyze()"] --> AF2["Counter(words)"]
        AF2 --> AF3["Get statistics"]
        AF3 --> AF4["unique_words count"]
    end
    
    subgraph lemma ["Lemmatization (optional)"]
        L1{"Config:<br/>lemmatization.enabled?"} -->|Yes| L2["LemmaGrouper.group_by_lemma()"]
        L1 -->|No| L3["Skip"]
        L2 --> L4["Group conjugations under lemma"]
        L4 --> L5["{lemma: LemmaGroup}"]
    end
    
    subgraph threshold ["Apply Threshold"]
        T1["FrequencyAnalyzer.calculate_smart_threshold()"]
        T1 --> T2{"threshold_mode?"}
        T2 -->|"auto"| T3["Smart calculation:<br/>small dataset - lower threshold<br/>large dataset - higher threshold"]
        T2 -->|"manual"| T4["Use --min-freq value"]
        T3 --> T5["filtered_frequencies, threshold"]
        T4 --> T5
    end
    
    subgraph curation ["LLM Curation (optional)"]
        C1{"--curate flag<br/>or config enabled?"} -->|No| C2["Skip -->reports"]
        C1 -->|Yes| C3["LLMCurator.curate()"]
        C3 --> C4["Filter: keep=True only"]
        C4 --> C5["CuratedWord list"]
    end
    
    subgraph reports ["Generate Reports"]
        R1["ReportGenerator.generate_all_reports()"]
        R1 --> R2["anki_import_words.txt"]
        R1 --> R3["word_frequency_report.csv"]
        R1 --> R4["word_frequency_summary.md"]
    end
    
    parse --> process
    process --> analyze
    analyze --> lemma
    lemma --> threshold
    threshold --> curation
    curation --> reports
```

---

## 2. Translation Workflow

### 2.1 DeepL Translation Flow

```mermaid
flowchart TD
    A["translate_word_list()"] --> B["get_deepl_translator()"]
    
    B --> B1["Check DEEPL_API_KEY env var"]
    B1 --> B2{"API Key exists?"}
    B2 -->|No| B3["Exit with error"]
    B2 -->|Yes| B4["Create deepl.Translator()"]
    B4 --> B5["Return translator instance"]
    
    A --> C["For each word in list"]
    C --> D["PronounContextHelper.contextualize()"]
    D --> D1["Add subject pronoun for verbs"]
    D1 --> D2["se - I know"]
    
    D2 --> E["translator.translate_text()"]
    E --> F["Write output"]
    
    F --> F1["ANKI: palabra\\ttraduccion"]
    F --> F2["CSV: original,translation"]
    F --> F3["Plain: palabra - traduccion"]
    
    note3["PronounContextHelper adds subject pronouns<br/>for contextual DeepL translation"]:::note
    classDef note fill:#9f9,stroke:#333
```

### 2.2 Integrated vs Standalone Translation

```mermaid
flowchart LR
    subgraph Integrated ["Integrated (--translate flag)"]
        I1["After analysis completes"]
        I2["translate_wordlist() called"]
        I3["Filtered frequencies as input"]
    end
    
    subgraph Standalone ["Standalone translate_wordlist.py"]
        S1["Called directly by user"]
        S2["PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist"]
        S3["User-provided word list file"]
    end
    
    Integrated --> O["Output: translated_words.txt"]
    Standalone --> O
```

---

## 3. Anki Integration Flows

### 3.1 Add Audio -->Anki Notes

```mermaid
flowchart TD
    A["PYTHONPATH=src python -m ai_assisted_language_quizzer.anki_tools.add_audio_to_anki"] --> B["parse_arguments()"]
    
    B --> B1["--audio-dir<br/>--word-list<br/>--deck<br/>--search-field<br/>--audio-field"]
    
    B1 --> C["AnkiConnector(url)"]
    C --> C1["Connect -->localhost:8765"]
    C1 --> C2["Version check (must be 6)"]
    
    C2 --> D["AudioAttacher class"]
    
    D --> D1["find_audio_file(word)"]
    D1 --> D1a["Look in audio_dir for:<br/>word.wav, word.mp3,<br/>word_female_02.wav"]
    D1a --> D1b["Return Optional[Path]"]
    
    D --> D2["attach_audio_to_note(word, note_id)"]
    D2 --> D2a["anki.store_media_file()"]
    D2a --> D2b["anki.update_note_fields()"]
    
    D --> D3["find_notes_missing_audio()"]
    D3 --> D3a["anki.find_notes(query)"]
    D3a --> D3b["anki.notes_info() - check audio field"]
    D3b --> D3c["Return (note_id, word) list"]
```

### 3.2 Add Words -->Anki Notes

```mermaid
flowchart TD
    A["process_file()"] --> B["Read tab-separated file"]
    
    B --> C["For each line"]
    C --> D["Split on tab"]
    D --> E["Extract 4th column"]
    E --> F["Parse: word (type)"]
    F --> F1["original_word = 'palabra'"]
    F1 --> F2["word_type = '(noun)'"]
    
    F2 --> G["lookup_word(original_word, target_lang, source_lang)"]
    G --> G1["DeepL translation"]
    G1 --> H["Reconstruct field"]
    H --> H1["'palabra, translated_word (noun)'"]
    
    H1 --> I["Write modified line"]
```

### 3.3 AnkiConnect API Operations

```mermaid
sequenceDiagram
    participant Python
    participant AnkiConnect
    participant Anki
    
    Python->>AnkiConnect: invoke("version")
    AnkiConnect->>Anki: Check version
    Anki-->>Python: version number
    
    Python->>AnkiConnect: store_media_file(filename, data)
    AnkiConnect->>Anki: Save -->media collection
    Anki-->>Python: filename
    
    Python->>AnkiConnect: findNotes(query)
    AnkiConnect->>Anki: Search deck
    Anki-->>Python: note_ids list
    
    Python->>AnkiConnect: notesInfo(notes)
    AnkiConnect->>Anki: Get note details
    Anki-->>Python: notes info
    
    Python->>AnkiConnect: updateNoteFields(note_id, fields)
    AnkiConnect->>Anki: Modify note
    Anki-->>Python: success
```

---

## 4. Audio Generation Flow

### 4.1 Main Audio Generation Flow

```mermaid
flowchart TD
    A["PYTHONPATH=src python -m ai_assisted_language_quizzer.audio.download_from_alltalk"] --> B["parse_arguments()"]
    
    B --> B1["--word-list<br/>--language<br/>--voice<br/>--server<br/>--delay<br/>--output-dir"]
    
    B1 --> C["Validate word list file"]
    C -->|Exists| D["parse_voice_range()"]
    C -->|Not found| E["Exit with error"]
    
    D --> D1["'female_03-female_07'"]
    D1 --> D2["[female_03, female_04, ..., female_07]"]
    
    D2 --> F["For each voice"]
    F --> G["For each word"]
    
    G --> H["GenerateAudio.request_audio_generation()"]
    H --> H1["Validate: if not sentence - return empty"]
    
    H1 --> H2["Create ASCII filename for API"]
    H2 --> H2a["remove_special_chars_for_filename()"]
    H2a --> H2b["'despues' - 'despues'"]
    
    H2 --> H3["Build request payload"]
    H3 --> H3a["text_input: ORIGINAL word (keep accents!)"]
    H3a --> H3b["character_voice_gen: voice.wav"]
    H3b --> H3c["output_file_name: ASCII-safe"]
    
    H3 --> H4["POST -->AllTalk server"]
    H4 --> H5["Parse response for output_file_url"]
    
    H5 --> I["retrieve_audio_file()"]
    I --> I1["GET download from file_url"]
    I1 --> I2["Save .wav with preserved accents"]
    I2 --> I2a["clean_filename_keep_accents()"]
    I2a --> I2b["'despues.wav' (accent preserved)"]
```

### 4.2 Filename Handling Detail

```mermaid
flowchart TD
    A["Two different filename functions for different purposes"]
    
    B["For AllTalk API"] -->B1["remove_special_chars_for_filename()"]
    B1 -->B2["Requires ASCII-only output_file_name"]
    B2 -->B3["Removes: accents, special chars, spaces"]
    B3 -->B4["Example: 'despues' - 'despues'"]
    
    C["For final filename"] -->C1["clean_filename_keep_accents()"]
    C1 -->C2["Human-readable filenames"]
    C2 -->C3["Removes: / \\ : * ? \" < > |"]
    C3 -->C4["Keeps: a, e, i, o, u"]
    C4 -->C4b["Example: 'despues.wav'"]
    
    note4["IMPORTANT: Original word with accents is sent to TTS for proper pronunciation. Only the filename is ASCII-fied."]:::note
    
```

---

## 5. Complete Data Flow Summary

```mermaid
flowchart LR
    subgraph Input ["Input"]
        S["subtitles/*.srt"]
    end
    
    subgraph Core ["subtitle_word_frequency.py"]
        A["SubtitleFrequencyAnalyzer.analyze()"]
        
        A --> A1["SRTParser"]
        A --> A2["WordProcessor"]
        A --> A3["StopWordManager"]
        A --> A4["FrequencyAnalyzer"]
        A --> A5["LemmaGrouper (optional)"]
        A --> A6["LLMCurator (optional)"]
        A --> A7["ReportGenerator"]
    end
    
    subgraph Output ["data/output/"]
        O1["anki_import_words.txt"]
        O2["word_frequency_report.csv"]
        O3["word_frequency_summary.md"]
    end
    
    subgraph Translate ["translate_wordlist.py"]
        T["DeepL Translation"]
        T --> T1["translated_words.txt"]
    end
    
    subgraph Audio ["download_from_alltalk.py"]
        AU["AllTalk TTS API"]
        AU --> AU1["audio/*.wav"]
    end
    
    subgraph Anki ["anki_tools/"]
        AN["AnkiConnect API"]
        AN --> AN1["Cards with audio"]
    end
    
    Input --> Core
    Core --> Output
    Output --> T
    Output --> AU
    T1 --> AN
    AU1 --> AN
```

---

## 6. Key Classes and Responsibilities

```mermaid
flowchart TB
    subgraph subtitle_analyzer ["subtitle_analyzer/"]
        SA1["SRTParser<br/>Parse .srt files"]
        SA2["WordProcessor<br/>Tokenize, normalize"]
        SA3["StopWordManager<br/>Load, filter stopwords"]
        SA4["FrequencyAnalyzer<br/>Count frequencies"]
        SA5["LemmaGrouper<br/>Group conjugations (spaCy)"]
        SA6["LLMCurator<br/>Score via Minimax API"]
        SA7["ReportGenerator<br/>Generate CSV, TXT, MD"]
        SA8["translator<br/>DeepL functions"]
    end
    
    subgraph anki_tools ["anki_tools/"]
        AN1["AnkiConnector<br/>Connect -->AnkiConnect API"]
        AN2["AudioAttacher<br/>Attach audio files"]
    end
    
    subgraph audio ["audio/"]
        AU1["GenerateAudio<br/>AllTalk TTS API"]
    end
    
    ```

---

## 7. Configuration & Environment

```mermaid
flowchart TD
    subgraph Environment ["Environment Variables (.env)"]
        E1["DEEPL_API_KEY"]
        E2["MINIMAX_API_KEY (optional)"]
        E3["ALLTALK_URL (optional)"]
    end
    
    subgraph Config ["config.yaml"]
        C1["lemmatization.enabled: false"]
        C1 --> C1a["language_model: es_core_news_sm"]
        
        C2["llm_curation.enabled: false"]
        C2 --> C2a["model: minimax-m2.5"]
        C2 --> C2b["batch_size: 40"]
        C2 --> C2c["learner_level: A2-B1"]
        
        C3["translation.enabled: false"]
        C3 --> C3a["source_lang: ES"]
        C3 --> C3b["target_lang: EN-US"]
        
        C4["paths"]
        C4 --> C4a["subtitles_directory: ../subtitles"]
        C4 --> C4b["output_directory: ../../data/output"]
        
        C5["analysis"]
        C5 --> C5a["target_words: 500"]
        C5 --> C5b["min_word_length: 2"]
        C5 --> C5c["threshold_mode: auto"]
    end
```

---

## 8. Common Workflows

### 8.1 Complete Workflow (Recommended)

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Anki
    
    User->>CLI: Place .srt files in subtitles/
    User->>CLI: PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --curate --translate
    CLI->>CLI: Parse subtitles
    CLI->>CLI: Process & filter words
    CLI->>CLI: Lemmatization (optional)
    CLI->>CLI: LLM curation (optional)
    CLI->>CLI: Generate reports
    Note over CLI: data/output/anki_import_words.txt<br/>data/output/translated_words.txt
    
    User->>Anki: File - Import<br/>Select translated_words.txt
    User->>Anki: Configure: Basic, Tab-separated
    User->>Anki: Import
    
    User->>CLI: PYTHONPATH=src python -m ai_assisted_language_quizzer.anki_tools.add_audio_to_anki<br/>-a ./audio -w word_list.txt -d "Deck"
    CLI->>Anki: Attach audio via AnkiConnect
```

### 8.2 Step-by-Step Workflow

```mermaid
flowchart LR
    A["1. Extract vocabulary<br/>PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency"] --> B["2. Translate<br/>PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist"]
    B --> C["3. Generate audio (optional)<br/>PYTHONPATH=src python -m ai_assisted_language_quizzer.audio.download_from_alltalk"]
    C --> D["4. Import -->Anki manually"]
    D --> E["5. Attach audio (optional)<br/>PYTHONPATH=src python -m ai_assisted_language_quizzer.anki_tools.add_audio_to_anki"]
```

---

## 9. Error Handling Summary

```mermaid
flowchart TD
    subgraph SRTParser ["SRTParser"]
        S1["Logs errors, continues with other files"]
        S2["Raises: FileNotFoundError, UnicodeDecodeError"]
    end
    
    subgraph WordProcessor ["WordProcessor"]
        W1["No explicit error handling"]
        W2["Relies on regex and length filtering"]
    end
    
    subgraph FrequencyAnalyzer ["FrequencyAnalyzer"]
        F1["Returns empty if no words analyzed"]
        F2["calculate_smart_threshold handles 0 unique words"]
    end
    
    subgraph LLMCurator ["LLMCurator"]
        L1["On API failure: uses defaults (keep=True, A2)"]
        L2["Retries once, then fails gracefully"]
    end
    
    subgraph AnkiConnector ["AnkiConnector"]
        A1["Raises exceptions on connection failures"]
        A2["Version check ensures compatibility"]
    end
    
    subgraph AudioAttacher ["AudioAttacher"]
        AU1["Silently skips missing audio files"]
        AU2["Reports count of successful attachments"]
    end
    
    subgraph DeepL ["DeepL Translation"]
        D1["On error: marks word as '[ERROR]'"]
        D2["Continues processing remaining words"]
    end
```

---

*For more details on any specific component, refer -->the inline documentation in each module or run any script with `--help` for usage information.*