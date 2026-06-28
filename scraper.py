import os
import time
import random
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Strict Storage Directory Layout Setup
BASE_OUTPUT_DIR = "tn_agri_data"
TEXT_DIR = os.path.join(BASE_OUTPUT_DIR, "text")
PDF_DIR = os.path.join(BASE_OUTPUT_DIR, "pdfs")

os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_scheme_links():
    """
    Evaluates the main portal index table and extracts the map of 56 scheme deep links.
    """
    target_url = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="
    base_portal_url = "https://www.tn.gov.in"
    extracted_schemes = []

    print("[*] Launching browser session to discover index links...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = context.new_page()
        
        try:
            page.goto(target_url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
            
            soup = BeautifulSoup(page.content(), "html.parser")
            
            for anchor in soup.find_all("a", href=True):
                href_value = anchor["href"]
                text_value = anchor.get_text(strip=True)
                
                is_scheme_link = any(term in href_value.lower() for term in ["scheme", "detail", "view"])
                if is_scheme_link and text_value:
                    full_url = href_value if href_value.startswith("http") else f"{base_portal_url}/{href_value.lstrip('/')}"
                    if "scheme_list.php" in full_url:
                        continue
                    if full_url not in [link for _, link in extracted_schemes]:
                        extracted_schemes.append((text_value, full_url))
                        
            print(f"[✓] Structural Discovery Complete: Found {len(extracted_schemes)} valid schemes.")
        except Exception as e:
            print(f"[!] Target Error mapping portal: {str(e)}")
        finally:
            browser.close()
            
    return extracted_schemes


def process_and_save_sub_page(title, url):
    """
    Visits an isolated scheme sub-page, extracts clean textual details, 
    and checks for downstream PDF download links.
    """
    # Create a safe file prefix name from the scheme title
    safe_title = "".join([c if c.isalnum() else "_" for c in title])[:60].strip("_")
    print(f"[*] Processing Content: '{title}'")
    
    try:
        # Use simple requests with strict timeouts for reading text content pages
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"    [!] Failed to pull page. HTTP Status Code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Target main body or scheme information container specifically to ignore header clutter
        # TN Portal wraps data within main body segments or tabular structures
        main_body = soup.find("div", {"id": "content"}) or soup.find("main") or soup.find("table") or soup.body
        
        if main_body:
            # Drop unnecessary text elements if they are found in headers/nav maps
            clean_text = main_body.get_text(separator="\n", strip=True)
            
            # 1. Save Clean Raw Text Document
            text_file_path = os.path.join(TEXT_DIR, f"{safe_title}.txt")
            with open(text_file_path, "w", encoding="utf-8") as text_file:
                text_file.write(f"Source Link Matrix: {url}\n")
                text_file.write(f"Official Scheme Name: {title}\n")
                text_file.write("-" * 50 + "\n\n")
                text_file.write(clean_text)
            print(f"    [✓] Extracted text saved to: {text_file_path}")
            
            # 2. Look for nested PDF circular attachments within the text block
            for link in main_body.find_all("a", href=True):
                href = link["href"].lower()
                if href.endswith(".pdf"):
                    pdf_url = link["href"] if link["href"].startswith("http") else f"https://www.tn.gov.in/{link['href'].lstrip('/')}"
                    download_attached_pdf(pdf_url, safe_title)
                    
    except Exception as e:
        print(f"    [!] Framework failure parsing scheme page details: {str(e)}")


def download_attached_pdf(pdf_url, base_filename):
    """
    Safely downloads and stores any target binary policy PDF documents.
    """
    try:
        print(f"    [*] Found PDF Attachment. Downloading: {pdf_url}")
        res = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=40)
        if res.status_code == 200:
            unique_stamp = int(time.time() * 1000) % 10000
            pdf_filename = f"{base_filename}_{unique_stamp}.pdf"
            pdf_path = os.path.join(PDF_DIR, pdf_filename)
            
            with open(pdf_path, "wb") as pdf_file:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        pdf_file.write(chunk)
            print(f"    [✓] Binary PDF Document Ingested: {pdf_path}")
    except Exception as e:
        print(f"    [!] Failed parsing download for PDF target {pdf_url}: {str(e)}")


if __name__ == "__main__":
    scheme_targets = get_scheme_links()
    
    if not scheme_targets:
        print("[!] No active links were discovered. Exiting extraction safety flow.")
    else:
        print(f"\n[*] Starting deep-dive extraction of {len(scheme_targets)} paths. Please wait...")
        for index, (title, url) in enumerate(scheme_targets, 1):
            print(f"\n[Progress: {index}/{len(scheme_targets)}]")
            process_and_save_sub_page(title, url)
            
            # Throttling delay: Crucial guard against crashing government portal nodes
            time.sleep(random.uniform(1.0, 2.5))
            
        print("\n[✓][✓] Ingestion Scraping Phase Finished successfully.")