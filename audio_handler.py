import argparse
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from typing import List, Optional, Tuple

from tqdm import tqdm
from secure_subprocess import secure_runner, SubprocessError
from config import config


def convert_chunk_to_audio(args: Tuple[int, str, str, Optional[str]]) -> Optional[str]:
    """Converts a single text chunk to an audio file using the 'say' command."""
    index, text_chunk, chapter_dir, voice = args

    output_filename = os.path.join(chapter_dir, f"Chapter_{index + 1:03d}.aiff")

    # Build command arguments securely
    command_args = ["-o", output_filename]
    if voice:
        command_args.extend(["-v", voice])

    # Retry mechanism for transient failures
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = secure_runner.run_command(
                "say", 
                command_args, 
                input_data=text_chunk,
                timeout=300  # 5 minute timeout per chunk
            )
            
            if result.returncode == 0:
                # Verify the output file was created and has content
                if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                    return output_filename
                else:
                    print(
                        f"\nWarning: Audio file for chunk {index + 1} was not created or is empty",
                        file=sys.stderr,
                    )
                    return None
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"\nError processing chunk {index + 1}: {error_msg}", file=sys.stderr)
                
                if attempt < max_retries - 1:
                    print(f"Retrying chunk {index + 1} (attempt {attempt + 2}/{max_retries})", file=sys.stderr)
                    continue
                else:
                    print(f"Failed to process chunk {index + 1} after {max_retries} attempts", file=sys.stderr)
                    return None
                    
        except SubprocessError as e:
            error_msg = str(e)
            print(f"\nError processing chunk {index + 1}: {error_msg}", file=sys.stderr)
            
            if attempt < max_retries - 1:
                print(f"Retrying chunk {index + 1} (attempt {attempt + 2}/{max_retries})", file=sys.stderr)
                continue
            else:
                print(f"Failed to process chunk {index + 1} after {max_retries} attempts", file=sys.stderr)
                return None

    return None


def secure_file_cleanup(file_path: str) -> None:
    """Securely clean up a temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        print(f"Warning: Could not clean up temporary file {file_path}: {e}", file=sys.stderr)


def process_chapters(text_chunks: List[str], chapter_dir: str, args: argparse.Namespace, final_output_path: str) -> None:
    """Process text chunks into audio files and merge them."""
    
    # Prepare arguments for parallel processing
    chunk_args = [(i, chunk, chapter_dir, args.voice) for i, chunk in enumerate(text_chunks)]
    
    # Use multiprocessing with progress bar
    with Pool(processes=args.jobs) as pool:
        results = list(tqdm(
            pool.imap(convert_chunk_to_audio, chunk_args),
            total=len(text_chunks),
            desc="Converting text to audio",
            unit="chapter"
        ))
    
    # Filter out None results and sort by chapter number
    audio_files = [f for f in results if f is not None]
    audio_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    
    if not audio_files:
        raise RuntimeError("No audio files were successfully created")
    
    # Check if we have a reasonable number of successful conversions
    success_rate = len(audio_files) / len(text_chunks)
    if success_rate < 0.5:  # Less than 50% success rate
        raise RuntimeError(f"Too many failed conversions ({success_rate:.1%} success rate)")
    
    print(f"Successfully converted {len(audio_files)} out of {len(text_chunks)} chapters")
    
    # Merge audio files
    merge_audio_files(audio_files, final_output_path)
    
    # Convert to MP3 if requested
    if args.format == "mp3":
        aiff_path = final_output_path
        mp3_path = os.path.splitext(final_output_path)[0] + ".mp3"
        convert_aiff_to_mp3(aiff_path, mp3_path)
        
        # Clean up the temporary AIFF file
        secure_file_cleanup(aiff_path)


def merge_audio_files(audio_files: List[str], output_path: str) -> None:
    """Merge multiple audio files into a single file using ffmpeg."""
    if not audio_files:
        raise RuntimeError("No audio files to merge")
    
    # Create a temporary file list for ffmpeg
    temp_list_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_list_path = temp_file.name
            for audio_file in audio_files:
                # Escape single quotes in filenames for ffmpeg
                escaped_path = audio_file.replace("'", "'\"'\"'")
                temp_file.write(f"file '{escaped_path}'\n")
        
        print(f"Merging {len(audio_files)} audio files into '{os.path.basename(output_path)}'...")
        
        # Use ffmpeg to concatenate the files
        command_args = ["-f", "concat", "-safe", "0", "-i", temp_list_path, "-c", "copy", output_path, "-y"]
        
        result = secure_runner.run_command(
            "ffmpeg",
            command_args,
            timeout=1800  # 30 minute timeout for merging
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Error during audio merging:\n{result.stderr}")
        
        print(f"Successfully created merged audio file: {output_path}")
        
    except SubprocessError as e:
        raise RuntimeError(f"Error during audio merging: {e}")
    
    finally:
        if temp_list_path:
            secure_file_cleanup(temp_list_path)


def convert_aiff_to_mp3(aiff_path: str, mp3_path: str) -> None:
    """Converts an AIFF file to MP3 using ffmpeg with configured quality."""
    print(f"Converting '{os.path.basename(aiff_path)}' to MP3 format...")
    
    # Get MP3 quality from configuration
    mp3_quality = config.get_mp3_quality()
    
    command_args = ["-i", aiff_path, "-q:a", str(mp3_quality), mp3_path, "-y"]
    
    try:
        result = secure_runner.run_command(
            "ffmpeg",
            command_args,
            timeout=600  # 10 minute timeout for conversion
        )
        
        if result.returncode != 0:
            sys.exit(f"Error during MP3 conversion:\n{result.stderr}")
            
        print(f"Successfully created MP3 file: {mp3_path} (quality: {mp3_quality})")
        
    except SubprocessError as e:
        sys.exit(f"Error during MP3 conversion: {e}")


def get_default_jobs() -> int:
    """Get the default number of parallel jobs."""
    cpu_count = os.cpu_count()
    return max(1, cpu_count - 1) if cpu_count else 1
