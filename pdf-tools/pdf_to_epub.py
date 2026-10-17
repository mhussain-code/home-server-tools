import sys
import os
from pdf2docx import Converter
from ebooklib import epub

def pdf_to_epub(pdf_path, epub_path):
    # Convert PDF to DOCX
    docx_path = pdf_path.replace('.pdf', '.docx')
    cv = Converter(pdf_path)
    cv.convert(docx_path)
    cv.close()

    # Convert DOCX to EPUB
    book = epub.EpubBook()

    # Define title and author for the EPUB book
    book.set_identifier('sample_id')
    book.set_title('Sample Book')
    book.set_language('en')
    book.add_author('Author Name')

    # Read content from the DOCX file
    with open(docx_path, 'rb') as docx_file:
        book.add_item(epub.EpubHtml(title="Chapter 1", file_name="chap_01.xhtml", content=docx_file.read()))

    # Define Table Of Contents
    book.toc = (epub.Link("chap_01.xhtml", "Chapter 1", "chap_1"))

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define spine (order of content)
    book.spine = ["nav", "chap_01"]

    # Write the EPUB file
    epub.write_epub(epub_path, book, {})

    # Clean up the intermediate DOCX file
    os.remove(docx_path)

# Example usage
pdf_to_epub(sys.argv[1], sys.argv[2])
