import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from io import StringIO
import threading

def ensure_scheme(url):
    """
    Ensure the URL has a scheme; default to https if not.
    """
    if not urlparse(url).scheme:
        return "https://" + url
    return url

def normalize_url(url):
    """
    Normalize a URL by ensuring it has a scheme and removing 'www.' if present.
    The function returns the URL with the scheme and without 'www.'.
    """
    url = ensure_scheme(url)  # Ensure the URL has a scheme
    parts = urlparse(url)
    netloc = parts.netloc.replace("www.", "")
    # Reconstruct the URL without 'www.'
    return parts._replace(netloc=netloc).geturl()

def is_valid_url(url, domain):
    """
    Check if a URL is valid and belongs to the specified domain.
    This function assumes both URL and domain are normalized.
    """
    parsed_url = urlparse(url)
    normalized_domain = normalize_url(domain)
    return parsed_url.scheme in ('http', 'https') and normalized_domain in normalize_url(parsed_url.netloc)

def scrape_site(session_state, url, domain):
    urls, visited_urls = get_all_website_links(url, domain)
    
    scraped_data = StringIO()
    scraped_data.write(f"Scraped content van: {url}\n\n")
    
    for url in visited_urls:
        if not session_state.running:
            break
        text = scrape_text(url)
        scraped_data.write(f"URL: {url}\n{text}\n\n")
    
    scraped_data.seek(0)
    session_state.scraped_data_bytes = scraped_data.getvalue().encode('utf-8')

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

# Streamlit UI
st.title("Website Scraper")
user_input_url = st.text_input("Voer de website in die je wilt scrapen.", "")

if not 'running' in st.session_state:
    st.session_state.running = False

if st.button("Start") and not st.session_state.running:
    st.session_state.running = True
    user_input_url = normalize_url(user_input_url)
    domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(user_input_url))
    domain = normalize_url(domain)
    # Use threading to allow scraping in the background
    thread = threading.Thread(target=scrape_site, args=(st.session_state, user_input_url, domain))
    thread.start()

if st.button("Stop"):
    st.session_state.running = False

if 'scraped_data_bytes' in st.session_state and st.session_state.scraped_data_bytes:
    st.download_button(label="Download het tekst bestand",