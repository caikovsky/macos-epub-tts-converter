# EPUB to Audiobook Converter (Parallel Edition)

> **Note:** This tool is designed for **macOS only** as it relies on the built-in `say` command for speech synthesis. It will not work on Windows or Linux.

A robust, secure, and extensively tested command-line tool to rapidly convert EPUB files into audiobooks using parallel processing and the built-in text-to-speech engine on macOS. Features comprehensive input validation, structured logging, error handling, security measures, and a complete testing framework.

## ✨ Key Features

### 🔒 **Security & Validation**
- **System Dependencies Check**: Validates that `say` and `ffmpeg` are available
- **Input Validation**: Comprehensive EPUB file validation (structure, integrity, security)
- **Argument Sanitization**: Prevents command injection and validates all user inputs
- **Secure Processing**: All subprocess calls are sandboxed with timeout protection
- **Enhanced Voice Support**: Supports complex voice names like "Zoe (Enhanced)" with security validation

### ⚡ **High-Performance Processing**
- **EPUB Parsing**: Parses and validates the EPUB file structure
- **Content Extraction**: Splits content into chapters with HTML cleaning
- **Parallel Processing**: Uses multiple CPU cores for simultaneous audio conversion
- **Progress Tracking**: Real-time progress reporting with detailed logging
- **Audio Merging**: Uses `ffmpeg` to merge all segments into a final audiobook
- **Fixed MP3 Conversion**: Proper AIFF-to-AIFF merging before MP3 conversion (resolves ffmpeg errors)

### 📊 **Comprehensive Logging**
- **System Information**: Logs platform, Python version, and system specs
- **Process Tracking**: Detailed logs of each conversion step
- **Error Handling**: Structured error messages with context
- **Log Files**: Timestamped logs stored in `logs/` directory with automatic rotation

### 🧪 **Testing Framework**
- **Comprehensive Test Suite**: Unit tests for all major components
- **Security Testing**: Command injection and directory traversal protection tests
- **Mock Systems**: Subprocess execution and dependency testing
- **Coverage Reporting**: HTML and XML coverage reports with 80% minimum threshold
- **Performance Testing**: Framework ready for benchmarks and load testing

### ⚙️ **Configuration System**
- **INI-based Configuration**: Flexible configuration with `config.ini`
- **CLI Override**: Command-line arguments override configuration settings
- **Validation**: Comprehensive configuration validation with helpful error messages
- **Defaults**: Sensible defaults with easy customization

## Requirements

*   **macOS:** This tool depends on the `say` command, which is exclusive to macOS.
*   **Python 3.8+:** Should be pre-installed on modern macOS versions.
*   **ffmpeg:** A free, powerful audio/video utility. This is required for merging the audio chunks.

## Installation

### Quick Install

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
    git clone https://github.com/caikovsky/macos-epub-tts-converter.git
    cd macos-epub-tts-converter
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

### Development Installation

For development and testing:

```bash
# Install with testing dependencies (already included in requirements.txt)
pip install -r requirements.txt

# Verify installation
python3 main.py --help
```

## Configuration

### Configuration File

Create a `config.ini` file for custom settings:

```bash
# Copy the example configuration
cp config.ini.example config.ini

# Edit your preferences
nano config.ini
```

Example configuration:
```ini
[defaults]
# Default voice for text-to-speech
voice = Zoe (Enhanced)

# Default output format (aiff or mp3)
format = mp3

# Keep individual chapter files
keep_chapters = true

# Number of parallel jobs (auto = CPU cores - 1)
jobs = auto

[audio]
# MP3 quality (0 = highest, 9 = lowest)
mp3_quality = 5

# Timeout for audio merging (seconds)
merge_timeout = 600

[processing]
# Maximum number of retries for failed conversions
max_retries = 3

# Failure threshold (0.5 = 50% of chapters can fail before aborting)
failure_threshold = 0.5
```

### Voice Selection

List available voices:
```bash
say -v '?'
```

Enhanced voices (higher quality):
- `Zoe (Enhanced)`
- `Ava (Premium)`
- `Samantha (Enhanced)`

## Usage

### Basic Usage

```bash
python3 main.py --input /path/to/your/book.epub --output MyBook.mp3 --format mp3
```

### Command Line Arguments

*   `-i`, `--input`: (Required) Path to the input EPUB file
*   `-o`, `--output`: (Required) Base filename for the output audio file (e.g., `MyAudiobook.mp3`)
*   `-v`, `--voice`: (Optional) Voice to use (overrides config file)
*   `-j`, `--jobs`: (Optional) Number of parallel jobs (overrides config file)
*   `-f`, `--format`: (Optional) Output format: `aiff` or `mp3` (overrides config file)
*   `--keep-chapters`: (Optional) Save individual chapter files (overrides config file)
*   `--config-file`: (Optional) Path to custom configuration file

### Advanced Examples

```bash
# Convert with enhanced voice and multiple cores
python3 main.py \
    -i "O_Cortiço.epub" \
    -o "O_Cortiço.mp3" \
    -v "Zoe (Enhanced)" \
    -j 8 \
    --format mp3 \
    --keep-chapters

# Use custom configuration file
python3 main.py -i "book.epub" -o "book.mp3" --config-file /path/to/custom.ini

# Convert to high-quality AIFF (lossless)
python3 main.py -i "book.epub" -o "book.aiff" --format aiff

# Quick MP3 conversion with default settings
python3 main.py -i "book.epub" -o "book.mp3"
```

## Output Structure

