import fitz  # PyMuPDF
import os
import re
from difflib import SequenceMatcher
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


def highlight_differences(
    base_pdf_path: str,
    test_pdf_path: str,
    output_path: str,
    highlight_color: Tuple[float, float, float] = (1, 0, 0)
) -> None:
    base_doc = fitz.open(base_pdf_path)
    test_doc = fitz.open(test_pdf_path)

    for page_num in range(min(len(base_doc), len(test_doc))):
        base_page = base_doc[page_num]
        test_page = test_doc[page_num]

        base_words = extract_words(base_page)
        test_words = extract_words(test_page)

        base_text = [re.sub(r'\s+', '', word["text"]) for word in base_words]
        test_text = [re.sub(r'\s+', '', word["text"]) for word in test_words]

        matcher = SequenceMatcher(None, base_text, test_text)
        for tag, _, _, j1, j2 in matcher.get_opcodes():
            if tag in ("insert", "replace", "delete"):
                for idx in range(j1, j2):
                    if idx < len(test_words):
                        rect = test_words[idx]["rect"]
                        highlight = test_page.add_highlight_annot(rect)
                        highlight.set_colors(stroke=highlight_color)
                        highlight.update()

    test_doc.save(output_path)
    base_doc.close()
    test_doc.close()


def merge_pdfs_side_by_side(
    base_pdf_path: str,
    highlighted_pdf_path: str,
    output_path: str,
    dpi: int = 150
) -> None:
    base_doc = fitz.open(base_pdf_path)
    test_doc = fitz.open(highlighted_pdf_path)
    output_doc = fitz.open()

    for page_num in range(min(len(base_doc), len(test_doc))):
        base_page = base_doc.load_page(page_num)
        test_page = test_doc.load_page(page_num)

        width = base_page.rect.width + test_page.rect.width
        height = max(base_page.rect.height, test_page.rect.height)
        new_page = output_doc.new_page(width=width, height=height)

        # Insert base PDF page
        pix_base = base_page.get_pixmap(dpi=dpi)
        new_page.insert_image(fitz.Rect(0, 0, base_page.rect.width, base_page.rect.height), pixmap=pix_base)

        # Insert test PDF page (highlighted)
        pix_test = test_page.get_pixmap(dpi=dpi)
        new_page.insert_image(
            fitz.Rect(base_page.rect.width, 0, width, test_page.rect.height),
            pixmap=pix_test
        )

    output_doc.save(output_path)
    output_doc.close()
    base_doc.close()
    test_doc.close()


def compare_two_pdfs(
    base_pdf_path: str,
    test_pdf_path: str,
    output_dir: str
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    highlighted_pdf = os.path.join(output_dir, "highlighted_test.pdf")
    merged_output_pdf = os.path.join(output_dir, "side_by_side_comparison.pdf")

    highlight_differences(base_pdf_path, test_pdf_path, highlighted_pdf, (1, 0, 0))  # red highlight
    merge_pdfs_side_by_side(base_pdf_path, highlighted_pdf, merged_output_pdf)

    return merged_output_pdf


if __name__ == "__main__":
    BASE_PDF = "pdfs/test1.pdf"
    TEST_PDF = "pdfs/test2.pdf"
    OUTPUT_DIR = "comparison_output"

    result_pdf = compare_two_pdfs(BASE_PDF, TEST_PDF, OUTPUT_DIR)
    print(f"Comparison complete. Output saved to: {result_pdf}")
