import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import subprocess
import argparse
import sys
import os
from multiprocessing import Pool
import tempfile
from tqdm import tqdm
from typing import List, Optional, Tuple

# A list of common navigation-related text to filter out non-content chapters.
NAV_KEYWORDS = ["table of contents", "cover", "copyright", "dedication", "toc", "contents"]

def get_book_title(book: epub.EpubBook) -> str:
    """Extracts the title from the EPUB metadata."""
    if book.get_metadata('DC', 'title'):
        return book.get_metadata('DC', 'title')[0][0]
    return "Untitled"

def clean_html_chapter(soup: BeautifulSoup):
    """
    Surgically removes common non-narrative elements from a chapter's HTML.
    This function modifies the soup object in-place.
    """
    # Remove nav tags, which are almost always for table of contents
    for tag in soup.find_all('nav'):
        tag.decompose()

    # Remove elements with class names commonly used for page numbers
    for class_name in ['page-number', 'pagenum', 'pagebreak']:
        for tag in soup.find_all(class_=class_name):
            tag.decompose()

def epub_to_chunks(epub_path: str) -> Tuple[str, List[str]]:
    """
    Extracts and cleans text content from an EPUB file, returning the
    title and a list of text chunks (chapters). This version is robust
    and handles EPUBs that may not have a standard spine.
    """
    try:
        book = epub.read_epub(epub_path)
    except ebooklib.epub.EpubException as e:
        sys.exit(f"Error: Failed to read EPUB file at '{epub_path}'. It may be corrupt or not a valid EPUB. Details: {e}")
    except FileNotFoundError:
        sys.exit(f"Error: Input file not found at '{epub_path}'")

    title = get_book_title(book)
    print(f"Processing '{title}'...")

    # Find the navigation file to explicitly exclude it.
    nav_file_name = None
    for item in book.get_items_of_type(ebooklib.ITEM_NAVIGATION):
        nav_file_name = item.get_name()

    text_chunks: List[str] = []
    # Iterate through all documents in the book as a fallback for missing spine.
    for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Exclude the title page and the navigation file by their names.
        if doc.get_name().lower() in ['titlepage.xhtml', nav_file_name]:
            continue
            
        soup = BeautifulSoup(doc.get_content(), 'html.parser')
        
        # Clean the HTML before extracting text
        clean_html_chapter(soup)
        
        text = soup.get_text(strip=True, separator=' ')
        
        if text:
            text_chunks.append(text)

    return title, text_chunks


def convert_chunk_to_audio(args: Tuple[int, str, str, Optional[str]]) -> Optional[str]:
    """
    Worker function to convert a single text chunk to an audio file.
    """
    index, text_chunk, chapter_dir, voice = args
    
    output_filename = os.path.join(chapter_dir, f"Chapter_{index + 1:03d}.aiff")
    
    command = ['say', '-o', output_filename]
    if voice:
        command.extend(['-v', voice])
    
    try:
        subprocess.run(
            command,
            input=text_chunk,
            text=True,
            check=True,
            capture_output=True
        )
        return output_filename
    except subprocess.CalledProcessError as e:
        print(f"\nWarning: Failed to convert chunk {index + 1}. Error: {e.stderr}", file=sys.stderr)
        return None

def merge_audio_files(file_list: List[str], final_output: str) -> None:
    """
    Merges a list of audio files into a single file using ffmpeg.
    """
    print("\nMerging audio chapters with ffmpeg...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for filename in file_list:
            f.write(f"file '{os.path.abspath(filename)}'\n")
        temp_list_path = f.name

    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', temp_list_path,
        '-c', 'copy', final_output, '-y'
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully created merged audio file: {final_output}")
    except FileNotFoundError:
        sys.exit("Error: 'ffmpeg' command not found. Please install ffmpeg and ensure it's in your PATH.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error during ffmpeg merge:\n{e.stderr.decode('utf-8')}")
    finally:
        os.remove(temp_list_path)

def convert_aiff_to_mp3(aiff_path: str, mp3_path: str) -> None:
    """Converts an AIFF file to a high-quality MP3 using ffmpeg."""
    print(f"Converting '{os.path.basename(aiff_path)}' to MP3 format...")
    command = [
        'ffmpeg', '-i', aiff_path, '-q:a', '0', mp3_path, '-y'
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully created MP3 file: {mp3_path}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error during MP3 conversion:\n{e.stderr.decode('utf-8')}")

def process_chapters(text_chunks: List[str], chapter_dir: str, args: argparse.Namespace, final_output_path: str):
    """
    Handles the core logic of converting and merging chapters.
    """
    num_workers = args.jobs or max(1, os.cpu_count() - 1)
    pool_args = [
        (i, chunk, chapter_dir, args.voice) 
        for i, chunk in enumerate(text_chunks)
    ]
    # Explicitly free up memory from the large text_chunks list
    del text_chunks

    results = []
    with Pool(processes=num_workers) as pool:
        pbar = tqdm(pool.imap_unordered(convert_chunk_to_audio, pool_args), total=len(pool_args), desc="Converting Chapters")
        for result in pbar:
            if result:
                results.append(result)
        
        # Ensure all processes are finished and resources are released
        pool.close()
        pool.join()
    
    if not results:
        sys.exit("\nError: All audio chapter conversions failed.")
        
    results.sort()
    
    if args.format == 'mp3':
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

def main() -> None:
    """Main function to parse arguments and orchestrate the conversion."""
    parser = argparse.ArgumentParser(
        description="Convert an EPUB file to an audio file using parallel processing.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-i', '--input', required=True, help="Path to the input EPUB file.")
    parser.add_argument('-o', '--output', required=True, help="Base filename for the output audio file (e.g., 'MyBook.mp3').")
    parser.add_argument('-v', '--voice', help="The voice for speech synthesis (e.g., 'Samantha').")
    parser.add_argument('-j', '--jobs', type=int, help="Number of parallel jobs. Defaults to (CPU cores - 1).")
    parser.add_argument(
        '-f', '--format', 
        choices=['aiff', 'mp3'], 
        default='aiff', 
        help="The output audio format. 'mp3' requires ffmpeg. (default: aiff)"
    )
    parser.add_argument(
        '--keep-chapters',
        action='store_true',
        help="If specified, saves the individual chapter audio files in a dedicated folder."
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

if __name__ == '__main__':
    main()
