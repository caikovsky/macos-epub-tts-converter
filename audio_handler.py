import argparse
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from typing import List, Optional, Tuple

from tqdm import tqdm


def convert_chunk_to_audio(args: Tuple[int, str, str, Optional[str]]) -> Optional[str]:
    """
    Worker function to convert a single text chunk to an audio file.
    """
    index, text_chunk, chapter_dir, voice = args

    output_filename = os.path.join(chapter_dir, f"Chapter_{index + 1:03d}.aiff")

    command = ["say", "-o", output_filename]
    if voice:
        command.extend(["-v", voice])

    try:
        subprocess.run(
            command, input=text_chunk, text=True, check=True, capture_output=True
        )
        return output_filename
    except subprocess.CalledProcessError as e:
        print(
            f"\nWarning: Failed to convert chunk {index + 1}. Error: {e.stderr}",
            file=sys.stderr,
        )
        return None


def merge_audio_files(file_list: List[str], final_output: str) -> None:
    """
    Merges a list of audio files into a single file using ffmpeg.
    """
    print("\nMerging audio chapters with ffmpeg...")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        for filename in file_list:
            f.write(f"file '{os.path.abspath(filename)}'\n")
        temp_list_path = f.name

    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        temp_list_path,
        "-c",
        "copy",
        final_output,
        "-y",
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully created merged audio file: {final_output}")
    except FileNotFoundError:
        sys.exit(
            "Error: 'ffmpeg' command not found. Please install ffmpeg and ensure it's in your PATH."
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error during ffmpeg merge:\n{e.stderr.decode('utf-8')}")
    finally:
        os.remove(temp_list_path)


def convert_aiff_to_mp3(aiff_path: str, mp3_path: str) -> None:
    """Converts an AIFF file to a high-quality MP3 using ffmpeg."""
    print(f"Converting '{os.path.basename(aiff_path)}' to MP3 format...")
    command = ["ffmpeg", "-i", aiff_path, "-q:a", "0", mp3_path, "-y"]
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully created MP3 file: {mp3_path}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error during MP3 conversion:\n{e.stderr.decode('utf-8')}")


def process_chapters(
    text_chunks: List[str],
    chapter_dir: str,
    args: argparse.Namespace,
    final_output_path: str,
):
    """
    Handles the core logic of converting and merging chapters.
    """
    num_workers = args.jobs or max(1, os.cpu_count() - 1)
    pool_args = [
        (i, chunk, chapter_dir, args.voice) for i, chunk in enumerate(text_chunks)
    ]
    # Explicitly free up memory from the large text_chunks list
    del text_chunks

    results = []
    with Pool(processes=num_workers) as pool:
        pbar = tqdm(
            pool.imap_unordered(convert_chunk_to_audio, pool_args),
            total=len(pool_args),
            desc="Converting Chapters",
        )
        for result in pbar:
            if result:
                results.append(result)

        # Ensure all processes are finished and resources are released
        pool.close()
        pool.join()

    if not results:
        sys.exit("\nError: All audio chapter conversions failed.")

    results.sort()

    if args.format == "mp3":
        # Use a temporary file for the intermediate AIFF merge
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as temp_aiff:
            temp_aiff_path = temp_aiff.name

        try:
            merge_audio_files(results, temp_aiff_path)
            convert_aiff_to_mp3(temp_aiff_path, final_output_path)
        finally:
            # Guaranteed cleanup of the intermediate file
            os.remove(temp_aiff_path)
    else:
        # The final output is AIFF
        merge_audio_files(results, final_output_path)
