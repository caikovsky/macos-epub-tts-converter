import argparse
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from typing import List, Optional, Tuple

from tqdm import tqdm
from secure_subprocess import secure_runner, SubprocessError


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
                print(
                    f"\nWarning: Failed to convert chunk {index + 1} (attempt {attempt + 1}/{max_retries}). Error: {error_msg}",
                    file=sys.stderr,
                )
                
                # If this is the last attempt, give up
                if attempt == max_retries - 1:
                    return None
                
                # Wait a bit before retrying
                import time
                time.sleep(1)
                
        except SubprocessError as e:
            print(
                f"\nWarning: Failed to convert chunk {index + 1} (attempt {attempt + 1}/{max_retries}). Security/subprocess error: {e}",
                file=sys.stderr,
            )
            
            # If this is the last attempt, give up
            if attempt == max_retries - 1:
                return None
            
            # Wait a bit before retrying
            import time
            time.sleep(1)
        
        except Exception as e:
            print(
                f"\nWarning: Unexpected error converting chunk {index + 1} (attempt {attempt + 1}/{max_retries}): {e}",
                file=sys.stderr,
            )
            
            # If this is the last attempt, give up
            if attempt == max_retries - 1:
                return None
            
            # Wait a bit before retrying
            import time
            time.sleep(1)
    
    return None


def merge_audio_files(file_list: List[str], final_output: str) -> None:
    """Merges a list of audio files into a single file using ffmpeg."""
    print("\nMerging audio chapters with ffmpeg...")

    # Validate input files
    if not file_list:
        raise ValueError("No audio files provided for merging")
    
    # Check that all input files exist and are not empty
    valid_files = []
    for filename in file_list:
        if not os.path.exists(filename):
            print(f"Warning: Audio file not found: {filename}", file=sys.stderr)
            continue
        
        if os.path.getsize(filename) == 0:
            print(f"Warning: Audio file is empty: {filename}", file=sys.stderr)
            continue
        
        valid_files.append(filename)
    
    if not valid_files:
        raise ValueError("No valid audio files found for merging")
    
    if len(valid_files) != len(file_list):
        print(f"Warning: Using {len(valid_files)} out of {len(file_list)} audio files", file=sys.stderr)

    # Create file list content
    file_list_content = ""
    for filename in valid_files:
        file_list_content += f"file '{os.path.abspath(filename)}'\n"
    
    # Create secure temporary file
    from secure_subprocess import create_secure_temp_file, secure_file_cleanup
    
    temp_list_path = None
    try:
        temp_list_path = create_secure_temp_file(file_list_content, suffix=".txt")
        
        command_args = [
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list_path,
            "-c", "copy",
            final_output,
            "-y",
        ]

        result = secure_runner.run_command(
            "ffmpeg",
            command_args,
            timeout=600  # 10 minute timeout for merging
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"ffmpeg merge failed: {error_msg}")
        
        # Verify the output file was created
        if not os.path.exists(final_output):
            raise RuntimeError(f"Output file was not created: {final_output}")
        
        if os.path.getsize(final_output) == 0:
            raise RuntimeError(f"Output file is empty: {final_output}")
            
        print(f"Successfully created merged audio file: {final_output}")
        
    except SubprocessError as e:
        if "not found" in str(e):
            raise RuntimeError("'ffmpeg' command not found. Please install ffmpeg and ensure it's in your PATH.")
        else:
            raise RuntimeError(f"ffmpeg subprocess error: {e}")
    finally:
        if temp_list_path:
            secure_file_cleanup(temp_list_path)


def convert_aiff_to_mp3(aiff_path: str, mp3_path: str) -> None:
    """Converts an AIFF file to a high-quality MP3 using ffmpeg."""
    print(f"Converting '{os.path.basename(aiff_path)}' to MP3 format...")
    
    command_args = ["-i", aiff_path, "-q:a", "0", mp3_path, "-y"]
    
    try:
        result = secure_runner.run_command(
            "ffmpeg",
            command_args,
            timeout=600  # 10 minute timeout for conversion
        )
        
        if result.returncode != 0:
            sys.exit(f"Error during MP3 conversion:\n{result.stderr}")
            
        print(f"Successfully created MP3 file: {mp3_path}")
        
    except SubprocessError as e:
        sys.exit(f"Error during MP3 conversion: {e}")


def process_chapters(
    text_chunks: List[str],
    chapter_dir: str,
    args: argparse.Namespace,
    final_output_path: str,
) -> None:
    """Orchestrates the parallel conversion of text chunks to audio and merges them."""
    num_workers = args.jobs or max(1, (os.cpu_count() or 2) - 1)
    pool_args = [
        (i, chunk, chapter_dir, args.voice) for i, chunk in enumerate(text_chunks)
    ]
    del text_chunks

    results = []
    failed_chunks = []
    
    with Pool(processes=num_workers) as pool:
        pbar = tqdm(
            pool.imap_unordered(convert_chunk_to_audio, pool_args),
            total=len(pool_args),
            desc="Converting Chapters",
        )
        for i, result in enumerate(pbar):
            if result:
                results.append(result)
            else:
                failed_chunks.append(i + 1)

        pool.close()
        pool.join()

    # Report conversion results
    total_chunks = len(pool_args)
    successful_chunks = len(results)
    failed_count = len(failed_chunks)
    
    if failed_count > 0:
        print(f"\nWarning: {failed_count} out of {total_chunks} chapters failed to convert", file=sys.stderr)
        if failed_count <= 5:  # Show specific chapter numbers if not too many
            print(f"Failed chapters: {', '.join(map(str, failed_chunks))}", file=sys.stderr)
    
    print(f"\nSuccessfully converted {successful_chunks} out of {total_chunks} chapters")

    if not results:
        raise RuntimeError("All audio chapter conversions failed. Check the error messages above.")
    
    if failed_count > total_chunks * 0.5:  # More than 50% failed
        raise RuntimeError(f"Too many chapters failed ({failed_count}/{total_chunks}). Aborting.")

    results.sort()

    if args.format == "mp3":
        from secure_subprocess import secure_file_cleanup
        
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as temp_aiff:
            temp_aiff_path = temp_aiff.name

        try:
            merge_audio_files(results, temp_aiff_path)
            convert_aiff_to_mp3(temp_aiff_path, final_output_path)
        finally:
            secure_file_cleanup(temp_aiff_path)
    else:
        merge_audio_files(results, final_output_path)
