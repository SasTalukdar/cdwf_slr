#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 10 11:49:58 2025

@author: sasankatalukdar
"""

import json
import os
import re
import nltk
from nltk.corpus import words
import requests
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from elsapy.elsclient import ElsClient
from elsapy.elsdoc import FullDoc
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import pandas as pd

# Optional import for clipboard functionality
try:
    import pyperclip
except ImportError:
    pass

# Ensure the NLTK words corpus is available
nltk.download('words', quiet=True)
english_words = set(words.words())

# Configuration
MY_PATH = '/Users/sasankatalukdar/sas/cdwf_slr/RIS_ToFetchAbstract_04Apr2025_Sasanka/'
FNAME = "Tag03_04.json"
OUTPUT_FILES = {
    "linter": os.path.join(MY_PATH, "linter_fetched.json"),
    "api": os.path.join(MY_PATH, "api_fetched.json"),
    "selenium": os.path.join(MY_PATH, "selenium_fetched.json"),
    "manual": os.path.join(MY_PATH, "manual_fetched.json"),
    "not_available": os.path.join(MY_PATH, "abstract_not_available.json"),
    "non_article": os.path.join(MY_PATH, "non_article_datasets.json")
}

CONFIG_FILES = {
    "elsevier": f"{MY_PATH}elsevier_config.json",
    "springer": f"{MY_PATH}springer_config.json",  # Kept for compatibility, overridden by SPRINGER_CONFIGS
    "wiley": f"{MY_PATH}wiley_config.json"
}
SPRINGER_CONFIGS = [
    f"{MY_PATH}springer_config1.json",
    f"{MY_PATH}springer_config2.json",
    f"{MY_PATH}springer_config3.json",
    # Add more as needed
]
PUBLISHER_DOMAINS = {
    "elsevier.com": "elsevier",
    "springer.com": "springer",
    "wiley.com": "wiley"
}

# Springer API key management
springer_key_index = 0
springer_request_count = 0
MAX_REQUESTS_PER_KEY = 500

# ----------------------
# Helper Functions
# ----------------------
def load_existing_outputs(output_files):
    """Load URLs from existing output JSON files."""
    processed_urls = set()
    all_papers = []
    #change into keys
    for key, file_path in output_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    papers = json.load(f)
                    for paper in papers:
                        url = paper.get('URL')
                        paper['abstract_status']=key
                        if url:
                            processed_urls.add(url)
                        all_papers.append(paper)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    return processed_urls, all_papers

# ----------------------
# API Functions
# ----------------------
def get_springer_config():
    global springer_key_index, springer_request_count
    if springer_request_count >= MAX_REQUESTS_PER_KEY:
        springer_key_index += 1
        springer_request_count = 0
    if springer_key_index < len(springer_configs):
        springer_request_count += 1
        return springer_configs[springer_key_index]
    else:
        return None

def load_config(publisher):
    config_file = CONFIG_FILES.get(publisher.lower())
    if not config_file or not os.path.exists(config_file):
        raise ValueError(f"Config file for {publisher} not found at {config_file}")
    with open(config_file) as con_file:
        config = json.load(con_file)
    if 'apikey' not in config:
        raise ValueError(f"API key missing in {publisher} config")
    return config

def get_publisher(url):
    for domain in PUBLISHER_DOMAINS:
        if domain in url:
            return PUBLISHER_DOMAINS[domain]
    return None

def fetch_elsevier_abstract(paper, client):
    if "URL" in paper and "elsevier.com" in paper["URL"]:
        pii = paper["URL"].split("/")[-1]
        pii_doc = FullDoc(sd_pii=pii)
        if pii_doc.read(client):
            return pii_doc.data["coredata"].get("dc:description", None)
    return None

def fetch_springer_abstract(paper, config):
    if "URL" in paper and "springer.com" in paper["URL"]:
        doi_match = re.search(r"10\.\d{4,9}/.+", paper["URL"])
        if doi_match:
            doi = doi_match.group(0)
            api_url = f"https://api.springernature.com/meta/v2/json?q=doi:{doi}&api_key={config['apikey']}"
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get('records'):
                    return data['records'][0].get("abstract", None)
            except requests.RequestException as e:
                print(f"Springer API error: {e}")
    return None

def fetch_wiley_abstract(paper, config):
    if "URL" in paper and "wiley.com" in paper["URL"]:
        doi = paper["URL"].split("/doi/")[-1].strip("/")
        base_url = "https://api.wiley.com/onlinelibrary/metadata/v1/articles"
        try:
            response = requests.get(f"{base_url}?doi={doi}&apiKey={config['apikey']}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if "articles" in data and data["articles"]:
                return data["articles"][0].get("abstract", None)
        except requests.RequestException as e:
            print(f"Wiley API error: {e}")
    return None

def fetch_abstract_api(paper, configs):
    """Fetch abstract for a single paper using the appropriate API."""
    url = paper.get('URL')
    if not url:
        return None
    publisher = get_publisher(url)
    if not publisher:
        return None
    config = configs.get(publisher)
    if not config:
        return None
    try:
        if publisher == "elsevier":
            client = ElsClient(config['apikey'])
            return fetch_elsevier_abstract(paper, client)
        elif publisher == "springer":
            return fetch_springer_abstract(paper, config)
        elif publisher == "wiley":
            return fetch_wiley_abstract(paper, config)
    except Exception as e:
        print(f"Error fetching abstract for {url}: {e}")
    return None

# ----------------------
# Selenium & Abstract Extraction Functions
# ----------------------
def extract_abstract(text, min_word_count=50):
    paragraphs = text.split('\n')
    abstract_paragraphs = []
    for para in paragraphs:
        stripped_para = para.strip()
        if not stripped_para:
            continue
        cleaned = re.sub(r'[\d\W_]+', ' ', stripped_para)
        word_list = cleaned.lower().split()
        filtered_words = [word for word in word_list if word in english_words]
        if len(filtered_words) >= min_word_count:
            abstract_paragraphs.append(stripped_para)
        elif abstract_paragraphs:
            break
    return '\n'.join(abstract_paragraphs) if abstract_paragraphs else None

def setup_selenium(headless=True):
    service = Service()  # Set executable_path if needed
    options = webdriver.ChromeOptions()
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def process_selenium_url(url):
    """Process a single URL using Selenium and return the extracted abstract."""
    print(f"[Process] Processing URL: {url}")
    driver = setup_selenium(headless=False)  # Always interactive now
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        input(f"Solve any CAPTCHAs for {url} and press Enter to continue...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as temp_file:
            temp_file.write(text)
            print(f"[Process] Saved raw text to {temp_file.name}")
        abstract = extract_abstract(text)
        return abstract
    except Exception as e:
        print(f"[Process] Error processing {url}: {e}")
        return None
    finally:
        driver.quit()

def save_all_datasets(article_journals, non_article_journals):
    """Save datasets based on abstract_status."""
    api_fetched = [paper for paper in article_journals if paper.get('abstract_status') == 'api']
    selenium_fetched = [paper for paper in article_journals if paper.get('abstract_status') == 'selenium']
    manual_fetched = [paper for paper in article_journals if paper.get('abstract_status') == 'manual']
    abstract_not_available = [paper for paper in article_journals if paper.get('abstract_status') == 'not_available']
    non_article_datasets = non_article_journals

    with open(OUTPUT_FILES["api"], "w") as f:
        json.dump(api_fetched, f, indent=4)
    with open(OUTPUT_FILES["selenium"], "w") as f:
        json.dump(selenium_fetched, f, indent=4)
    with open(OUTPUT_FILES["manual"], "w") as f:
        json.dump(manual_fetched, f, indent=4)
    with open(OUTPUT_FILES["not_available"], "w") as f:
        json.dump(abstract_not_available, f, indent=4)
    with open(OUTPUT_FILES["non_article"], "w") as f:
        json.dump(non_article_datasets, f, indent=4)

    print(f"\nSaved: API={len(api_fetched)}, Selenium={len(selenium_fetched)}, Manual={len(manual_fetched)}, Not Available={len(abstract_not_available)}, Non-Article={len(non_article_datasets)}")

# Main Process
if __name__ == "__main__":
    # Load existing processed URLs from output files
    processed_urls, existing_papers = load_existing_outputs(OUTPUT_FILES)
    print(f"Found {len(processed_urls)} URLs already processed in output files.")
    
    # Load JSON data
    try:
        with open(os.path.join(MY_PATH, FNAME)) as json_file:
            data = json.load(json_file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        exit(1)
    
    #exclude existing urls from data
    data=[paper for paper in data if paper.get('URL') not in processed_urls]
    #add abstract data
    data=data+existing_papers
    
    # Separate article journals and non-article journals
    article_journals = [paper for paper in data if paper.get('type') == 'article-journal']  
    non_article_journals = [paper for paper in data if paper.get('type') != 'article-journal']
    
    # Separate already available abstracts
    if len(processed_urls)==0:
        linter_articles = [paper for paper in article_journals if 'abstract' in paper]
        with open(os.path.join(MY_PATH, "linter_fetched.json"), "w") as f:
            json.dump(linter_articles, f, indent=4)
    
    print(f"Remaining article journals to process: {len([p for p in article_journals if 'abstract' not in p and p.get('URL')])}")
    print(f"Total non-article journals: {len(non_article_journals)}")

    # Load all publisher configs once
    configs = {}
    springer_configs = []

    # Load non-Springer configs
    for publisher in set(PUBLISHER_DOMAINS.values()) - {"springer"}:
        try:
            configs[publisher] = load_config(publisher)
        except ValueError as e:
            print(e)
            exit(1)

    # Load Springer configs
    for config_file in SPRINGER_CONFIGS:
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
                if 'apikey' in config:
                    springer_configs.append(config)
                else:
                    print(f"API key missing in {config_file}")
        else:
            print(f"Config file {config_file} not found")

    if not springer_configs:
        print("No valid Springer config files found. Springer API fetching will be skipped.")

    # Step 1: Parallel API Fetching
    selenium_urls = []
    papers_to_process = [paper for paper in article_journals if 'abstract' not in paper and paper.get('URL')]

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_paper = {}
        for paper in papers_to_process:
            publisher = get_publisher(paper.get('URL'))
            if publisher == "springer":
                config = get_springer_config()
                if config:
                    future = executor.submit(fetch_abstract_api, paper, {"springer": config})
                    future_to_paper[future] = paper
                else:
                    print(f"No more Springer API keys available for {paper.get('URL')}. Skipping to Selenium.")
                    selenium_urls.append(paper.get('URL'))
            else:
                future = executor.submit(fetch_abstract_api, paper, configs)
                future_to_paper[future] = paper

        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                abstract = future.result()
                if abstract:
                    paper['abstract'] = abstract
                    paper['abstract_status'] = 'API'
                    print(f"Fetched abstract for {paper.get('id', 'unknown')} via API.")
                else:
                    selenium_urls.append(paper.get('URL'))
            except Exception as exc:
                print(f"Error processing {paper.get('URL')}: {exc}")
                selenium_urls.append(paper.get('URL'))

    # Handle papers without URLs
    for paper in article_journals:
        if 'abstract' not in paper and not paper.get('URL'):
            print(f"Paper {paper.get('id', 'unknown')} has no URL.")

    # Collect URLs needing Selenium processing
    missing_abstract_urls = [paper.get('URL') for paper in article_journals if 'abstract' not in paper and paper.get('URL')]

    # Step 2: Interactive Selenium Processing
    if missing_abstract_urls:
        print("\nStarting interactive Selenium processing...")
        for i, url in enumerate(missing_abstract_urls, start=1):
            print(f"\n[Interactive] Processing URL {i}/{len(missing_abstract_urls)}: {url}")
            driver = setup_selenium(headless=False)
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                input(f"Solve any CAPTCHAs for {url}, accept Cookies, and press Enter to continue...")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                abstract = extract_abstract(text)
                if abstract:
                    print(f"Extracted abstract: {abstract}")
                else:
                    print("No abstract extracted.")

                while True:
                    choice = input("Press Enter to accept, 'p' to paste from clipboard, 'm' for manual, 'g' for Google Scholar, 'n' for not available, 'r' for non-article: ").strip().lower()
                    if choice == '' and abstract:
                        for paper in article_journals:
                            if paper.get('URL') == url:
                                paper['abstract'] = abstract
                                paper['abstract_status'] = 'Selenium'
                                break
                        break
                    elif choice == 'g':
                        title = paper.get('title', '').replace(' ', '+')
                        # scholar_url = f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={title}&btnG="
                        scholar_url = f"https://scholar.google.com/"
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                            df = pd.DataFrame([{'Source': scholar_url, 'SelectedText': '', 'Check': 0}])
                            df.to_csv(temp_csv.name, index=False)
                            csv_path = temp_csv.name
                        subprocess.run(['python', 'manual_extractor.py', csv_path])
                        df = pd.read_csv(csv_path)
                        selected_text = df.at[0, 'SelectedText']
                        check = df.at[0, 'Check']
                        for paper in article_journals:
                            if paper.get('URL') == scholar_url:
                                if check == 1 and selected_text:
                                    confirm = input("Was manual extraction successful? (y/n): ").strip().lower()
                                    if confirm == 'y':
                                        paper['abstract'] = selected_text
                                        paper['abstract_status'] = 'Manual'
                                    else:
                                        paper['abstract_status'] = 'Not Available'
                                else:
                                    paper['abstract_status'] = 'Not Available'
                                break
                        os.unlink(csv_path)
                        break
                        
                    elif choice == 'm':
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                            df = pd.DataFrame([{'Source': url, 'SelectedText': '', 'Check': 0}])
                            df.to_csv(temp_csv.name, index=False)
                            csv_path = temp_csv.name
                        subprocess.run(['python', 'manual_extractor.py', csv_path])
                        df = pd.read_csv(csv_path)
                        selected_text = df.at[0, 'SelectedText']
                        check = df.at[0, 'Check']
                        for paper in article_journals:
                            if paper.get('URL') == url:
                                if check == 1 and selected_text:
                                    confirm = input("Was manual extraction successful? (y/n): ").strip().lower()
                                    if confirm == 'y':
                                        paper['abstract'] = selected_text
                                        paper['abstract_status'] = 'Manual'
                                    else:
                                        paper['abstract_status'] = 'Not Available'
                                else:
                                    paper['abstract_status'] = 'Not Available'
                                break
                        os.unlink(csv_path)
                        break
                    elif choice == 'n':
                        for paper in article_journals:
                            if paper.get('URL') == url:
                                paper['abstract_status'] = 'Not Available'
                                break
                        break
                    elif choice == 'r':
                        for paper in article_journals:
                            if paper.get('URL') == url:
                                article_journals.remove(paper)
                                non_article_journals.append(paper)
                                break
                        break
                    elif choice == 'p':
                        try:
                            selected_text = pyperclip.paste()
                            print("Pasted abstract from clipboard:")
                            print(selected_text)
                        except (ImportError, NameError):
                            print("pyperclip not installed or unavailable. Falling back to multi-line input.")
                            print("Please copy and paste the abstract (type 'DONE' on a new line when finished):")
                            lines = []
                            while True:
                                line = input()
                                if line.strip().lower() == 'done':
                                    break
                                lines.append(line)
                            selected_text = '\n'.join(lines)
                            print("Entered abstract:")
                            print(selected_text)
                        for paper in article_journals:
                            if paper.get('URL') == url:
                                paper['abstract'] = selected_text
                                paper['abstract_status'] = 'Manual'
                                break
                        break
                    else:
                        print("Invalid choice. Please try again.")
            except Exception as e:
                print(f"Error processing {url}: {e}")
            finally:
                driver.quit()
            save_all_datasets(article_journals, non_article_journals)
            time.sleep(2)  # Brief pause between URLs

    # Final save
    save_all_datasets(article_journals, non_article_journals)
    print("\nProcessing complete.")