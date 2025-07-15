"""
Input validation and security utilities for the TTS application.
"""

import os
import sys
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import ebooklib
from ebooklib import epub


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_epub_file(epub_path: str) -> Tuple[bool, str]:
    """
    Validates an EPUB file for security and integrity.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not os.path.exists(epub_path):
            return False, f"EPUB file not found: {epub_path}"
        
        # Check file size (reasonable limit: 500MB)
        file_size = os.path.getsize(epub_path)
        if file_size > 500 * 1024 * 1024:  # 500MB
            return False, f"EPUB file too large: {file_size / (1024*1024):.1f}MB (max: 500MB)"
        
        if file_size == 0:
            return False, "EPUB file is empty"
        
        # Check if it's a valid ZIP file (EPUB is a ZIP archive)
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_file:
                # Check for required EPUB files
                required_files = ['mimetype', 'META-INF/container.xml']
                zip_contents = zip_file.namelist()
                
                for required_file in required_files:
                    if required_file not in zip_contents:
                        return False, f"Invalid EPUB: missing required file '{required_file}'"
                
                # Check mimetype
                try:
                    mimetype = zip_file.read('mimetype').decode('utf-8').strip()
                    if mimetype != 'application/epub+zip':
                        return False, f"Invalid EPUB mimetype: {mimetype}"
                except Exception:
                    return False, "Invalid EPUB: cannot read mimetype"
                
                # Check for suspicious files or directory traversal
                for filename in zip_contents:
                    if filename.startswith('/') or '..' in filename:
                        return False, f"Suspicious file path in EPUB: {filename}"
                    
                    # Check for excessively long paths
                    if len(filename) > 255:
                        return False, f"File path too long in EPUB: {filename[:50]}..."
                
        except zipfile.BadZipFile:
            return False, "File is not a valid ZIP/EPUB archive"
        
        # Try to parse with ebooklib
        try:
            book = epub.read_epub(epub_path)
            title = book.get_metadata("DC", "title")
            if not title:
                return False, "EPUB appears to be missing title metadata"
        except ebooklib.epub.EpubException as e:
            return False, f"EPUB parsing error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error reading EPUB: {str(e)}"
        
        return True, "EPUB file is valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to prevent directory traversal and other issues.
    
    Args:
        filename: The original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename isn't empty
    if not filename:
        filename = "output"
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename


def validate_output_path(output_path: str) -> Tuple[bool, str]:
    """
    Validates and sanitizes output path.
    
    Args:
        output_path: Desired output path
        
    Returns:
        Tuple of (is_valid, sanitized_path_or_error)
    """
    try:
        # Sanitize the filename part
        output_dir = os.path.dirname(output_path)
        filename = os.path.basename(output_path)
        sanitized_filename = sanitize_filename(filename)
        
        # Reconstruct path
        if output_dir:
            sanitized_path = os.path.join(output_dir, sanitized_filename)
        else:
            sanitized_path = sanitized_filename
        
        # Check if parent directory exists or can be created
        parent_dir = os.path.dirname(os.path.abspath(sanitized_path))
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except OSError as e:
                return False, f"Cannot create output directory: {e}"
        
        # Check write permissions
        test_dir = parent_dir if parent_dir else '.'
        if not os.access(test_dir, os.W_OK):
            return False, f"No write permission for directory: {test_dir}"
        
        return True, sanitized_path
        
    except Exception as e:
        return False, f"Path validation error: {str(e)}"


def validate_voice(voice: Optional[str]) -> Tuple[bool, str]:
    """
    Validates TTS voice name.
    
    Args:
        voice: Voice name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if voice is None:
        return True, "No voice specified (will use system default)"
    
    # Check for obvious injection attempts (allow parentheses and spaces for enhanced voices)
    dangerous_chars = [';', '&', '|', '`', '$', '<', '>', '"', "'"]
    for char in dangerous_chars:
        if char in voice:
            return False, f"Invalid character in voice name: {char}"
    
    # Check length
    if len(voice) > 100:
        return False, "Voice name too long"
    
    # Check for directory traversal
    if '..' in voice or '/' in voice or '\\' in voice:
        return False, "Invalid voice name format"
    
    # Additional check for balanced parentheses (for enhanced voices)
    if voice.count('(') != voice.count(')'):
        return False, "Unbalanced parentheses in voice name"
    
    return True, "Voice name is valid"


def validate_jobs(jobs: Optional[int]) -> Tuple[bool, str]:
    """
    Validates number of parallel jobs.
    
    Args:
        jobs: Number of jobs
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if jobs is None:
        return True, "No job count specified (will use default)"
    
    if not isinstance(jobs, int):
        return False, "Job count must be an integer"
    
    if jobs < 1:
        return False, "Job count must be at least 1"
    
    if jobs > 32:  # Reasonable upper limit
        return False, "Job count too high (maximum: 32)"
    
    return True, "Job count is valid"


def validate_format(format_type: str) -> Tuple[bool, str]:
    """
    Validates output format.
    
    Args:
        format_type: Audio format (aiff or mp3)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_formats = ['aiff', 'mp3']
    
    if format_type not in valid_formats:
        return False, f"Invalid format: {format_type}. Must be one of: {', '.join(valid_formats)}"
    
    return True, "Format is valid"


def check_system_dependencies() -> Tuple[bool, str]:
    """
    Checks if required system dependencies are available.
    
    Returns:
        Tuple of (all_available, error_message)
    """
    import subprocess
    
    # Check for 'say' command (macOS TTS)
    try:
        result = subprocess.run(['say', '-v', '?'], capture_output=True, timeout=5)
        if result.returncode != 0:
            return False, "'say' command not available. This tool requires macOS."
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "'say' command not found. This tool requires macOS."
    
    # Check for 'ffmpeg' (audio processing)
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode != 0:
            return False, "'ffmpeg' not available. Please install ffmpeg."
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "'ffmpeg' not found. Please install ffmpeg (brew install ffmpeg)."
    
    return True, "All system dependencies are available"


def create_safe_output_directory(base_name: str, base_output_dir: str = "output") -> str:
    """
    Creates a safe output directory with proper permissions.
    
    Args:
        base_name: Base name for the output directory
        base_output_dir: Base output directory (default: "output")
        
    Returns:
        Path to the created directory
    """
    # Sanitize the base name
    safe_name = sanitize_filename(base_name)
    
    # Create output directory structure using configured base directory
    output_dir = os.path.join(base_output_dir, safe_name)
    
    try:
        os.makedirs(output_dir, mode=0o755, exist_ok=True)
        
        # Verify the directory was created and is writable
        if not os.path.exists(output_dir):
            raise ValidationError(f"Failed to create output directory: {output_dir}")
        
        if not os.access(output_dir, os.W_OK):
            raise ValidationError(f"Output directory is not writable: {output_dir}")
            
        return output_dir
        
    except OSError as e:
        raise ValidationError(f"Cannot create output directory: {e}") 