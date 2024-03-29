import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from io import StringIO

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
                # Skip if href is empty, None, an anchor, email link, or JavaScript action
                continue
            href = urljoin(url, href)
            href = ensure_scheme(href)  # Make sure the scheme is present
            href = normalize_url(href)  # Normalize the URL before validation and addition
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
user_input_url = st.text_input("Voer de website in om de tekst van alle pagina's binnen de opgegeven URL te scrapen.", "")

if user_input_url:
    user_input_url = normalize_url(user_input_url)  # Ensure the user input URL is normalized
    domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(user_input_url))
    domain = normalize_url(domain)  # Further normalize domain if necessary
    all_links, visited_urls = get_all_website_links(user_input_url, domain)
    
    scraped_data = StringIO()
    scraped_data.write(f"Scraped content van: {user_input_url}\n\n")
    
    for url in visited_urls:
        st.write(f"Tekst extraheren van: {url}")
        text = scrape_text(url)
        scraped_data.write(f"URL: {url}\n{text}\n\n")
    
    scraped_data.seek(0)
    scraped_data_bytes = scraped_data.getvalue().encode('utf-8')

    st.download_button(label="Download het tekst bestand",
                       data=scraped_data_bytes,
                       file_name="site.txt",
                       mime="text/plain")