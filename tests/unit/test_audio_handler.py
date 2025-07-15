"""
Unit tests for the audio handler module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from audio_handler import (
    convert_chunk_to_audio,
    process_chapters,
    merge_audio_files,
    convert_aiff_to_mp3,
    secure_file_cleanup
)


@pytest.mark.unit
@pytest.mark.audio
class TestConvertChunkToAudio:
    """Test cases for convert_chunk_to_audio function."""
    
    def test_convert_chunk_to_audio_success(self, temp_dir, mock_subprocess_runner):
        """Test successful text chunk to audio conversion."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, "Samantha")
        
        # Mock successful subprocess execution
        mock_subprocess_runner.run_command.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )
        
        # Create a mock output file
        output_file = Path(chapter_dir) / "Chapter_001.aiff"
        output_file.write_bytes(b"mock audio data")
        
        # Execute
        result = convert_chunk_to_audio(args)
        
        # Verify
        assert result is not None
        assert result == str(output_file)
        assert output_file.exists()
        
        # Verify subprocess was called with correct arguments
        mock_subprocess_runner.run_command.assert_called_once()
        call_args = mock_subprocess_runner.run_command.call_args
        assert call_args[0][0] == "say"
        assert "-o" in call_args[0][1]
        assert "-v" in call_args[0][1]
        assert "Samantha" in call_args[0][1]
    
    def test_convert_chunk_to_audio_no_voice(self, temp_dir, mock_subprocess_runner):
        """Test audio conversion without specifying voice."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, None)
        
        # Mock successful subprocess execution
        mock_subprocess_runner.run_command.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )
        
        # Create a mock output file
        output_file = Path(chapter_dir) / "Chapter_001.aiff"
        output_file.write_bytes(b"mock audio data")
        
        # Execute
        result = convert_chunk_to_audio(args)
        
        # Verify
        assert result is not None
        
        # Verify subprocess was called without voice parameter
        call_args = mock_subprocess_runner.run_command.call_args
        assert "-v" not in call_args[0][1]
    
    def test_convert_chunk_to_audio_subprocess_error(self, temp_dir, mock_subprocess_runner):
        """Test handling of subprocess errors."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, "Samantha")
        
        # Mock subprocess failure
        mock_subprocess_runner.run_command.return_value = Mock(
            returncode=1, stdout="", stderr="Error occurred"
        )
        
        # Execute
        result = convert_chunk_to_audio(args)
        
        # Verify
        assert result is None
    
    def test_convert_chunk_to_audio_file_not_created(self, temp_dir, mock_subprocess_runner):
        """Test handling when output file is not created."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, "Samantha")
        
        # Mock successful subprocess but file not created
        mock_subprocess_runner.run_command.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )
        
        # Execute (no file created)
        result = convert_chunk_to_audio(args)
        
        # Verify
        assert result is None
    
    def test_convert_chunk_to_audio_empty_file(self, temp_dir, mock_subprocess_runner):
        """Test handling when output file is empty."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, "Samantha")
        
        # Mock successful subprocess execution
        mock_subprocess_runner.run_command.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )
        
        # Create empty output file
        output_file = Path(chapter_dir) / "Chapter_001.aiff"
        output_file.touch()
        
        # Execute
        result = convert_chunk_to_audio(args)
        
        # Verify
        assert result is None
    
    def test_convert_chunk_to_audio_retry_mechanism(self, temp_dir, mock_subprocess_runner):
        """Test retry mechanism for transient failures."""
        # Setup
        chapter_dir = str(temp_dir / "chapters")
        os.makedirs(chapter_dir, exist_ok=True)
        
        args = (0, "Test text content", chapter_dir, "Samantha")
        
        # Mock first call fails, second succeeds
        mock_subprocess_runner.run_command.side_effect = [
            Mock(returncode=1, stdout="", stderr="Temporary error"),
            Mock(returncode=0, stdout="", stderr="")
        ]
        
        # Create a mock output file after second call
        output_file = Path(chapter_dir) / "Chapter_001.aiff"
        
        def create_file_on_second_call(*args, **kwargs):
            output_file.write_bytes(b"mock audio data")
            return mock_subprocess_runner.run_command.side_effect[1]
        
        mock_subprocess_runner.run_command.side_effect = [
            Mock(returncode=1, stdout="", stderr="Temporary error"),
            create_file_on_second_call
        ]
        
        # Execute
        result = convert_chunk_to_audio(args)
        
        # Verify retry occurred
        assert mock_subprocess_runner.run_command.call_count == 2


