import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from io import StringIO

def normalize_url(url):
    """
    Normalize a URL by removing 'www.' if present.
    """
    if url.startswith("www."):
        return url[4:]
    return url

def is_valid_url(url, domain):
    """
    Check if a URL is valid and belongs to the specified domain, 
    normalizing both the URL and the domain to handle 'www.' consistently.
    """
    parsed_url = urlparse(url)
    normalized_url_domain = normalize_url(parsed_url.netloc)
    normalized_domain = normalize_url(domain)
    return bool(parsed_url.netloc) and normalized_domain in normalized_url_domain

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
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
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

st.title("Website Scraper")
user_input_url = st.text_input("Vul de website in om te scrapen", "")

if user_input_url:
    domain = "{uri.scheme}://{uri.netloc}/".format(uri=urlparse(user_input_url))
    # Normalize domain to handle 'www.' prefix uniformly
    domain = normalize_url(domain)
    all_links, visited_urls = get_all_website_links(user_input_url, domain)
    
    scraped_data = StringIO()
    scraped_data.write(f"Scraped inhoud van: {user_input_url}\n\n")
    
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
