import fitz 
from difflib import SequenceMatcher
import os
import re


def extract_words(page):
    words = []
    word_list = page.get_text("words") 
    for w in word_list:
        words.append({"text": w[4], "rect": fitz.Rect(w[:4])})
    return words


def highlight_word_differences(base_pdf_path, compare_pdf_path, output_path, color):
    base_doc = fitz.open(base_pdf_path)
    compare_doc = fitz.open(compare_pdf_path)

    for page_num in range(min(len(base_doc), len(compare_doc))):
        base_page = base_doc[page_num]
        compare_page = compare_doc[page_num]

        base_words = extract_words(base_page)
        compare_words = extract_words(compare_page)

        base_text = [re.sub(r'\s+', '', w["text"]) for w in base_words]
        compare_text = [re.sub(r'\s+', '', w["text"]) for w in compare_words]

        matcher = SequenceMatcher(None, base_text, compare_text)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("insert", "replace", "delete"):
                for idx in range(j1, j2):
                    if idx < len(compare_words):
                        rect = compare_words[idx]["rect"]
                        annot = compare_page.add_highlight_annot(rect)
                        annot.set_colors(stroke=color)
                        annot.update()

    compare_doc.save(output_path)
    base_doc.close()
    compare_doc.close()


def merge_horizontally(pdf_paths, output_path):
    pdf_docs = [fitz.open(p) for p in pdf_paths]
    num_pages = min([len(doc) for doc in pdf_docs])

    output = fitz.open()
    for i in range(num_pages):
        pages = [doc.load_page(i) for doc in pdf_docs]
        widths = [page.rect.width for page in pages]
        heights = [page.rect.height for page in pages]

        new_width = sum(widths)
        new_height = max(heights)
        new_page = output.new_page(width=new_width, height=new_height)

        x_offset = 0
        for page in pages:
            pix = page.get_pixmap(dpi=150)
            img_rect = fitz.Rect(x_offset, 0, x_offset + page.rect.width, page.rect.height)
            new_page.insert_image(img_rect, pixmap=pix)
            x_offset += page.rect.width

    output.save(output_path)
    output.close()
    for doc in pdf_docs:
        doc.close()


def compare_pdfs(pdf1_path, pdf2_path, pdf3_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    pdf2_highlighted = os.path.join(output_dir, "pdf2_highlighted.pdf")
    pdf3_highlighted = os.path.join(output_dir, "pdf3_highlighted.pdf")

    highlight_word_differences(pdf1_path, pdf2_path, pdf2_highlighted, (1, 0, 0))  # Red
    highlight_word_differences(pdf1_path, pdf3_path, pdf3_highlighted, (0, 1, 0))  # Green

    merge_horizontally(
        [pdf1_path, pdf2_highlighted, pdf3_highlighted],
        os.path.join(output_dir, "combined_output.pdf")
    )

    print(f"✅ Comparison complete. Output saved at: {output_dir}/combined_output.pdf")


if __name__ == "__main__":
    pdf1 = r"test1.pdf"
    pdf2 = r"test2.pdf"
    pdf3 = r"test3.pdf"
    output_directory = "comparison_results"
    compare_pdfs(pdf1, pdf2, pdf3, output_directory)
