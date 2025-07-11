import argparse
import os
import sys
import tempfile

from audio_handler import process_chapters
from epub_handler import epub_to_chunks


def main() -> None:
    """Main function to parse arguments and orchestrate the conversion."""
    parser = argparse.ArgumentParser(
        description="Convert an EPUB file to an audio file using parallel processing.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input EPUB file."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Base filename for the output audio file (e.g., 'MyBook.mp3').",
    )
    parser.add_argument(
        "-v", "--voice", help="The voice for speech synthesis (e.g., 'Samantha')."
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Number of parallel jobs. Defaults to (CPU cores - 1).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["aiff", "mp3"],
        default="aiff",
        help="The output audio format. 'mp3' requires ffmpeg. (default: aiff)",
    )
    parser.add_argument(
        "--keep-chapters",
        action="store_true",
        help="If specified, saves the individual chapter audio files in a dedicated folder.",
    )

    args = parser.parse_args()

    # --- New Output Directory Logic ---
    output_base_name = os.path.splitext(os.path.basename(args.output))[0]
    book_output_dir = os.path.join("output", output_base_name)
    os.makedirs(book_output_dir, exist_ok=True)

    final_output_path = os.path.join(book_output_dir, os.path.basename(args.output))
    # --- End New Logic ---

    title, text_chunks = epub_to_chunks(args.input)

    if not text_chunks:
        sys.exit("Error: No text content could be extracted from the EPUB.")

    num_chunks = len(text_chunks)
    print(f"Book split into {num_chunks} chapters/chunks.")

    if args.keep_chapters:
        chapter_dir = os.path.join(book_output_dir, f"{output_base_name}_chapters")
        os.makedirs(chapter_dir, exist_ok=True)

        # --- Pre-run Cleanup Logic ---
        print(f"Cleaning up old chapter files in {chapter_dir}...")
        for old_file in os.listdir(chapter_dir):
            if old_file.endswith(".aiff"):
                os.remove(os.path.join(chapter_dir, old_file))
        # --- End Cleanup Logic ---

        print(f"Chapter files will be saved in: {chapter_dir}")
        process_chapters(text_chunks, chapter_dir, args, final_output_path)
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            process_chapters(text_chunks, temp_dir, args, final_output_path)


if __name__ == "__main__":
    main()
