import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import WORKER_URL, USER_AGENTS

BASE_URL = "https://www.tokyoinsider.com"

def get_random_headers():
    """Returns randomized headers for HTTP requests to mimic browser behavior.
    
    Returns:
        dict: Dictionary containing request headers with random User-Agent.
    """
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': f'{BASE_URL}/',
        'DNT': '1',
    }

def fetch_page_content(url):
    """Fetches page content through Cloudflare Worker.
    
    Args:
        url (str): URL to fetch content from
        
    Returns:
        BeautifulSoup: Parsed HTML content or None if request fails
    """
    try:
        response = requests.get(
            f"{WORKER_URL}?url={url}",
            headers=get_random_headers()
        )
        response.encoding = 'utf-8'
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

def parse_download_entry(entry):
    """Extracts download information from a single entry div.
    
    Args:
        entry (bs4.element.Tag): BeautifulSoup tag containing download entry
        
    Returns:
        dict: Parsed download information or None if invalid entry
    """
    main_div = entry.find('div')
    if not main_div:
        return None
        
    download_link_tag = main_div.find('a', href=lambda x: x and not x.endswith('/comment'))
    if not download_link_tag:
        return None
    
    # Extract basic info
    title = download_link_tag.text.strip()
    download_link = download_link_tag['href']
    if not download_link.startswith('http'):
        download_link = f"{BASE_URL}{download_link}"
    
    # Extract file metadata
    finfo = entry.find(class_='finfo')
    language_span = finfo.find('span') if finfo else None
    language = language_span['class'][0] if language_span and language_span.has_attr('class') else "N/A"
    
    # Process file info text
    size, added_on = "N/A", "N/A"
    if finfo:
        info_text = finfo.get_text(separator='|').split('|')
        info = [item.strip() for item in info_text if item.strip()]
        
        for i, item in enumerate(info):
            if item.startswith('Size:'):
                size = info[i+1] if i+1 < len(info) else "N/A"
            elif item.startswith('Added On:'):
                added_on = info[i+1] if i+1 < len(info) else "N/A"
    
    return {
        'title': title,
        'download_link': download_link,
        'size': size,
        'language': language,
        'added_on': added_on
    }

def parse_navigation_links(soup):
    """Extracts previous and next episode links from navigation div.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        tuple: (previous_episode_url, next_episode_url)
    """
    nav_div = soup.find('div', class_='fsplit')
    if not nav_div:
        return None, None
    
    def process_link(link):
        if link and link['href']:
            url = link['href']
            return url if url.startswith('http') else f"{BASE_URL}{url}"
        return None
    
    prev_link = nav_div.find('a', class_='nfl')
    next_link = nav_div.find('a', class_='nfr')
    
    return process_link(prev_link), process_link(next_link)

def extract_download_links(url):
    """Main function to extract download links and episode navigation from a page.
    
    Args:
        url (str): URL of the page to scrape
        
    Returns:
        dict: Dictionary containing downloads list and navigation links, or None if failed
    """
    soup = fetch_page_content(url)
    if not soup:
        return None
    
    # Parse all download entries
    download_entries = soup.find_all(class_=['c_h2', 'c_h2b'])
    results = [entry for entry in (parse_download_entry(e) for e in download_entries) if entry]
    
    # Parse navigation links
    prev_ep, next_ep = parse_navigation_links(soup)
    
    return {
        'downloads': results,
        'prev_ep': prev_ep,
        'next_ep': next_ep
    }
