"""
EPUB sample generators for comprehensive testing.
"""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional


def create_minimal_epub(output_path: Path, title: str = "Test Book", author: str = "Test Author") -> Path:
    """Create a minimal valid EPUB file for basic testing."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
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
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{title}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:identifier id="bookid">test-book-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        <itemref idref="chapter1"/>
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
        <navPoint id="chapter1" playOrder="1">
            <navLabel><text>Chapter 1</text></navLabel>
            <content src="chapter1.xhtml"/>
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
    <h1>Chapter 1</h1>
    <p>This is a minimal test chapter.</p>
</body>
</html>'''
        epub.writestr("OEBPS/chapter1.xhtml", chapter1)
    
    return output_path


def create_multi_chapter_epub(output_path: Path, num_chapters: int = 5) -> Path:
    """Create an EPUB with multiple chapters for testing parallel processing."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
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
        
        # Generate manifest and spine items
        manifest_items = []
        spine_items = []
        nav_points = []
        
        for i in range(1, num_chapters + 1):
            chapter_id = f"chapter{i}"
            chapter_file = f"chapter{i}.xhtml"
            
            manifest_items.append(f'<item id="{chapter_id}" href="{chapter_file}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{chapter_id}"/>')
            nav_points.append(f'''<navPoint id="{chapter_id}" playOrder="{i}">
            <navLabel><text>Chapter {i}</text></navLabel>
            <content src="{chapter_file}"/>
        </navPoint>''')
        
        # OEBPS/content.opf
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Multi-Chapter Test Book</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:identifier id="bookid">test-book-multi-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        {chr(10).join(manifest_items)}
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        {chr(10).join(spine_items)}
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-multi-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Multi-Chapter Test Book</text></docTitle>
    <navMap>
        {chr(10).join(nav_points)}
    </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)
        
        # Create chapter files
        for i in range(1, num_chapters + 1):
            chapter_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter {i}</title>
</head>
<body>
    <h1>Chapter {i}: Test Chapter</h1>
    <p>This is chapter {i} of the multi-chapter test book.</p>
    <p>It contains some test content for processing. The content is moderately long to test audio conversion timing.</p>
    <p>Each chapter should be processed independently and then merged together.</p>
</body>
</html>'''
            epub.writestr(f"OEBPS/chapter{i}.xhtml", chapter_content)
    
    return output_path


def create_complex_formatting_epub(output_path: Path) -> Path:
    """Create an EPUB with complex HTML formatting for testing text extraction."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
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
        <dc:title>Complex Formatting Test</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:identifier id="bookid">test-book-complex-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        <itemref idref="chapter1"/>
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-complex-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Complex Formatting Test</text></docTitle>
    <navMap>
        <navPoint id="chapter1" playOrder="1">
            <navLabel><text>Chapter 1</text></navLabel>
            <content src="chapter1.xhtml"/>
        </navPoint>
    </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)
        
        # OEBPS/chapter1.xhtml with complex formatting
        chapter1 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Complex Formatting Chapter</title>
    <style type="text/css">
        .footnote { font-size: smaller; }
        .emphasis { font-style: italic; }
    </style>
</head>
<body>
    <h1>Chapter 1: Complex Formatting</h1>
    
    <p>This chapter contains <strong>bold text</strong> and <em>italic text</em> and <u>underlined text</u>.</p>
    
    <p>Here is a list:</p>
    <ul>
        <li>First item</li>
        <li>Second item with <span class="emphasis">emphasis</span></li>
        <li>Third item</li>
    </ul>
    
    <p>Here is a numbered list:</p>
    <ol>
        <li>First numbered item</li>
        <li>Second numbered item</li>
    </ol>
    
    <blockquote>
        <p>This is a blockquote with some important text that should be preserved.</p>
    </blockquote>
    
    <p>Here is a table:</p>
    <table>
        <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
        </tr>
        <tr>
            <td>Cell 3</td>
            <td>Cell 4</td>
        </tr>
    </table>
    
    <p>This paragraph has a <span class="footnote">footnote-style text</span> embedded.</p>
    
    <div>
        <p>This is text inside a div.</p>
    </div>
    
    <p>Link text: <a href="https://example.com">Example Link</a> should be preserved.</p>
    
    <p>Special characters: &amp; &lt; &gt; &quot; &apos;</p>
    
    <p>Unicode characters: café, naïve, résumé</p>
</body>
</html>'''
        epub.writestr("OEBPS/chapter1.xhtml", chapter1)
    
    return output_path


def create_empty_epub(output_path: Path) -> Path:
    """Create an EPUB with no content chapters for edge case testing."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
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
        
        # OEBPS/content.opf with no content items
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Empty Test Book</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:identifier id="bookid">test-book-empty-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-empty-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Empty Test Book</text></docTitle>
    <navMap>
    </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)
    
    return output_path


def create_malformed_epub(output_path: Path) -> Path:
    """Create a malformed EPUB for error testing."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Missing mimetype file
        
        # Invalid container.xml
        container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <!-- Missing rootfile -->
    </rootfiles>
</container>'''
        epub.writestr("META-INF/container.xml", container_xml)
        
        # Invalid content.opf
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf">
    <!-- Missing required metadata -->
    <manifest>
    </manifest>
    <spine>
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
    
    return output_path


def create_large_epub(output_path: Path, num_chapters: int = 50) -> Path:
    """Create a large EPUB for performance testing."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
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
        
        # Generate manifest and spine items
        manifest_items = []
        spine_items = []
        nav_points = []
        
        for i in range(1, num_chapters + 1):
            chapter_id = f"chapter{i}"
            chapter_file = f"chapter{i}.xhtml"
            
            manifest_items.append(f'<item id="{chapter_id}" href="{chapter_file}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{chapter_id}"/>')
            nav_points.append(f'''<navPoint id="{chapter_id}" playOrder="{i}">
            <navLabel><text>Chapter {i}</text></navLabel>
            <content src="{chapter_file}"/>
        </navPoint>''')
        
        # OEBPS/content.opf
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Large Test Book</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:identifier id="bookid">test-book-large-123</dc:identifier>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        {chr(10).join(manifest_items)}
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        {chr(10).join(spine_items)}
    </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="test-book-large-123"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Large Test Book</text></docTitle>
    <navMap>
        {chr(10).join(nav_points)}
    </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)
        
        # Create chapter files with substantial content
        for i in range(1, num_chapters + 1):
            chapter_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Chapter {i}</title>
</head>
<body>
    <h1>Chapter {i}: Large Test Chapter</h1>
    <p>This is chapter {i} of the large test book. It contains substantial content for performance testing.</p>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
    <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
    <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.</p>
    <p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.</p>
    <p>This chapter is designed to test the performance of the TTS system with longer content that will take more time to process and convert to audio.</p>
</body>
</html>'''
            epub.writestr(f"OEBPS/chapter{i}.xhtml", chapter_content)
    
    return output_path 