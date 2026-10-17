import sys
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(file_path, output_path1, output_path2):
    pdf_reader = PdfReader(file_path)

    # Get the total number of pages
    total_pages = len(pdf_reader.pages)
    middle_page = total_pages // 2

    # Create two PDF writers for the two halves
    pdf_writer1 = PdfWriter()
    pdf_writer2 = PdfWriter()

    # Add the pages to the respective PDF writers
    for page_num in range(total_pages):
        page = pdf_reader.pages[page_num]
        if page_num < middle_page:
            pdf_writer1.add_page(page)
        else:
            pdf_writer2.add_page(page)

    # Write the split PDFs to files
    with open(output_path1, 'wb') as output_pdf1:
        pdf_writer1.write(output_pdf1)

    with open(output_path2, 'wb') as output_pdf2:
        pdf_writer2.write(output_pdf2)


# Usage
split_pdf(sys.argv[1], 'first_half.pdf', 'second_half.pdf')
