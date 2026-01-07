import pdfplumber

def extract_text(pdf_path, output_txt):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(text)

    print("PDF text extracted successfully.")

if __name__ == "__main__":
    extract_text("IAPR_Review_1.pdf", "IAPR_Review_1.txt")
