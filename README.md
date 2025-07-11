# EPUB to Audiobook Converter (Parallel Edition)

> **Note:** This tool is designed for **macOS only** as it relies on the built-in `say` command for speech synthesis. It will not work on Windows or Linux.

A command-line tool to rapidly convert EPUB files into audiobooks by using parallel processing and the built-in text-to-speech engine on macOS.

## How It Works

This script is optimized for speed and leverages multiple CPU cores:
1.  It parses the `.epub` file and splits the content into separate chunks (usually one per chapter).
2.  It calculates the optimal number of parallel workers to use (typically one less than your total CPU cores).
3.  It assigns each text chunk to a worker, which converts it to an audio segment *simultaneously*. A progress bar will show the status of the chunk conversions.
4.  Once all chunks are converted, it uses **`ffmpeg`** to instantly merge all the audio segments into a single, final audiobook file.

## Requirements

*   **macOS:** This tool depends on the `say` command, which is exclusive to macOS.
*   **Python 3:** Should be pre-installed on modern macOS versions.
*   **ffmpeg:** A free, powerful audio/video utility. This is required for merging the audio chunks.

## Quickstart

1.  **Install Homebrew (if you don't have it):**
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

2.  **Install ffmpeg:**
    ```bash
    brew install ffmpeg
    ```

3.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

4.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

5.  **Install the required Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from your terminal. All output files will be automatically placed in a dedicated folder for the book inside the `output/` directory.

For example, using `--output MyBook.mp3` will create the following structure:
```
output/
└── MyBook/
    ├── MyBook.mp3
    └── MyBook_chapters/
        ├── Chapter_001.aiff
        ...
```

### Command

```bash
python3 tts.py --input /path/to/your/book.epub --output MyBook.mp3 --format mp3
```

### Arguments

*   `-i`, `--input`: (Required) The path to the input EPUB file.
*   `-o`, `--output`: (Required) The base filename for the final output audio file (e.g., `MyAudiobook.mp3`). This will also be used as the name for the book's output folder.
*   `-v`, `--voice`: (Optional) The voice to use. Run `say -v '?'` to see available voices.
*   `-j`, `--jobs`: (Optional) The number of parallel jobs to run. Defaults to the number of CPU cores minus one.
*   `-f`, '--format`: (Optional) The final audio format. Choices are `aiff` or `mp3`. Defaults to `aiff`.
*   `--keep-chapters`: (Optional) If included, this flag will save the individual audio for each chapter.

### Examples

```bash
# Convert a book to MP3 using the default settings.
python3 tts.py -i "MyBook.epub" -o "MyBook.mp3" --format mp3
```

```bash
# Convert a book using the premium "Zoe (enhanced)" voice, 7 cores, and keep the chapter files.
python3 tts.py \
    -i "O_Cortiço.epub" \
    -o "O_Cortiço.mp3" \
    -v "Zoe (enhanced)" \
    -j 7 \
    --format mp3 \
    --keep-chapters
```