Using `--output MyBook.mp3` will create the following structure:
```
output/
└── MyBook/
    ├── MyBook.mp3              # Final audiobook
    └── MyBook_chapters/        # Individual chapters (if --keep-chapters)
        ├── Chapter_001.aiff
        ├── Chapter_002.aiff
        └── ...

logs/
├── tts_20240715_143022.log     # Timestamped log files
├── tts_20240715_143118.log
└── ...
```

## Additional Tools

### Text Extraction Tool

Extract EPUB content to plain text files for review:

```bash
# Extract all chapters from an EPUB to separate text files
python3 extract_text.py -i "MyBook.epub" -o "MyBook_text"
```

This creates a `text_exports/MyBook_text/` directory with individual `.txt` files for each chapter.

### Test Runner

Run the comprehensive test suite:

```bash
# Run all tests
python3 run_tests.py all

# Run only unit tests
python3 run_tests.py unit

# Run security tests
python3 run_tests.py security

# Run with coverage report
python3 run_tests.py all --html

# Run specific test categories
python3 run_tests.py unit --verbose
python3 run_tests.py integration --exitfirst
```

## System Information Display

The application shows system information on startup:
```
15:53:21 | INFO | System Information:
15:53:21 | INFO |   Platform: Darwin 24.5.0
15:53:21 | INFO |   Python: 3.13.2
15:53:21 | INFO |   CPU cores: 10
15:53:21 | INFO |   Working directory: /Users/user/tts
```

## Security Features

This application includes comprehensive security measures:

### 🔒 **Input Validation**
- **EPUB Integrity**: Validates ZIP structure, mimetype, and file paths
- **Path Sanitization**: Prevents directory traversal attacks
- **Argument Validation**: Sanitizes all command-line arguments
- **File Size Limits**: Prevents processing of excessively large files

### 🛡️ **Command Injection Prevention**
- **Voice Parameter Validation**: Blocks dangerous characters in voice names while supporting enhanced voices
- **Subprocess Sandboxing**: Only allows whitelisted commands (`say`, `ffmpeg`)
- **Argument Sanitization**: Removes dangerous characters from all inputs
- **Timeout Protection**: All operations have timeout limits

### 📊 **Logging & Monitoring**
- **Timestamped Logs**: All operations logged with precise timestamps
- **Structured Logging**: Organized log format with module/function/line info
- **Error Context**: Detailed error messages with context information
- **Log Rotation**: Automatic log file rotation (10MB limit, 5 backups)

## Testing

### Running Tests

```bash
# Run all tests with coverage
python3 run_tests.py all --html

# Run specific test categories
python3 run_tests.py unit        # Unit tests only
python3 run_tests.py security    # Security tests only
python3 run_tests.py performance # Performance tests only

# Run tests in parallel
python3 run_tests.py all -n 4

# Run with verbose output
python3 run_tests.py unit --verbose
```

### Test Coverage

The test suite includes:
- **Unit Tests**: Individual component testing
- **Security Tests**: Command injection, directory traversal protection
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load testing and benchmarking
- **Mock Systems**: Subprocess and dependency testing

Coverage reports are generated in `htmlcov/index.html` when using `--html`.

## Development

### Project Structure

```
├── main.py                 # Main application entry point
├── audio_handler.py        # Audio processing and merging
├── config.py              # Configuration management
├── validation.py           # Input validation and security
├── secure_subprocess.py    # Secure subprocess execution
├── epub_handler.py         # EPUB file processing
├── logging_config.py       # Logging configuration
├── extract_text.py         # Text extraction tool
├── run_tests.py           # Test runner script
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── fixtures/          # Test fixtures
│   └── conftest.py        # Pytest configuration
├── config.ini.example     # Example configuration
└── requirements.txt       # Python dependencies
```

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Write tests**: Add tests for new functionality
4. **Run tests**: `python3 run_tests.py all`
5. **Commit changes**: `git commit -m "feat: description"`
6. **Push to branch**: `git push origin feature/my-feature`
7. **Create Pull Request**

### Code Quality

- **Type hints**: All functions have comprehensive type hints
- **Security**: All inputs are validated and sanitized
- **Testing**: Comprehensive test coverage with pytest
- **Documentation**: All modules and functions are documented
- **Logging**: Structured logging throughout the application

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
- Use only alphanumeric characters, spaces, and parentheses in voice names
- Run `say -v '?'` to see available voices
- Enhanced voices like "Zoe (Enhanced)" are supported

**MP3 Conversion Issues**
```bash
ERROR | Audio processing failed: Error during audio merging
```
- This was fixed in recent versions - ensure you're using the latest version
- The system now properly merges AIFF files before MP3 conversion

**Configuration Errors**
```bash
ERROR | Configuration error: Invalid format: wav
```
- Check your `config.ini` file for invalid values
- Supported formats are `aiff` and `mp3`
- Use `python3 main.py --help` to see valid options

### Performance Issues

**Slow Processing**
- Increase parallel jobs: `-j 8` (adjust based on your CPU cores)
- Use AIFF format for faster processing (no MP3 conversion)
- Check system resources and available memory

**Memory Issues**
- Reduce parallel jobs: `-j 2`
- Process smaller EPUB files
- Close other applications to free memory

### Log Files

Check the `logs/` directory for detailed troubleshooting information:
- Each run creates a timestamped log file
- Logs include system information, processing steps, and error details
- Log files are automatically rotated to prevent disk space issues

Enable debug logging by setting `log_level = DEBUG` in `config.ini`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for macOS using the native `say` command
- Uses `ffmpeg` for audio processing and merging
- Comprehensive testing framework with pytest
- Security-focused design with input validation and sanitization



