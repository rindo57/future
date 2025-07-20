import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import WORKER_URL, USER_AGENTS

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


def extract_episode_links(url):
    response = requests.get(url, headers=get_random_headers())
    response.encoding = 'utf-8'
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    anime_data = []

    for td in soup.find_all("div", class_=["episode c_h2", "episode c_h2b"]):
        a_tag = td.find("a", href=True)
        if a_tag and a_tag.text.strip():
            title = a_tag.text.strip()
           
            if title.startswith("upload"):
                continue
            i_tag = td.find("i")
            if i_tag:
                subtitle = i_tag.text.strip()
                if subtitle.startswith(":"):
                    subtitle = subtitle[1:].strip()
                title = f"{title} - {subtitle}"
            full_url = urljoin(url, a_tag["href"])
            anime_data.append({
                "title": title,
                "url": full_url
            })

    return anime_data

def extract_main_links(url):
    response = requests.get(url, headers=get_random_headers())
    response.encoding = 'utf-8'
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    anime_data = []

    for td in soup.find_all("td", class_=["c_h2", "c_h2b"]):
        a_tag = td.find("a", href=True)
        if a_tag and a_tag.text.strip():  # Ensure title is not empty
            title = a_tag.text.strip()
            full_url = urljoin(url, a_tag["href"])
            anime_data.append((title, full_url))

    return anime_data
