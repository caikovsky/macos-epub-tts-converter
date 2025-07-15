# EPUB to Audiobook Converter (Parallel Edition)

> **Note:** This tool is designed for **macOS only** as it relies on the built-in `say` command for speech synthesis. It will not work on Windows or Linux.

A robust, secure command-line tool to rapidly convert EPUB files into audiobooks by using parallel processing and the built-in text-to-speech engine on macOS. Features comprehensive input validation, structured logging, error handling, and security measures.

## How It Works

This tool is optimized for speed, security, and reliability:

### 🔒 **Security & Validation**
1. **System Dependencies Check**: Validates that `say` and `ffmpeg` are available
2. **Input Validation**: Comprehensive EPUB file validation (structure, integrity, security)
3. **Argument Sanitization**: Prevents command injection and validates all user inputs
4. **Secure Processing**: All subprocess calls are sandboxed with timeout protection

### ⚡ **High-Performance Processing**
1. **EPUB Parsing**: Parses and validates the EPUB file structure
2. **Content Extraction**: Splits content into chapters with HTML cleaning
3. **Parallel Processing**: Uses multiple CPU cores for simultaneous audio conversion
4. **Progress Tracking**: Real-time progress reporting with detailed logging
5. **Audio Merging**: Uses `ffmpeg` to merge all segments into a final audiobook

### 📊 **Comprehensive Logging**
- **System Information**: Logs platform, Python version, and system specs
- **Process Tracking**: Detailed logs of each conversion step
- **Error Handling**: Structured error messages with context
- **Log Files**: Timestamped logs stored in `logs/` directory with automatic rotation

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

Run the script from your terminal. The application will automatically validate your inputs, log system information, and organize all output files.

### Output Structure

Using `--output MyBook.mp3` will create the following structure:
```
output/
└── MyBook/
    ├── MyBook.mp3
    └── MyBook_chapters/
        ├── Chapter_001.aiff
        └── Chapter_002.aiff
        ...

logs/
├── tts_20240715_143022.log
├── tts_20240715_143118.log
└── ...
```

### System Information Display

The application now shows system information on startup:
```
15:53:21 | INFO | System Information:
15:53:21 | INFO |   Platform: Darwin 24.5.0
15:53:21 | INFO |   Python: 3.13.2
15:53:21 | INFO |   CPU cores: 10
15:53:21 | INFO |   Working directory: /Users/user/tts
```

### Command

```bash
python3 main.py --input /path/to/your/book.epub --output MyBook.mp3 --format mp3
```

### Arguments

*   `-i`, `--input`: (Required) The path to the input EPUB file.
*   `-o`, `--output`: (Required) The base filename for the final output audio file (e.g., `MyAudiobook.mp3`). This will also be used as the name for the book's output folder.
*   `-v`, `--voice`: (Optional) The voice to use. Run `say -v '?'` to see available voices.
*   `-j`, `--jobs`: (Optional) The number of parallel jobs to run. Defaults to the number of CPU cores minus one.
*   `-f`, '--format`: (Optional) The final audio format. Choices are `aiff` or `mp3`. Defaults to `aiff`.
*   `--keep-chapters`: (Optional) If included, this flag will save the individual audio for each chapter.

## Text Extraction Tool

The application now includes a standalone text extraction tool for converting EPUB files to plain text:

```bash
# Extract all chapters from an EPUB to separate text files
python3 extract_text.py -i "MyBook.epub" -o "MyBook_text"
```

This creates a `text_exports/MyBook_text/` directory with individual `.txt` files for each chapter.

## Enhanced Error Handling

The application now provides detailed error messages and validation:

```bash
# Example: Invalid EPUB file
python3 main.py -i "invalid.epub" -o "output.mp3"
# Output: ERROR | EPUB validation failed: File is not a valid ZIP/EPUB archive

# Example: Security validation
python3 main.py -i "book.epub" -o "output.mp3" -v "Voice;rm -rf /"
# Output: ERROR | Voice validation failed: Invalid character in voice name: ;
```

### Examples

```bash
# Convert a book to MP3 using the default settings
python3 main.py -i "MyBook.epub" -o "MyBook.mp3" --format mp3
```

```bash
# Convert with premium voice, multiple cores, and keep chapter files
python3 main.py \
    -i "O_Cortiço.epub" \
    -o "O_Cortiço.mp3" \
    -v "Zoe (Enhanced)" \
    -j 7 \
    --format mp3 \
    --keep-chapters
```

```bash
# Extract text chapters for review before conversion
python3 extract_text.py -i "MyBook.epub" -o "MyBook_chapters"
```

## Security Features

This application includes comprehensive security measures:

### 🔒 **Input Validation**
- **EPUB Integrity**: Validates ZIP structure, mimetype, and file paths
- **Path Sanitization**: Prevents directory traversal attacks
- **Argument Validation**: Sanitizes all command-line arguments
- **File Size Limits**: Prevents processing of excessively large files

### 🛡️ **Command Injection Prevention**
- **Voice Parameter Validation**: Blocks dangerous characters in voice names
- **Subprocess Sandboxing**: Only allows whitelisted commands (`say`, `ffmpeg`)
- **Argument Sanitization**: Removes dangerous characters from all inputs
- **Timeout Protection**: All operations have timeout limits

### 📊 **Logging & Monitoring**
- **Timestamped Logs**: All operations logged with precise timestamps
- **Structured Logging**: Organized log format with module/function/line info
- **Error Context**: Detailed error messages with context information
- **Log Rotation**: Automatic log file rotation (10MB limit, 5 backups)

## Troubleshooting

### Common Issues

**EPUB Validation Failed**
```bash
ERROR | EPUB validation failed: File is not a valid ZIP/EPUB archive
```
- Ensure the file is a valid EPUB format
- Check file permissions and corruption

**System Dependencies Missing**
```bash
ERROR | System dependency check failed: 'ffmpeg' not found
```
- Install ffmpeg: `brew install ffmpeg`
- Verify macOS has the `say` command

**Voice Validation Failed**
```bash
ERROR | Voice validation failed: Invalid character in voice name
```
- Use only alphanumeric characters and spaces in voice names
- Run `say -v '?'` to see available voices

### Log Files

Check the `logs/` directory for detailed troubleshooting information:
- Each run creates a timestamped log file
- Logs include system information, processing steps, and error details
- Log files are automatically rotated to prevent disk space issues



