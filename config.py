"""
Configuration management system for the TTS application.
"""

import configparser
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import logging

logger = logging.getLogger("tts.config")


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class TtsConfig:
    """
    Configuration manager for the TTS application.
    
    Provides a three-layer configuration system:
    1. Command line arguments (highest priority)
    2. Configuration file
    3. Default values (lowest priority)
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'defaults': {
            'voice': '',  # Empty means use system default
            'format': 'aiff',
            'keep_chapters': 'false',
            'jobs': 'auto',
        },
        'directories': {
            'output_dir': 'output',
            'chapter_suffix': '_chapters',
        },
        'audio': {
            'mp3_quality': '0',  # Highest quality
            'cleanup_old_files': 'true',
            'conversion_timeout': '300',  # 5 minutes per chunk
            'merge_timeout': '600',  # 10 minutes for merging
        },
        'processing': {
            'max_retries': '3',
            'retry_delay': '1',  # seconds
            'skip_titlepage': 'true',
            'skip_navigation': 'true',
            'failure_threshold': '0.5',  # 50% failure rate threshold
        },
        'logging': {
            'log_level': 'INFO',
            'enable_colors': 'true',
            'max_log_size': '10485760',  # 10MB
            'log_backups': '5',
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        self.config_file = config_file or self._get_default_config_path()
        self.config = configparser.ConfigParser()
        self._load_defaults()
        self._load_config_file()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        return os.path.join(os.getcwd(), 'config.ini')
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        for section, options in self.DEFAULT_CONFIG.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
    
    def _load_config_file(self) -> None:
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                logger.info(f"Configuration loaded from: {self.config_file}")
            except configparser.Error as e:
                logger.warning(f"Error reading config file {self.config_file}: {e}")
                logger.info("Using default configuration")
        else:
            logger.debug(f"No configuration file found at {self.config_file}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Fallback value if key not found
            
        Returns:
            Configuration value as string
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise ConfigError(f"Configuration key '{section}.{key}' not found")
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Fallback value if key not found
            
        Returns:
            Configuration value as boolean
        """
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            logger.warning(f"Invalid boolean value for {section}.{key}: {e}")
            return fallback
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """
        Get an integer configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Fallback value if key not found
            
        Returns:
            Configuration value as integer
        """
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            logger.warning(f"Invalid integer value for {section}.{key}: {e}")
            return fallback
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """
        Get a float configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Fallback value if key not found
            
        Returns:
            Configuration value as float
        """
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            logger.warning(f"Invalid float value for {section}.{key}: {e}")
            return fallback
    
    def get_defaults_for_cli(self) -> Dict[str, Any]:
        """
        Get default values for command line argument parser.
        
        Returns:
            Dictionary of default values for CLI arguments
        """
        defaults = {}
        
        # Voice setting
        voice = self.get('defaults', 'voice')
        if voice:
            defaults['voice'] = voice
        
        # Format setting
        defaults['format'] = self.get('defaults', 'format')
        
        # Keep chapters setting
        defaults['keep_chapters'] = self.getboolean('defaults', 'keep_chapters')
        
        # Jobs setting
        jobs = self.get('defaults', 'jobs')
        if jobs != 'auto':
            try:
                defaults['jobs'] = int(jobs)
            except ValueError:
                logger.warning(f"Invalid jobs value in config: {jobs}")
        
        return defaults
    
    def create_default_config_file(self, force: bool = False) -> None:
        """
        Create a default configuration file.
        
        Args:
            force: If True, overwrite existing file
        """
        if os.path.exists(self.config_file) and not force:
            logger.info(f"Configuration file already exists: {self.config_file}")
            return
        
        try:
            with open(self.config_file, 'w') as f:
                f.write(self._generate_config_file_content())
            
            logger.info(f"Default configuration file created: {self.config_file}")
            
        except IOError as e:
            raise ConfigError(f"Failed to create config file: {e}")
    
    def _generate_config_file_content(self) -> str:
        """Generate the content for the default configuration file."""
        return '''# TTS Application Configuration
# This file contains default settings for the TTS application.
# Command line arguments will override these settings.

[defaults]
# Default voice for text-to-speech (leave empty for system default)
# Run 'say -v ?' to see available voices
voice = 

# Default output format (aiff or mp3)
format = aiff

# Keep individual chapter files by default
keep_chapters = false

# Number of parallel jobs (auto = CPU cores - 1, or specify a number)
jobs = auto

[directories]
# Base directory for output files
output_dir = output

# Suffix for chapter directories
chapter_suffix = _chapters

[audio]
# MP3 quality (0 = highest, 9 = lowest)
mp3_quality = 0

# Clean up old chapter files before processing
cleanup_old_files = true

# Timeout for individual chunk conversion (seconds)
conversion_timeout = 300

# Timeout for audio merging (seconds)
merge_timeout = 600

[processing]
# Maximum number of retries for failed conversions
max_retries = 3

# Delay between retries (seconds)
retry_delay = 1

# Skip title page during processing
skip_titlepage = true

# Skip navigation files during processing
skip_navigation = true

# Failure threshold (0.5 = 50% of chapters can fail before aborting)
failure_threshold = 0.5

[logging]
# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level = INFO

# Enable colored console output
enable_colors = true

# Maximum log file size in bytes (10MB)
max_log_size = 10485760

# Number of log file backups to keep
log_backups = 5
'''
    
    def validate_config(self) -> None:
        """Validate the current configuration."""
        errors = []
        
        # Validate format
        format_value = self.get('defaults', 'format')
        if format_value not in ['aiff', 'mp3']:
            errors.append(f"Invalid format: {format_value}. Must be 'aiff' or 'mp3'")
        
        # Validate jobs
        jobs_value = self.get('defaults', 'jobs')
        if jobs_value != 'auto':
            try:
                jobs_int = int(jobs_value)
                if jobs_int < 1:
                    errors.append(f"Invalid jobs value: {jobs_value}. Must be 'auto' or a positive integer")
            except ValueError:
                errors.append(f"Invalid jobs value: {jobs_value}. Must be 'auto' or a positive integer")
        
        # Validate timeouts
        conversion_timeout = self.getint('audio', 'conversion_timeout', 300)
        if conversion_timeout < 1:
            errors.append(f"Invalid conversion_timeout: {conversion_timeout}. Must be positive")
        
        merge_timeout = self.getint('audio', 'merge_timeout', 600)
        if merge_timeout < 1:
            errors.append(f"Invalid merge_timeout: {merge_timeout}. Must be positive")
        
        # Validate MP3 quality
        mp3_quality = self.getint('audio', 'mp3_quality', 0)
        if mp3_quality < 0 or mp3_quality > 9:
            errors.append(f"Invalid mp3_quality: {mp3_quality}. Must be between 0 and 9")
        
        # Validate failure threshold
        failure_threshold = self.getfloat('processing', 'failure_threshold', 0.5)
        if failure_threshold < 0 or failure_threshold > 1:
            errors.append(f"Invalid failure_threshold: {failure_threshold}. Must be between 0 and 1")
        
        # Validate log level
        log_level = self.get('logging', 'log_level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            errors.append(f"Invalid log_level: {log_level}. Must be one of: {', '.join(valid_levels)}")
        
        if errors:
            raise ConfigError("Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))
    
    def get_output_directory(self) -> str:
        """Get the configured output directory."""
        return self.get('directories', 'output_dir')
    
    def get_chapter_suffix(self) -> str:
        """Get the configured chapter directory suffix."""
        return self.get('directories', 'chapter_suffix')
    
    def get_conversion_timeout(self) -> int:
        """Get the configured conversion timeout."""
        return self.getint('audio', 'conversion_timeout', 300)
    
    def get_merge_timeout(self) -> int:
        """Get the configured merge timeout."""
        return self.getint('audio', 'merge_timeout', 600)
    
    def get_mp3_quality(self) -> int:
        """Get the configured MP3 quality."""
        return self.getint('audio', 'mp3_quality', 0)
    
    def get_max_retries(self) -> int:
        """Get the configured maximum retries."""
        return self.getint('processing', 'max_retries', 3)
    
    def get_retry_delay(self) -> int:
        """Get the configured retry delay."""
        return self.getint('processing', 'retry_delay', 1)
    
    def get_failure_threshold(self) -> float:
        """Get the configured failure threshold."""
        return self.getfloat('processing', 'failure_threshold', 0.5)
    
    def should_cleanup_old_files(self) -> bool:
        """Check if old files should be cleaned up."""
        return self.getboolean('audio', 'cleanup_old_files', True)
    
    def should_skip_titlepage(self) -> bool:
        """Check if title page should be skipped."""
        return self.getboolean('processing', 'skip_titlepage', True)
    
    def should_skip_navigation(self) -> bool:
        """Check if navigation should be skipped."""
        return self.getboolean('processing', 'skip_navigation', True)


# Global configuration instance
config = TtsConfig() 