"""
Audio sample generators and mock audio files for testing.
"""

import wave
import struct
from pathlib import Path
from typing import List, Optional


def create_mock_aiff_file(output_path: Path, duration_seconds: float = 5.0, sample_rate: int = 22050) -> Path:
    """Create a mock AIFF file with silence for testing."""
    # Generate silence data
    num_samples = int(duration_seconds * sample_rate)
    silence_data = b'\x00\x00' * num_samples  # 16-bit silence
    
    # Create AIFF file manually (simplified)
    with open(output_path, 'wb') as f:
        # FORM chunk
        f.write(b'FORM')
        f.write(struct.pack('>L', 46 + len(silence_data)))  # File size - 8
        f.write(b'AIFF')
        
        # COMM chunk
        f.write(b'COMM')
        f.write(struct.pack('>L', 18))  # COMM chunk size
        f.write(struct.pack('>H', 1))   # Number of channels (mono)
        f.write(struct.pack('>L', num_samples))  # Number of sample frames
        f.write(struct.pack('>H', 16))  # Sample size (16-bit)
        f.write(struct.pack('>H', 0x400E))  # Sample rate (22050 Hz in IEEE 754 format)
        f.write(b'\xAC\x44\x00\x00\x00\x00\x00\x00')  # Rest of sample rate
        
        # SSND chunk
        f.write(b'SSND')
        f.write(struct.pack('>L', 8 + len(silence_data)))  # SSND chunk size
        f.write(struct.pack('>L', 0))   # Offset
        f.write(struct.pack('>L', 0))   # Block size
        f.write(silence_data)
    
    return output_path


def create_mock_wav_file(output_path: Path, duration_seconds: float = 5.0, sample_rate: int = 22050) -> Path:
    """Create a mock WAV file with silence for testing."""
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Generate silence
        num_samples = int(duration_seconds * sample_rate)
        silence_data = b'\x00\x00' * num_samples
        wav_file.writeframes(silence_data)
    
    return output_path


def create_mock_chapter_files(output_dir: Path, num_chapters: int = 3, duration_each: float = 2.0) -> List[Path]:
    """Create multiple mock chapter audio files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    chapter_files = []
    for i in range(1, num_chapters + 1):
        chapter_file = output_dir / f"Chapter_{i:03d}.aiff"
        create_mock_aiff_file(chapter_file, duration_each)
        chapter_files.append(chapter_file)
    
    return chapter_files


def create_mock_corrupted_audio_file(output_path: Path) -> Path:
    """Create a corrupted audio file for error testing."""
    with open(output_path, 'wb') as f:
        # Write invalid audio data
        f.write(b'INVALID_AUDIO_DATA' * 100)
    
    return output_path


def create_mock_empty_audio_file(output_path: Path) -> Path:
    """Create an empty audio file for edge case testing."""
    output_path.touch()
    return output_path


def create_mock_large_audio_file(output_path: Path, duration_seconds: float = 300.0) -> Path:
    """Create a large mock audio file for performance testing."""
    return create_mock_aiff_file(output_path, duration_seconds)


def create_mock_mp3_file(output_path: Path, duration_seconds: float = 5.0) -> Path:
    """Create a mock MP3 file (simplified header only)."""
    # Create a minimal MP3 file with ID3 header
    id3_header = b'ID3\x03\x00\x00\x00\x00\x00\x00'
    
    # MP3 frame header for 44.1kHz, 128kbps, stereo
    mp3_frame_header = b'\xFF\xFB\x90\x00'
    
    # Calculate approximate file size for duration
    bitrate = 128000  # 128 kbps
    file_size = int((duration_seconds * bitrate) / 8)
    
    with open(output_path, 'wb') as f:
        f.write(id3_header)
        f.write(mp3_frame_header)
        # Fill with pseudo-random data
        for i in range(file_size // 1024):
            f.write(bytes([i % 256] * 1024))
    
    return output_path


class MockAudioProcessor:
    """Mock audio processor for testing without actual audio processing."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.processed_files = []
    
    def process_text_to_audio(self, text: str, output_path: Path, voice: Optional[str] = None) -> bool:
        """Mock text-to-audio conversion."""
        # Create a mock audio file
        create_mock_aiff_file(output_path, duration_seconds=len(text) * 0.1)
        self.processed_files.append(output_path)
        return True
    
    def merge_audio_files(self, input_files: List[Path], output_path: Path) -> bool:
        """Mock audio merging."""
        # Calculate total duration
        total_duration = len(input_files) * 5.0  # Assume 5 seconds per file
        create_mock_aiff_file(output_path, duration_seconds=total_duration)
        return True
    
    def convert_to_mp3(self, input_path: Path, output_path: Path, quality: int = 5) -> bool:
        """Mock MP3 conversion."""
        create_mock_mp3_file(output_path, duration_seconds=5.0)
        return True
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """Mock getting audio duration."""
        # Return a mock duration based on file size
        if audio_path.exists():
            file_size = audio_path.stat().st_size
            return file_size / 10000  # Mock calculation
        return 0.0
    
    def validate_audio_file(self, audio_path: Path) -> bool:
        """Mock audio file validation."""
        if not audio_path.exists():
            return False
        
        # Check if it's a recognized audio file
        suffix = audio_path.suffix.lower()
        return suffix in ['.aiff', '.wav', '.mp3']


def create_audio_test_fixtures(temp_dir: Path) -> dict:
    """Create a complete set of audio test fixtures."""
    fixtures = {}
    
    # Basic audio files
    fixtures['minimal_aiff'] = create_mock_aiff_file(temp_dir / "minimal.aiff", 1.0)
    fixtures['medium_aiff'] = create_mock_aiff_file(temp_dir / "medium.aiff", 10.0)
    fixtures['large_aiff'] = create_mock_aiff_file(temp_dir / "large.aiff", 60.0)
    
    # Chapter files
    fixtures['chapter_files'] = create_mock_chapter_files(temp_dir / "chapters", 5, 3.0)
    
    # Error cases
    fixtures['corrupted_audio'] = create_mock_corrupted_audio_file(temp_dir / "corrupted.aiff")
    fixtures['empty_audio'] = create_mock_empty_audio_file(temp_dir / "empty.aiff")
    
    # Different formats
    fixtures['wav_file'] = create_mock_wav_file(temp_dir / "test.wav", 5.0)
    fixtures['mp3_file'] = create_mock_mp3_file(temp_dir / "test.mp3", 5.0)
    
    # Mock processor
    fixtures['processor'] = MockAudioProcessor(temp_dir)
    
    return fixtures 