@pytest.mark.unit
@pytest.mark.audio
class TestProcessChapters:
    """Test cases for process_chapters function."""
    
    def test_process_chapters_success_aiff(self, temp_dir, mock_args, sample_text_chunks):
        """Test successful chapter processing with AIFF output."""
        # Setup
        mock_args.format = "aiff"
        mock_args.jobs = 2
        final_output_path = str(temp_dir / "output.aiff")
        
        with patch('audio_handler.Pool') as mock_pool, \
             patch('audio_handler.merge_audio_files') as mock_merge:
            
            # Mock multiprocessing pool
            mock_pool_instance = Mock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance
            
            # Mock successful audio file creation
            mock_audio_files = [
                str(temp_dir / "Chapter_001.aiff"),
                str(temp_dir / "Chapter_002.aiff"),
                str(temp_dir / "Chapter_003.aiff")
            ]
            
            # Create mock audio files
            for file_path in mock_audio_files:
                Path(file_path).write_bytes(b"mock audio data")
            
            mock_pool_instance.imap.return_value = mock_audio_files
            
            # Execute
            process_chapters(sample_text_chunks, str(temp_dir), mock_args, final_output_path)
            
            # Verify
            mock_merge.assert_called_once()
            merge_call_args = mock_merge.call_args[0]
            assert merge_call_args[1] == final_output_path
    
    def test_process_chapters_success_mp3(self, temp_dir, mock_args, sample_text_chunks):
        """Test successful chapter processing with MP3 output."""
        # Setup
        mock_args.format = "mp3"
        mock_args.jobs = 2
        final_output_path = str(temp_dir / "output.mp3")
        
        with patch('audio_handler.Pool') as mock_pool, \
             patch('audio_handler.merge_audio_files') as mock_merge, \
             patch('audio_handler.convert_aiff_to_mp3') as mock_convert, \
             patch('audio_handler.secure_file_cleanup') as mock_cleanup:
            
            # Mock multiprocessing pool
            mock_pool_instance = Mock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance
            
            # Mock successful audio file creation
            mock_audio_files = [
                str(temp_dir / "Chapter_001.aiff"),
                str(temp_dir / "Chapter_002.aiff"),
                str(temp_dir / "Chapter_003.aiff")
            ]
            
            # Create mock audio files
            for file_path in mock_audio_files:
                Path(file_path).write_bytes(b"mock audio data")
            
            mock_pool_instance.imap.return_value = mock_audio_files
            
            # Execute
            process_chapters(sample_text_chunks, str(temp_dir), mock_args, final_output_path)
            
            # Verify MP3 conversion workflow
            mock_merge.assert_called_once()
            mock_convert.assert_called_once()
            mock_cleanup.assert_called_once()
            
            # Verify AIFF file was created first, then converted
            merge_call_args = mock_merge.call_args[0]
            assert merge_call_args[1].endswith('.aiff')
            
            convert_call_args = mock_convert.call_args[0]
            assert convert_call_args[1] == final_output_path
    
    def test_process_chapters_no_audio_files(self, temp_dir, mock_args, sample_text_chunks):
        """Test handling when no audio files are created."""
        # Setup
        mock_args.format = "aiff"
        mock_args.jobs = 2
        final_output_path = str(temp_dir / "output.aiff")
        
        with patch('audio_handler.Pool') as mock_pool:
            # Mock multiprocessing pool
            mock_pool_instance = Mock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance
            
            # Mock no audio files created (all None)
            mock_pool_instance.imap.return_value = [None, None, None]
            
            # Execute and verify exception
            with pytest.raises(RuntimeError, match="No audio files were successfully created"):
                process_chapters(sample_text_chunks, str(temp_dir), mock_args, final_output_path)
    
    def test_process_chapters_low_success_rate(self, temp_dir, mock_args, sample_text_chunks):
        """Test handling when success rate is too low."""
        # Setup
        mock_args.format = "aiff"
        mock_args.jobs = 2
        final_output_path = str(temp_dir / "output.aiff")
        
        with patch('audio_handler.Pool') as mock_pool:
            # Mock multiprocessing pool
            mock_pool_instance = Mock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance
            
            # Mock low success rate (only 1 out of 3 successful)
            mock_audio_files = [
                str(temp_dir / "Chapter_001.aiff"),
                None,
                None
            ]
            
            # Create one mock audio file
            Path(mock_audio_files[0]).write_bytes(b"mock audio data")
            
            mock_pool_instance.imap.return_value = mock_audio_files
            
            # Execute and verify exception
            with pytest.raises(RuntimeError, match="Too many failed conversions"):
                process_chapters(sample_text_chunks, str(temp_dir), mock_args, final_output_path)


