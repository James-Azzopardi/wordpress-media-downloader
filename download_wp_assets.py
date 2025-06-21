import os
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import phpserialize
import urllib3
from tqdm import tqdm

# --- CONFIG ---
XML_FILE = 'wordpress-export.xml'  # Path to your WP XML export
DOWNLOAD_DIR = 'wp-assets'         # Folder to save the assets
MAX_WORKERS = 8                    # Adjust for CPU/network

# Disable insecure SSL warnings (only for known/trusted sources)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Load and parse XML safely
try:
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
except Exception as e:
    print(f"[!] Failed to parse XML file '{XML_FILE}': {e}")
    exit(1)

# Namespaces required by WordPress XML
ns = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

# Parse serialized image size data
def extract_wp_image_sizes(meta_value_cdata):
    try:
        data = phpserialize.loads(meta_value_cdata.encode(), decode_strings=True)
        sizes = data.get('sizes', {})
        return [sizes[size]['file'] for size in sizes]
    except Exception as e:
        print(f"[!] Failed to parse wp:meta_value: {e}")
        return []

# Download file and preserve folder structure
def download_file(url):
    try:
        parsed = urlparse(url)
        path = parsed.path  # e.g. /wp-content/uploads/2008/05/example.jpg

        match = re.search(r'wp-content/uploads/(.+)', path)
        if not match:
            return  # Skip anything outside the uploads folder

        relative_path = match.group(1)  # e.g. 2008/05/example.jpg
        save_path = os.path.join(DOWNLOAD_DIR, relative_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        if os.path.exists(save_path):
            return  # Skip existing files

        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"[!] Failed to download {url}: {e}")

# Collect all URLs
urls_to_download = set()

# --- STEP 1: Media Library Attachments ---
for item in root.findall('./channel/item'):
    attachment_url = item.find('wp:attachment_url', ns)
    meta_elements = item.findall('wp:postmeta', ns)

    for meta in meta_elements:
        key = meta.find('wp:meta_key', ns)
        value = meta.find('wp:meta_value', ns)
        if key is not None and key.text == '_wp_attachment_metadata' and value is not None:
            sized_files = extract_wp_image_sizes(value.text)
            if attachment_url is not None and attachment_url.text:
                base_url = attachment_url.text.rsplit('/', 1)[0]
                urls_to_download.add(attachment_url.text)  # Add original image
                for filename in sized_files:
                    full_url = f"{base_url}/{filename}"
                    urls_to_download.add(full_url)

# --- STEP 2: Inline Content Image URLs ---
for item in root.findall('./channel/item'):
    content_encoded = item.find('content:encoded', ns)
    if content_encoded is not None and content_encoded.text:
        soup = BeautifulSoup(content_encoded.text, 'html.parser')
        for tag in soup.find_all(['img', 'a']):
            url = tag.get('src') or tag.get('href')
            if url and re.match(r'^https?://', url):
                urls_to_download.add(url)

# --- Download All Files (Threaded) ---
print(f"🔍 Found {len(urls_to_download)} unique assets to download.\n")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(download_file, url) for url in urls_to_download]
    for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading"):
        pass

print("\n✅ All downloads complete!")
