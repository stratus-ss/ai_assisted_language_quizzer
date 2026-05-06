# LingQ Bulk Import

CLI tool for bulk-importing SRT (+ audio) files as LingQ lessons and replacing audio on existing lessons.

## Features

- **Bulk import**: Upload SRT files with matching audio files as LingQ lessons in one command
- **Audio replacement**: Update audio on existing lessons without losing LingQ progress (highlights, word statuses)
- **Course auto-resolution**: Matches course by name (case-insensitive partial match)
- **Interactive preview**: Shows a table of proposed audio→lesson matches before making any changes
- **Dry-run mode**: Preview what will be uploaded/patched without making API calls
- **Scripting support**: Use `--yes` to skip confirmation prompts for automation

## Setup

1. Add your LingQ API key to `.env`:
   ```
   LINGQ_API_KEY=your_key_here
   ```

2. Install dependencies:
   ```bash
   cd language
   source venv/bin/activate
   pip install -r ../requirements.txt
   ```

## Usage

```bash
cd language
source venv/bin/activate
```

### Import lessons

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/srt-and-audio-files \
  --course "Course Name" \
  --language es \
  --dry-run
```

Remove `--dry-run` to actually import.

### Replace audio on existing lessons

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/audio-files \
  --course "Course Name" \
  --language es \
  --replace-audio \
  --dry-run
```

### Scripting / CI mode (non-interactive)

When running in a non-interactive shell (e.g., scripts, CI, cron), use `--yes` to skip confirmation prompts:

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/audio-files \
  --course "Course Name" \
  --replace-audio \
  --yes
```

This also works with `--dry-run` to get machine-readable output without blocking on input.

## Common Patterns

### 1. Naming conventions — what the importer expects

The importer normalizes audio file stems and lesson titles before matching. It:
- Converts underscores (`_`) and hyphens (`-`) to spaces
- Lowercases everything
- Strips trailing language suffixes (e.g., `.es`, `.en`)
- Collapses multiple spaces

| Audio filename | Normalized key | LingQ lesson title | Match? |
|---|---|---|---|
| `Inside Job S01E01.mp3` | `inside job s01e01` | `Inside Job S01E01` | ✅ |
| `Inside_Job_S01E01.es.mp3` | `inside job s01e01` | `Inside Job S01E01` | ✅ |
| `inside-job s01e01.mp3` | `inside job s01e01` | `Inside Job S01E01` | ✅ |
| `Inside_Job_S01E01.es.mp3` | `inside job s01e01` | `Inside Job S01E01` | ✅ |

**Tip:** If your audio files use underscores and a language suffix (e.g., `Inside_Job_S01E01.es.mp3`) and your LingQ lessons use spaces (e.g., `Inside Job S01E01`), the importer will match them correctly. You do **not** need to rename your files.

For import mode, the same normalization is applied when matching SRT stems to lesson titles. If you are creating a new lesson, the title will be the normalized version of your SRT filename (with spaces, not underscores).

### 2. Import a single new lesson (SRT + audio in the same folder)

Put your SRT and audio file in the same directory with matching stems:

```
/path/to/lessons/
  Inside Job S01E07.srt
  Inside Job S01E07.mp3
```

Run the import:

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/lessons \
  --course "Inside Job" \
  --language es
```

The importer will:
1. Parse the SRT text
2. Find the matching audio file (same stem, any supported extension)
3. Create the lesson with the audio attached

### 3. Replace audio on some but not all lessons

If you have a folder with many audio files but only want to replace a subset, move the unwanted files to a subfolder or elsewhere before running:

```bash
# Move files you DON'T want to update
mkdir /path/to/lessons/backups
mv /path/to/lessons/old_audio/*.mp3 /path/to/lessons/backups/

# Now only the files remaining in /path/to/lessons will be matched and patched
python -m scripts.lingq_bulk_import \
  --dir /path/to/lessons \
  --course "Inside Job" \
  --replace-audio \
  --dry-run
```

### 4. Create a lesson first, then attach audio separately

If you want to create the lesson text first and add audio later, run the import in two steps:

```bash
# Step 1: Import SRT only (no audio)
python -m scripts.lingq_bulk_import \
  --dir /path/to/srt-only \
  --course "Inside Job" \
  --language es

# Step 2: Now replace audio on the newly created lesson
# (the importer will match by title now that the lesson exists)
python -m scripts.lingq_bulk_import \
  --dir /path/to/audio \
  --course "Inside Job" \
  --replace-audio
```

### 5. Interactive course selection

When running in an interactive terminal (TTY), the importer will list available courses if there are multiple matches and ask you to confirm:

```bash
$ python -m scripts.lingq_bulk_import \
    --dir /path/to/audio \
    --course "Inside" \
    --replace-audio

Available courses:
  1. Inside Job
  2. Inside Out
Select course number [1-2] or 'q' to quit: 1
Selected: Inside Job
=== Proposed Matches ===
Audio File                               | Lesson Title
----------------------------------------------------------------------------------------------------
Inside_Job_S01E07.es.mp3                   → Inside Job S01E07
Inside_Job_S01E08.es.mp3                   → Inside Job S01E08
Proceed? [y/N]
```

If only one course matches, it auto-confirms immediately.

### 6. Dry-run with scripting (no TTY)

When stdout is not a TTY, use `--yes` to force proceed without prompts:

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/audio \
  --course "Inside Job" \
  --replace-audio \
  --yes
```

For CI/pipeline use, combine with `--dry-run` to get output without side effects:

```bash
python -m scripts.lingq_bulk_import \
  --dir /path/to/audio \
  --course "Inside Job" \
  --replace-audio \
  --dry-run --yes
```

### 7. Import a single lesson with a specific SRT and audio file

When you have one SRT file (and optional audio), use `--lesson` and `--audio` to import it directly without a directory:

```bash
python -m scripts.lingq_bulk_import \
  --course "Inside Job" \
  --lesson "/path/to/Inside Job S01E07.srt" \
  --audio "/path/to/Inside Job S01E07.mp3" \
  --language es
```

The `--audio` flag is optional. If omitted, the importer looks for an audio file with the same stem as the SRT in the same directory as the SRT file.

This is useful for:
- Creating a single new lesson in an existing course
- Backfilling audio for an existing text-only lesson

## Audio matching for `--replace-audio`

The tool scans the target directory for audio files with these extensions: `.mp3`, `.m4a`, `.wav`, `.ogg`. Each file's stem is normalized and looked up against the list of lesson titles from the target course.

**Normalization rules:**
- Lowercase
- Replace `_` and `-` with space
- Strip trailing `.xx` language suffix (e.g., `.es`, `.en`)
- Collapse multiple spaces

A lesson is considered a match when the normalized audio stem equals the normalized lesson title.

Unmatched audio files are listed at the end of the output and do **not** cause a failure — they are simply skipped.

## Import mode

In import mode (the default, without `--replace-audio`), the tool:
1. Scans the directory for `.srt` files
2. For each SRT, optionally finds a matching audio file (same stem, any extension)
3. Parses the SRT text
4. Creates a lesson in the target course via `POST /api/v3/{lang}/lessons/import/`

Audio files must share the same stem as their SRT counterpart:
```
/path/to/
  Inside Job S01E07.srt      # → lesson "Inside Job S01E07"
  Inside Job S01E07.mp3      # → attached as audio
```

If no audio is found, the lesson is created text-only (no audio attached).

## How it works

- Scans directory for `.srt` files (import mode) or audio files (replace-audio mode)
- Matches course by name substring
- Parses SRT text via `SRTParser` from `subtitle_analyzer`
- Creates lessons with `POST /api/v3/{lang}/lessons/import/` or patches audio with `PATCH /api/v3/{lang}/lessons/{id}/`

## Configuration

Edit `src/ai_assisted_language_quizzer/core/subtitle_analyzer/config.yaml` section `lingq_import`:

```yaml
lingq_import:
  api_key_env: "LINGQ_API_KEY"       # env var name (not the key itself)
  default_language: "es"             # two-letter ISO code
  default_status: "private"          # or "shared"
  audio_extensions: [".mp3", ".m4a", ".wav", ".ogg"]
  api_base_url: "https://www.lingq.com/api/v3"
```

## Files

- `src/ai_assisted_language_quizzer/core/lingq_import/client.py` -- `LingQClient` class (API v3 HTTP client)
- `src/ai_assisted_language_quizzer/core/lingq_import/__init__.py` -- Package exports
- `src/ai_assisted_language_quizzer/core/lingq_import/test_harness.py` -- `LingQTestHarness` for API validation
- `lingq-bulk-import` -- CLI entry point

## Testing

The importer includes a test harness (`LingQTestHarness`) to validate API interactions and audio matching without affecting production data.

### Run Test Harness

Use the `--test` flag to run the internal validation suite using the test configuration:

```bash
python -m scripts.lingq_bulk_import \
  --dir data/test_lingq/normalized \
  --course "Your Test Course" \
  --test \
  --dry-run
```

### Smoke Test Results

The pipeline was verified using normalized audio files:
- **Test Data**: 18 normalized `.mp3` files successfully copied to `data/test_lingq/normalized`.
- **Validation**: Dry-run confirmed correct course resolution and audio stem matching logic.
- **Status**: Pass (Dry-run verified; no crashes, correct summary reporting).