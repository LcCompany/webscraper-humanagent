import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from io import StringIO
import threading

# Ensure the URL has a scheme; default to https if not.
def ensure_scheme(url):
    if not urlparse(url).scheme:
        return "https://" + url
    return url

# Normalize a URL by ensuring it has a scheme and removing 'www.' if present.
def normalize_url(url):
    url = ensure_scheme(url)  # Ensure the URL has a scheme
    parts = urlparse(url)
    netloc = parts.netloc.replace("www.", "")  # Reconstruct the URL without 'www.'
    return parts._replace(netloc=netloc).geturl()

# Check if a URL is valid and belongs to the specified domain.
def is_valid_url(url, domain):
    parsed_url = urlparse(url)
    normalized_domain = normalize_url(domain)
    return parsed_url.scheme in ('http', 'https') and normalized_domain in normalize_url(parsed_url.netloc)

# Get all website links that are valid and belong to the specified domain.
def get_all_website_links(url, domain):
    urls = set()
    visited_urls = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None or '#' in href or href.startswith('mailto:') or href.startswith('javascript:'):
                continue
            href = urljoin(url, href)
            href = ensure_scheme(href)
            href = normalize_url(href)
            if not is_valid_url(href, domain):
                continue
            if href in visited_urls:
                continue
            urls.add(href)
            visited_urls.add(href)
    except Exception as e:
        st.error(f"Error occurred: {e}")
    return urls, visited_urls

# Scrape text from a URL.
def scrape_text(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = ' '.join([p.text for p in soup.find_all('p')])
        return re.sub(r'\s+', ' ', text)
    except Exception as e:
        st.error(f"Error scraping {url}: {e}")
        return ""

# Scrape site function to be run in a separate thread.
def scrape_site(session_state, url, domain):
    urls, visited_urls = get_all_website_links(url, domain)
    
    scraped_data = StringIO()
    scraped_data.write(f"Scraped content from: {url}\n\n")
    
    for url in visited_urls:
        if not session_state.running:
            break
        st.write(f"Extracting text from: {url}")  # Optional: for real-time updates in the UI
        text = scrape_text(url)
        scraped_data.write(f"URL: {url}\n{text}\n\n")
    
    scraped_data.seek(0)
    session_state.scraped_data_bytes = scraped_data.getvalue().encode('utf-8')

# Streamlit UI setup
st.title("Website Scraper")
user_input_url = st.text_input("Enter the website URL you want to scrape.", "")

if 'running' not in st.session_state:
    st.session_state.running = False
    st.session_state.scraped_data_bytes = None

start = st.button("Start")
stop = st.button("Stop")

if start and not st.session_state.running:
    st.session_state.running = True
    user_input_url = normalize_url(user_input_url)
    domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(user_input_url))
    domain = normalize_url(domain)
    # Use threading to allow scraping in the background
    thread = threading.Thread(target=scrape_site, args=(st.session_state, user_input_url, domain))
    thread.start()

if stop:
    st.session_state.running = False

if 'scraped_data_bytes' in st.session_state and st.session_state.scraped_data_bytes:
    st.download_button(label="Download the text file",
                       data=st.session_state.scraped_data_bytes,
                       file_name="scraped_website_content.txt",
                       mime="text/plain")
