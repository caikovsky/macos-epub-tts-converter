import argparse
import os
import sys

# Reuse the robust EPUB handling logic we've already built
from epub_handler import epub_to_chunks


def save_chunks_to_text_files(epub_path: str, output_dir_name: str) -> None:
    """
    Extracts text chunks from an EPUB and saves each one to a separate .txt file.
    """
    # Get the book title and the clean text chunks
    title, text_chunks = epub_to_chunks(epub_path)

    if not text_chunks:
        sys.exit("Error: No text content could be extracted from the EPUB.")

    # Create the main output directory
    base_output_dir = "text_exports"
    os.makedirs(base_output_dir, exist_ok=True)

    # Create a specific directory for this book's text files
    book_text_dir = os.path.join(base_output_dir, output_dir_name)
    os.makedirs(book_text_dir, exist_ok=True)

    print(f"\nSaving {len(text_chunks)} chapters to: {book_text_dir}")

    # Save each chunk to a numbered text file
    for i, chunk in enumerate(text_chunks):
        file_path = os.path.join(book_text_dir, f"Chapter_{i + 1:03d}.txt")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(chunk)
        except IOError as e:
            print(f"Error writing file {file_path}: {e}", file=sys.stderr)

    print("\nSuccessfully saved all chapters as text files.")


def main() -> None:
    """Main function to parse arguments for the text extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract all chapters from an EPUB file into separate .txt files."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input EPUB file."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="A name for the output folder where the .txt files will be saved (e.g., 'MyBook_text').",
    )
    args = parser.parse_args()

    save_chunks_to_text_files(args.input, args.output)


if __name__ == "__main__":
    main()
