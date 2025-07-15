"""
Shared pytest fixtures and configuration for TTS testing.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest

from config import TtsConfig
from secure_subprocess import SecureSubprocessRunner
from tests.fixtures.epub_samples import (
    create_minimal_epub,
    create_multi_chapter_epub,
    create_complex_formatting_epub,
    create_empty_epub,
    create_malformed_epub,
    create_large_epub
)
from tests.fixtures.audio_samples import (
    create_audio_test_fixtures,
    MockAudioProcessor
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        'defaults': {
            'voice': 'Samantha',
            'format': 'aiff',
            'keep_chapters': 'false',
            'jobs': '4',
        },
        'directories': {
            'output_dir': 'test_output',
            'chapter_suffix': '_test_chapters',
        },
        'audio': {
            'mp3_quality': '5',
            'cleanup_old_files': 'true',
            'conversion_timeout': '60',
            'merge_timeout': '120',
        },
        'processing': {
            'max_retries': '2',
            'retry_delay': '0.5',
            'skip_titlepage': 'true',
            'skip_navigation': 'true',
            'failure_threshold': '0.5',
        },
        'logging': {
            'log_level': 'DEBUG',
            'enable_colors': 'false',
            'max_log_size': '1048576',
            'log_backups': '3',
        }
    }


@pytest.fixture
def mock_config(temp_dir: Path, sample_config: Dict[str, Any]) -> TtsConfig:
    """Create a mock TTS configuration."""
    config_file = temp_dir / "test_config.ini"
    
    # Create a temporary config file
    config_content = []
    for section, options in sample_config.items():
        config_content.append(f"[{section}]")
        for key, value in options.items():
            config_content.append(f"{key} = {value}")
        config_content.append("")
    
    config_file.write_text("\n".join(config_content))
    
    return TtsConfig(str(config_file))


@pytest.fixture
def mock_epub_file(temp_dir: Path) -> Path:
    """Create a mock EPUB file for testing."""
    epub_path = temp_dir / "test_book.epub"
    
    # Create a minimal EPUB structure
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # mimetype file (uncompressed)
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        epub.writestr("META-INF/container.xml", container_xml)
        
        # OEBPS/content.opf
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:identifier id="bookid">test-book-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
        <item id="chapter2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        <itemref idref="chapter1"/>
        <itemref idref="chapter2"/>
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Test Book</text></docTitle>
    <navMap>
        <navPoint id="chapter1" playOrder="1">
            <navLabel><text>Chapter 1</text></navLabel>
            <content src="chapter1.xhtml"/>
        </navPoint>
        <navPoint id="chapter2" playOrder="2">
            <navLabel><text>Chapter 2</text></navLabel>
            <content src="chapter2.xhtml"/>
        </navPoint>
    </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)
        
        # OEBPS/chapter1.xhtml
        chapter1 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 1</title>
</head>
<body>
    <h1>Chapter 1: The Beginning</h1>
    <p>This is the first chapter of our test book. It contains some sample text for testing the TTS conversion system.</p>
    <p>The text should be processed and converted to audio successfully.</p>
</body>
</html>'''
        epub.writestr("OEBPS/chapter1.xhtml", chapter1)
        
        # OEBPS/chapter2.xhtml
        chapter2 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter 2</title>
</head>
<body>
    <h1>Chapter 2: The Middle</h1>
    <p>This is the second chapter with more test content. It should also be processed correctly.</p>
    <p>We test various HTML elements and text formatting here.</p>
</body>
</html>'''
        epub.writestr("OEBPS/chapter2.xhtml", chapter2)
    
    return epub_path


@pytest.fixture
def mock_subprocess_runner():
    """Mock the SecureSubprocessRunner for testing."""
    with patch('secure_subprocess.SecureSubprocessRunner') as mock_runner:
        instance = Mock()
        mock_runner.return_value = instance
        
        # Mock successful 'say' command
        instance.run_command.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        yield instance


@pytest.fixture
def mock_system_dependencies():
    """Mock system dependencies (say, ffmpeg) for testing."""
    with patch('validation.subprocess.run') as mock_run:
        # Mock successful dependency checks
        mock_run.return_value = Mock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_audio_files(temp_dir: Path) -> list[Path]:
    """Create mock audio files for testing."""
    audio_files = []
    for i in range(3):
        audio_file = temp_dir / f"Chapter_{i+1:03d}.aiff"
        # Create empty files (in real tests, these would be actual audio)
        audio_file.write_bytes(b"MOCK_AUDIO_DATA")
        audio_files.append(audio_file)
    return audio_files


@pytest.fixture
def sample_text_chunks() -> list[str]:
    """Sample text chunks for testing."""
    return [
        "This is the first chapter of our test book.",
        "This is the second chapter with more content.",
        "This is the final chapter to conclude our test."
    ]


@pytest.fixture
def mock_args():
    """Mock command line arguments for testing."""
    mock_args = Mock()
    mock_args.voice = "Samantha"
    mock_args.format = "aiff"
    mock_args.jobs = 4
    mock_args.keep_chapters = False
    mock_args.input = "test_book.epub"
    mock_args.output = "test_output.aiff"
    return mock_args


@pytest.fixture
def minimal_epub(temp_dir: Path) -> Path:
    """Create a minimal EPUB file for testing."""
    return create_minimal_epub(temp_dir / "minimal.epub")


@pytest.fixture
def multi_chapter_epub(temp_dir: Path) -> Path:
    """Create a multi-chapter EPUB file for testing."""
    return create_multi_chapter_epub(temp_dir / "multi_chapter.epub", 5)


@pytest.fixture
def complex_formatting_epub(temp_dir: Path) -> Path:
    """Create an EPUB with complex formatting for testing."""
    return create_complex_formatting_epub(temp_dir / "complex.epub")


@pytest.fixture
def empty_epub(temp_dir: Path) -> Path:
    """Create an empty EPUB file for testing."""
    return create_empty_epub(temp_dir / "empty.epub")


@pytest.fixture
def malformed_epub(temp_dir: Path) -> Path:
    """Create a malformed EPUB file for testing."""
    return create_malformed_epub(temp_dir / "malformed.epub")


@pytest.fixture
def large_epub(temp_dir: Path) -> Path:
    """Create a large EPUB file for performance testing."""
    return create_large_epub(temp_dir / "large.epub", 20)


@pytest.fixture
def audio_fixtures(temp_dir: Path) -> dict:
    """Create comprehensive audio test fixtures."""
    return create_audio_test_fixtures(temp_dir / "audio")


@pytest.fixture
def mock_audio_processor(temp_dir: Path) -> MockAudioProcessor:
    """Create a mock audio processor for testing."""
    return MockAudioProcessor(temp_dir / "audio_processor")


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment before and after each test."""
    # Store original environment
    original_env = dict(os.environ)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def log_capture():
    """Capture log output for testing."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger("tts")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    logger.removeHandler(handler)


# Test markers helpers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "filesystem: mark test as requiring filesystem access"
    )
    config.addinivalue_line(
        "markers", "audio: mark test as involving audio processing"
    )
    config.addinivalue_line(
        "markers", "epub: mark test as processing EPUB files"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "security" in item.name.lower():
            item.add_marker(pytest.mark.security)
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow) 