import concurrent.futures
from bs4 import BeautifulSoup
import requests
import json
import os

def get_links_and_content(url):
    try:
        print(f"Fetching: {url}")
        response = requests.get(url)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return links, str(soup)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return [], ""

def clean_links(domain, links):
    clean_links = [
        link for link in links
        if link.startswith('/') or link.startswith(domain)
    ]
    full_links = [
        link if link.startswith(domain) else domain + link
        for link in clean_links
    ]
    return full_links

def find_all_links(start_url, domain, all_data):
    all_links = set(all_data.keys())
    new_links = set([start_url]) | all_links  # Add all known links to the queue
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        while new_links:
            futures = {executor.submit(get_links_and_content, link): link for link in new_links}
            new_links = set()
            
            for future in concurrent.futures.as_completed(futures):
                link = futures[future]  # Retrieve the URL associated with this future
                page_links, page_content = future.result()
                full_links = clean_links(domain, page_links)
                
                for link in full_links:
                    if link not in all_links:
                        all_links.add(link)
                        new_links.add(link)
                        
                # Updating existing links with the new content
                all_data[link] = page_content  
                        
    return all_data


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

url = 'https://www.oref.org.il/'
domain = 'https://www.oref.org.il/'

# Load previously fetched data if it exists
all_data = load_from_json('data.json')

# Find all links and update all_data
all_data = find_all_links(url, domain, all_data)
print(f"Found {len(all_data)} pages")

# Save data to a JSON file
save_to_json(all_data, 'data.json')
