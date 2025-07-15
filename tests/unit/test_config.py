"""
Unit tests for the configuration system.
"""

import tempfile
from pathlib import Path
import pytest

from config import TtsConfig, ConfigError


@pytest.mark.unit
class TestTtsConfig:
    """Test cases for TtsConfig class."""
    
    def test_default_config_initialization(self):
        """Test that default configuration is loaded correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            config = TtsConfig(str(config_path))
            
            # Test default values
            assert config.get('defaults', 'format') == 'aiff'
            assert config.get('defaults', 'keep_chapters') == 'false'
            assert config.get('defaults', 'jobs') == 'auto'
            assert config.get('audio', 'mp3_quality') == '0'
            assert config.get('processing', 'max_retries') == '3'
    
    def test_config_file_loading(self, temp_dir):
        """Test loading configuration from file."""
        config_file = temp_dir / "test_config.ini"
        config_content = """[defaults]
voice = TestVoice
format = mp3
keep_chapters = true

[audio]
mp3_quality = 5
"""
        config_file.write_text(config_content)
        
        config = TtsConfig(str(config_file))
        
        # Test loaded values
        assert config.get('defaults', 'voice') == 'TestVoice'
        assert config.get('defaults', 'format') == 'mp3'
        assert config.get('defaults', 'keep_chapters') == 'true'
        assert config.get('audio', 'mp3_quality') == '5'
    
    def test_config_validation_valid(self, mock_config):
        """Test configuration validation with valid values."""
        # Should not raise any exception
        mock_config.validate_config()
    
    def test_config_validation_invalid_format(self, temp_dir):
        """Test configuration validation with invalid format."""
        config_file = temp_dir / "test_config.ini"
        config_content = """[defaults]
format = invalid_format
"""
        config_file.write_text(config_content)
        
        config = TtsConfig(str(config_file))
        
        with pytest.raises(ConfigError) as exc_info:
            config.validate_config()
        
        assert "Invalid format" in str(exc_info.value)
    
    def test_config_validation_invalid_jobs(self, temp_dir):
        """Test configuration validation with invalid jobs value."""
        config_file = temp_dir / "test_config.ini"
        config_content = """[defaults]
jobs = -1
"""
        config_file.write_text(config_content)
        
        config = TtsConfig(str(config_file))
        
        with pytest.raises(ConfigError) as exc_info:
            config.validate_config()
        
        assert "Invalid jobs value" in str(exc_info.value)
    
    def test_config_validation_invalid_mp3_quality(self, temp_dir):
        """Test configuration validation with invalid MP3 quality."""
        config_file = temp_dir / "test_config.ini"
        config_content = """[audio]
mp3_quality = 15
"""
        config_file.write_text(config_content)
        
        config = TtsConfig(str(config_file))
        
        with pytest.raises(ConfigError) as exc_info:
            config.validate_config()
        
        assert "Invalid mp3_quality" in str(exc_info.value)
    
    def test_get_output_directory(self, mock_config):
        """Test getting output directory."""
        assert mock_config.get_output_directory() == 'test_output'
    
    def test_get_chapter_suffix(self, mock_config):
        """Test getting chapter suffix."""
        assert mock_config.get_chapter_suffix() == '_test_chapters'
    
    def test_get_mp3_quality(self, mock_config):
        """Test getting MP3 quality."""
        assert mock_config.get_mp3_quality() == 5
    
    def test_get_max_retries(self, mock_config):
        """Test getting maximum retries."""
        assert mock_config.get_max_retries() == 2
    
    def test_get_conversion_timeout(self, mock_config):
        """Test getting conversion timeout."""
        assert mock_config.get_conversion_timeout() == 60
    
    def test_get_merge_timeout(self, mock_config):
        """Test getting merge timeout."""
        assert mock_config.get_merge_timeout() == 120
    
    def test_get_failure_threshold(self, mock_config):
        """Test getting failure threshold."""
        assert mock_config.get_failure_threshold() == 0.5
    
    def test_should_cleanup_old_files(self, mock_config):
        """Test checking if old files should be cleaned up."""
        assert mock_config.should_cleanup_old_files() is True
    
    def test_should_skip_titlepage(self, mock_config):
        """Test checking if title page should be skipped."""
        assert mock_config.should_skip_titlepage() is True
    
    def test_config_get_with_fallback(self, mock_config):
        """Test getting configuration value with fallback."""
        # Test existing key
        assert mock_config.get('defaults', 'voice') == 'Samantha'
        
        # Test non-existing key with fallback
        assert mock_config.get('nonexistent', 'key', 'fallback') == 'fallback'
    
    def test_config_get_defaults_for_cli(self, mock_config):
        """Test getting defaults for CLI."""
        defaults = mock_config.get_defaults_for_cli()
        
        assert 'voice' in defaults
        assert 'format' in defaults
        assert 'jobs' in defaults
        assert defaults['voice'] == 'Samantha'
        assert defaults['format'] == 'aiff'
    
    def test_config_nonexistent_key_error(self, mock_config):
        """Test getting configuration value for non-existent key without fallback."""
        with pytest.raises(ConfigError):
            mock_config.get('nonexistent', 'key') 