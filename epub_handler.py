import sys
from typing import List, Tuple

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


def get_book_title(book: epub.EpubBook) -> str:
    """Extracts the title from the EPUB metadata."""
    if book.get_metadata("DC", "title"):
        return book.get_metadata("DC", "title")[0][0]
    return "Untitled"


def clean_html_chapter(soup: BeautifulSoup):
    """
    Surgically removes common non-narrative elements from a chapter's HTML.
    This function modifies the soup object in-place.
    """
    # Remove nav tags, which are almost always for table of contents
    for tag in soup.find_all("nav"):
        tag.decompose()

    # Remove elements with class names commonly used for page numbers
    for class_name in ["page-number", "pagenum", "pagebreak"]:
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
        sys.exit(
            f"Error: Failed to read EPUB file at '{epub_path}'. It may be corrupt or not a valid EPUB. Details: {e}"
        )
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
        if doc.get_name().lower() in ["titlepage.xhtml", nav_file_name]:
            continue

        soup = BeautifulSoup(doc.get_content(), "html.parser")

        # Clean the HTML before extracting text
        clean_html_chapter(soup)

        text = soup.get_text(strip=True, separator=" ")

        if text:
            text_chunks.append(text)

    return title, text_chunks
