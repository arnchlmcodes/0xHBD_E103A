import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

BOOK_PAGE = "https://ncert.nic.in/textbook.php?fegp1=2-10"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/143.0.0.0 Safari/537.36"
}

def fetch_page(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.text

def extract_pdf_links(book_page_url):
    html = fetch_page(book_page_url)
    soup = BeautifulSoup(html, "html.parser")
    pdf_links = []

    # Look for all <a> tags with href containing 'fegp1' or 'instruction.pdf'
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        if "instruction.pdf" in href:
            pdf_links.append(urljoin(book_page_url, href))
            continue
        if "fegp1" in href:
            # extract chapter number from query params
            parsed = urlparse(href)
            query_params = parse_qs(parsed.query)
            book_code = list(query_params.keys())[0]
            value = query_params[book_code][0]  # e.g., "1-10"
            if "-" in value:
                ss, _ = value.split('-')
                pdf_url = f"https://ncert.nic.in/textbook/pdf/{book_code}{ss}.pdf"
                pdf_links.append(pdf_url)
    return pdf_links

if __name__ == "__main__":
    pdfs = extract_pdf_links(BOOK_PAGE)
    print("Found PDF links:\n")
    for url in pdfs:
        print(url)
