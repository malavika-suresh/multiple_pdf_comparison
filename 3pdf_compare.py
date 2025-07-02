import sys
import os
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QWidget, QTextEdit, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt
import fitz  # PyMuPDF

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_words(page: fitz.Page) -> List[Dict]:
    words = []
    try:
        word_list = page.get_text("words", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for word in word_list:
            if word[4].strip():
                words.append({"text": word[4], "rect": fitz.Rect(word[:4])})
    except Exception as e:
        logger.warning(f"Error extracting words from page {page.number}: {str(e)}")
    return words

def normalize_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text.strip().lower())
    return re.sub(r'[^\w\s]', '', text)

def highlight_differences(base_pdf_path: str, test_pdf_path: str, output_path: str,
                           highlight_color: Tuple[float, float, float] = (1, 0, 0),
                           max_pages: Optional[int] = None, chunk_size: int = 10) -> None:
    from difflib import SequenceMatcher
    start_time = time.time()
    try:
        with fitz.open(base_pdf_path) as base_doc, fitz.open(test_pdf_path) as test_doc:
            total_pages = min(len(base_doc), len(test_doc))
            if max_pages is not None:
                total_pages = min(total_pages, max_pages)

            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                for page_num in range(chunk_start, chunk_end):
                    try:
                        base_page = base_doc.load_page(page_num)
                        test_page = test_doc.load_page(page_num)

                        base_words = extract_words(base_page)
                        test_words = extract_words(test_page)

                        base_text = [normalize_text(word["text"]) for word in base_words]
                        test_text = [normalize_text(word["text"]) for word in test_words]

                        matcher = SequenceMatcher(None, base_text, test_text, autojunk=False)

                        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                            if tag != "equal":
                                for idx in range(j1, min(j2, len(test_words))):
                                    test_word = normalize_text(test_words[idx]["text"])
                                    if test_word in base_text:
                                        continue  # Skip highlighting if the word exists in base_text
                                    rect = test_words[idx]["rect"]
                                    try:
                                        highlight = test_page.add_highlight_annot(rect)
                                        highlight.set_colors(stroke=highlight_color)
                                        highlight.set_opacity(0.4)
                                        highlight.update()
                                    except Exception as e:
                                        logger.warning(f"Error highlighting on page {page_num + 1}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                        continue
            test_doc.save(output_path, garbage=4, deflate=True)
    except Exception as e:
        logger.error(f"Error in highlight_differences: {str(e)}")
        raise
    logger.info(f"Highlighting completed in {time.time() - start_time:.2f} seconds")

def merge_three_pdfs(base_pdf: str, pdf1: str, pdf2: str, output_path: str, dpi: int = 150):
    with fitz.open() as output_doc:
        docs = [fitz.open(p) for p in [base_pdf, pdf1, pdf2]]
        total_pages = min(len(d) for d in docs)

        for i in range(total_pages):
            pages = [d.load_page(i) for d in docs]
            widths = [p.rect.width for p in pages]
            heights = [p.rect.height for p in pages]
            total_width = sum(widths)
            max_height = max(heights)

            new_page = output_doc.new_page(width=total_width, height=max_height)

            x = 0
            for j, page in enumerate(pages):
                pix = page.get_pixmap(dpi=dpi)
                rect = fitz.Rect(x, 0, x + page.rect.width, page.rect.height)
                new_page.insert_image(rect, pixmap=pix)
                x += page.rect.width

        output_doc.save(output_path, garbage=4, deflate=True)

def compare_three_pdfs(base_pdf_path: str, test1_pdf_path: str, test2_pdf_path: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    highlighted1 = os.path.join(output_dir, f"highlighted_test1_{timestamp}.pdf")
    highlighted2 = os.path.join(output_dir, f"highlighted_test2_{timestamp}.pdf")
    merged_output = os.path.join(output_dir, f"comparison_merged_{timestamp}.pdf")

    highlight_differences(base_pdf_path, test1_pdf_path, highlighted1, (0.7, 1, 0.7))  # green
    highlight_differences(base_pdf_path, test2_pdf_path, highlighted2, (1, 0.7, 0.7))  # red
    merge_three_pdfs(base_pdf_path, highlighted1, highlighted2, merged_output)

    return merged_output

class PDFCompareApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 3-Way Comparison Tool")
        self.setGeometry(300, 100, 700, 500)
        self.base_path = None
        self.test1_path = None
        self.test2_path = None
        self.output_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header = QLabel("<h2>PDF Comparison Tool</h2><p>Compare two test PDFs against a base reference PDF</p>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
        layout.addWidget(self.log_box)

        self.base_button = self.create_file_selector("Select Base PDF", "base")
        self.test1_button = self.create_file_selector("Select Test PDF 1", "test1")
        self.test2_button = self.create_file_selector("Select Test PDF 2", "test2")

        layout.addWidget(self.base_button)
        layout.addWidget(self.test1_button)
        layout.addWidget(self.test2_button)

        self.compare_btn = QPushButton("Compare PDFs")
        self.compare_btn.setEnabled(False)
        self.compare_btn.clicked.connect(self.compare_pdfs)
        self.compare_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #0066cc; color: white;")
        layout.addWidget(self.compare_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_file_selector(self, label_text, file_type):
        frame = QFrame()
        h_layout = QHBoxLayout()

        label = QLabel(label_text)
        button = QPushButton("Browse")
        button.clicked.connect(lambda: self.select_file(file_type, button))
        button.setStyleSheet("padding: 5px;")

        h_layout.addWidget(label)
        h_layout.addWidget(button)
        frame.setLayout(h_layout)
        return frame

    def select_file(self, file_type, button):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            setattr(self, f"{file_type}_path", path)
            button.setText(Path(path).name)

        if self.base_path and self.test1_path and self.test2_path:
            self.compare_btn.setEnabled(True)

    def compare_pdfs(self):
        self.log_box.append("\nStarting 3-way comparison... Please wait...\n")
        try:
            self.output_path = compare_three_pdfs(
                base_pdf_path=self.base_path,
                test1_pdf_path=self.test1_path,
                test2_pdf_path=self.test2_path,
                output_dir="comparison_output"
            )
            self.log_box.append("\nSuccess!\nMerged comparison PDF saved to output folder.")
            # Reset selections
            self.base_path = None
            self.test1_path = None
            self.test2_path = None
            self.base_button.layout().itemAt(1).widget().setText("Browse")
            self.test1_button.layout().itemAt(1).widget().setText("Browse")
            self.test2_button.layout().itemAt(1).widget().setText("Browse")
            self.compare_btn.setEnabled(False)
        except Exception as e:
            self.log_box.append(f"\nError: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PDFCompareApp()
    window.show()
    sys.exit(app.exec_())