@pytest.mark.unit
@pytest.mark.audio
class TestMergeAudioFiles:
    """Test cases for merge_audio_files function."""
    
    def test_merge_audio_files_success(self, temp_dir, audio_fixtures):
        """Test successful audio file merging."""
        # Setup
        audio_files = audio_fixtures['chapter_files']
        output_path = str(temp_dir / "merged.aiff")
        
        with patch('audio_handler.secure_runner') as mock_runner:
            # Mock successful ffmpeg execution
            mock_runner.run_command.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )
            
            # Execute
            merge_audio_files([str(f) for f in audio_files], output_path)
            
            # Verify
            mock_runner.run_command.assert_called_once()
            call_args = mock_runner.run_command.call_args
            assert call_args[0][0] == "ffmpeg"
            assert "-f" in call_args[0][1]
            assert "concat" in call_args[0][1]
    
    def test_merge_audio_files_no_files(self, temp_dir):
        """Test handling when no audio files are provided."""
        output_path = str(temp_dir / "merged.aiff")
        
        with pytest.raises(RuntimeError, match="No audio files to merge"):
            merge_audio_files([], output_path)
    
    def test_merge_audio_files_missing_files(self, temp_dir):
        """Test handling when some audio files are missing."""
        # Setup
        audio_files = [
            str(temp_dir / "Chapter_001.aiff"),
            str(temp_dir / "Chapter_002.aiff"),  # This file doesn't exist
            str(temp_dir / "Chapter_003.aiff")
        ]
        
        # Create only some files
        Path(audio_files[0]).write_bytes(b"mock audio data")
        Path(audio_files[2]).write_bytes(b"mock audio data")
        
        output_path = str(temp_dir / "merged.aiff")
        
        # Execute and verify exception
        with pytest.raises(RuntimeError, match="Missing audio files"):
            merge_audio_files(audio_files, output_path)
    
    def test_merge_audio_files_ffmpeg_error(self, temp_dir, audio_fixtures):
        """Test handling of ffmpeg errors during merging."""
        # Setup
        audio_files = audio_fixtures['chapter_files']
        output_path = str(temp_dir / "merged.aiff")
        
        with patch('audio_handler.secure_runner') as mock_runner:
            # Mock ffmpeg failure
            mock_runner.run_command.return_value = Mock(
                returncode=1, stdout="", stderr="FFmpeg error occurred"
            )
            
            # Execute and verify exception
            with pytest.raises(RuntimeError, match="Error during audio merging"):
                merge_audio_files([str(f) for f in audio_files], output_path)
    
    def test_merge_audio_files_temp_file_cleanup(self, temp_dir, audio_fixtures):
        """Test that temporary files are cleaned up properly."""
        # Setup
        audio_files = audio_fixtures['chapter_files']
        output_path = str(temp_dir / "merged.aiff")
        
        with patch('audio_handler.secure_runner') as mock_runner, \
             patch('audio_handler.secure_file_cleanup') as mock_cleanup:
            
            # Mock successful ffmpeg execution
            mock_runner.run_command.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )
            
            # Execute
            merge_audio_files([str(f) for f in audio_files], output_path)
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()


