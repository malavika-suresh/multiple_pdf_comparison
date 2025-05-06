<h1 style="color:blue; font-weight:bold;">PDF Comparison and Highlighting Tool</h1>

This Python-based tool allows for efficient comparison of two or more PDF documents, highlighting the differences between them.
It extracts and compares the words in the PDFs, ignoring whitespace differences, and highlights the changed, added, or missing words.

<h2 style="color:black; font-weight:bold;">Features:</h2>

- **Word-based Comparison:** Compares text from two or more PDFs, highlighting only added, modified, or deleted words.
- **Whitespace Ignored:** Ignores any differences in whitespace, focusing only on actual word changes.
- **Precise Highlighting:** Highlights the differences in the compared PDF files using custom colors (e.g., red for PDF2 and green for PDF3).
- **Side-by-Side Merging:** Merges the original and highlighted PDFs side by side for easy comparison.

<h2 style="color:black; font-weight:bold;">Usage:</h2>

- Provide paths to the PDF files to be compared.
- The tool will extract words from the PDFs, compare them, and highlight the differences.
- It saves the highlighted PDFs and a merged output with the original and highlighted PDFs placed side by side for an easy visual comparison.

<h2 style="color:black; font-weight:bold;">Dependencies:</h2>

- PyMuPDF (fitz)
- difflib (standard Python library)

<h2 style="color:black; font-weight:bold;">Example Output:</h2>

- **Original PDF:** The untouched source document.
- **Highlighted PDF:** PDFs with added, changed, or missing words highlighted in different colors.
- **Combined Output:** A single PDF containing the original and highlighted versions side by side.

<h2 style="color:black; font-weight:bold;">Result:</h2>

![combined_output_page-0001](https://github.com/user-attachments/assets/bb34330f-fbbf-465e-980e-95fddc5d2538)
