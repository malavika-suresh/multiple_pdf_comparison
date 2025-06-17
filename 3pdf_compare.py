"""
PDF Comparison Tool

This script compares two PDF files against a base PDF, highlights differences,
and generates a combined output for visual comparison.
"""

import fitz  # PyMuPDF
from difflib import SequenceMatcher
import os
import re
from typing import List, Dict, Tuple


def extract_words(page: fitz.Page) -> List[Dict]:

    words = []
    word_list = page.get_text("words") 
    for word in word_list:
        words.append({
            "text": word[4], 
            "rect": fitz.Rect(word[:4])
        })
    return words


def highlight_word_differences(
    base_pdf_path: str, 
    compare_pdf_path: str, 
    output_path: str, 
    color: Tuple[float, float, float]
) -> None:
    """
    Highlight differences between two PDFs by comparing words.
    
    Args:
        base_pdf_path: Path to the base/reference PDF
        compare_pdf_path: Path to the PDF to compare against base
        output_path: Path to save the highlighted PDF
        color: RGB tuple for highlight color
    """
    base_doc = fitz.open(base_pdf_path)
    compare_doc = fitz.open(compare_pdf_path)

    for page_num in range(min(len(base_doc), len(compare_doc))):
        base_page = base_doc[page_num]
        compare_page = compare_doc[page_num]

        base_words = extract_words(base_page)
        compare_words = extract_words(compare_page)

        # Normalize text by removing whitespace for comparison
        base_text = [re.sub(r'\s+', '', word["text"]) for word in base_words]
        compare_text = [re.sub(r'\s+', '', word["text"]) for word in compare_words]

        matcher = SequenceMatcher(None, base_text, compare_text)

        for operation, i1, i2, j1, j2 in matcher.get_opcodes():
            if operation in ("insert", "replace", "delete"):
                for idx in range(j1, j2):
                    if idx < len(compare_words):
                        rect = compare_words[idx]["rect"]
                        highlight = compare_page.add_highlight_annot(rect)
                        highlight.set_colors(stroke=color)
                        highlight.update()

    compare_doc.save(output_path)
    base_doc.close()
    compare_doc.close()


def merge_pdfs_horizontally(
    pdf_paths: List[str], 
    output_path: str,
    dpi: int = 150
) -> None:
   
    pdf_documents = [fitz.open(path) for path in pdf_paths]
    num_pages = min(len(doc) for doc in pdf_documents)

    output_document = fitz.open()
    
    for page_num in range(num_pages):
        pages = [doc.load_page(page_num) for doc in pdf_documents]
        widths = [page.rect.width for page in pages]
        heights = [page.rect.height for page in pages]

        new_width = sum(widths)
        new_height = max(heights)
        new_page = output_document.new_page(width=new_width, height=new_height)

        x_offset = 0
        for page in pages:
            pixmap = page.get_pixmap(dpi=dpi)
            img_rect = fitz.Rect(
                x_offset, 
                0, 
                x_offset + page.rect.width, 
                page.rect.height
            )
            new_page.insert_image(img_rect, pixmap=pixmap)
            x_offset += page.rect.width

    output_document.save(output_path)
    output_document.close()
    
    for doc in pdf_documents:
        doc.close()


def compare_pdfs(
    base_pdf_path: str,
    comparison_pdf1_path: str,
    comparison_pdf2_path: str,
    output_directory: str
) -> None:

    os.makedirs(output_directory, exist_ok=True)

    output_path1 = os.path.join(output_directory, "comparison1_highlighted.pdf")
    output_path2 = os.path.join(output_directory, "comparison2_highlighted.pdf")

    
    highlight_word_differences(base_pdf_path, comparison_pdf1_path, output_path1, (1, 0, 0))
    highlight_word_differences(base_pdf_path, comparison_pdf2_path, output_path2, (0, 1, 0))

   
    merged_output_path = os.path.join(output_directory, "combined_comparison.pdf")
    merge_pdfs_horizontally(
        [base_pdf_path, output_path1, output_path2],
        merged_output_path
    )

    print(f"Comparison complete. Output saved to: {merged_output_path}")


if __name__ == "__main__":
    # Example usage
    BASE_PDF = r"pdfs\test1.pdf"
    COMPARISON_PDF1 = r"pdfs\test2.pdf"
    COMPARISON_PDF2 = r"pdfs\test3.pdf"
    OUTPUT_DIR = "comparison_results"
    
    compare_pdfs(BASE_PDF, COMPARISON_PDF1, COMPARISON_PDF2, OUTPUT_DIR)