@pytest.mark.unit
@pytest.mark.audio
class TestConvertAiffToMp3:
    """Test cases for convert_aiff_to_mp3 function."""
    
    def test_convert_aiff_to_mp3_success(self, temp_dir, audio_fixtures):
        """Test successful AIFF to MP3 conversion."""
        # Setup
        aiff_path = str(audio_fixtures['minimal_aiff'])
        mp3_path = str(temp_dir / "output.mp3")
        
        with patch('audio_handler.secure_runner') as mock_runner, \
             patch('audio_handler.config') as mock_config:
            
            # Mock configuration
            mock_config.get_mp3_quality.return_value = 5
            
            # Mock successful ffmpeg execution
            mock_runner.run_command.return_value = Mock(
                returncode=0, stdout="", stderr=""
            )
            
            # Execute
            convert_aiff_to_mp3(aiff_path, mp3_path)
            
            # Verify
            mock_runner.run_command.assert_called_once()
            call_args = mock_runner.run_command.call_args
            assert call_args[0][0] == "ffmpeg"
            assert "-i" in call_args[0][1]
            assert "-q:a" in call_args[0][1]
            assert "5" in call_args[0][1]
    
    def test_convert_aiff_to_mp3_ffmpeg_error(self, temp_dir, audio_fixtures):
        """Test handling of ffmpeg errors during conversion."""
        # Setup
        aiff_path = str(audio_fixtures['minimal_aiff'])
        mp3_path = str(temp_dir / "output.mp3")
        
        with patch('audio_handler.secure_runner') as mock_runner, \
             patch('audio_handler.config') as mock_config, \
             patch('audio_handler.sys.exit') as mock_exit:
            
            # Mock configuration
            mock_config.get_mp3_quality.return_value = 5
            
            # Mock ffmpeg failure
            mock_runner.run_command.return_value = Mock(
                returncode=1, stdout="", stderr="Conversion error"
            )
            
            # Execute
            convert_aiff_to_mp3(aiff_path, mp3_path)
            
            # Verify sys.exit was called with error
            mock_exit.assert_called_once()
            assert "Error during MP3 conversion" in str(mock_exit.call_args[0][0])


@pytest.mark.unit
class TestSecureFileCleanup:
    """Test cases for secure_file_cleanup function."""
    
    def test_secure_file_cleanup_success(self, temp_dir):
        """Test successful file cleanup."""
        # Setup
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")
        
        # Execute
        secure_file_cleanup(str(test_file))
        
        # Verify
        assert not test_file.exists()
    
    def test_secure_file_cleanup_nonexistent_file(self, temp_dir):
        """Test cleanup of non-existent file (should not raise error)."""
        # Setup
        nonexistent_file = str(temp_dir / "nonexistent.txt")
        
        # Execute (should not raise exception)
        secure_file_cleanup(nonexistent_file)
    
    def test_secure_file_cleanup_permission_error(self, temp_dir):
        """Test cleanup handles permission errors gracefully."""
        # Setup
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")
        
        with patch('audio_handler.os.remove') as mock_remove:
            # Mock permission error
            mock_remove.side_effect = OSError("Permission denied")
            
            # Execute (should not raise exception)
            secure_file_cleanup(str(test_file))
            
            # Verify remove was attempted
            mock_remove.assert_called_once() 