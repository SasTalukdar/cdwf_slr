#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 20:34:19 2024

@author: sasankatalukdar
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
import warnings
from random import random

def read_variables(file_path):
    variables = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            key = key.strip(' ')
            value = value.strip(' ')
            if value.isdigit():
                value = int(value)
            else:
                value = value.strip("'")
            variables[key] = value
    return variables

# Example usage
file_path = 'input.txt'  # Replace with your actual file path
variables = read_variables(file_path)

# Assign variables
TAG = variables.get('TAG')
KEY_WORDS = variables.get('KEY_WORDS')
START_YEAR = variables.get('START_YEAR')
END_YEAR = variables.get('END_YEAR')
START_PAGE_NUM = variables.get('START_PAGE_NUM')
MAX_NUM = variables.get('MAX_NUM')

def construct_url(kw, st_yr, ed_yr, n):
    kw = kw.replace(' ', '+')
    kw = kw.replace('"', '%22')
    kw = kw.replace("'", '%22')
    st_yr_url = f'&as_ylo={st_yr}'
    ed_yr_url = f'&as_yhi={ed_yr}'
    url = f'https://scholar.google.com/scholar?start={n}&q={kw}&hl=en&as_sdt=0,5{st_yr_url}{ed_yr_url}'
    return url

def get_author(content):
    for char in range(0, len(content)):
        if content[char] == '-':
            out = content[2:char-1]
            break
    return out

def get_citations(content):
    out = 0
    for char in range(0, len(content)):
        if content[char:char+9] == 'Cited by ':
            init = char+9
            for end in range(init+1, init+6):
                if content[end] == '<':
                    break
            out = content[init:end]
    return int(out)

def get_year(content):
    for char in range(0, len(content)):
        if content[char] == '-':
            out = content[char-5:char-1]
    if not out.isdigit():
        out = 0
    return int(out)

def save_website_content(driver, url):
    # Variables
    data = []
    links = []
    title = []
    citations = []
    year = []
    author = []
    venue = []
    publisher = []
    rank = [0]

    try:
        driver.get(url)
        WebDriverWait(driver, 3600).until(EC.presence_of_element_located((By.CLASS_NAME, "gs_or")))

        # Create parser
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Get stuff
        mydivs = soup.findAll("div", {"class": "gs_or"})

        for div in mydivs:
            try:
                links.append(div.find('h3').find('a').get('href'))
            except:  # catch *all* exceptions
                links.append('Look manually at: ' + url)

            try:
                title.append(div.find('h3').find('a').text)
            except:
                title.append('Could not catch title')

            try:
                citations.append(get_citations(str(div.format_string)))
            except:
                warnings.warn("Number of citations not found for {}. Appending 0".format(title[-1]))
                citations.append(0)

            try:
                year.append(get_year(div.find('div', {'class': 'gs_a'}).text))
            except:
                warnings.warn("Year not found for {}, appending 0".format(title[-1]))
                year.append(0)

            try:
                author.append(get_author(div.find('div', {'class': 'gs_a'}).text))
            except:
                author.append("Author not found")

            try:
                publisher.append(div.find('div', {'class': 'gs_a'}).text.split("-")[-1])
            except:
                publisher.append("Publisher not found")

            try:
                venue.append(" ".join(div.find('div', {'class': 'gs_a'}).text.split("-")[-2].split(",")[:-1]))
            except:
                venue.append("Venue not found")

            rank.append(rank[-1] + 1)
        data = pd.DataFrame(list(zip(author, title, citations, year, publisher, venue, links)), index=rank[1:],
                            columns=['Author', 'Title', 'Citations', 'Year', 'Publisher', 'Venue', 'Source'])
        data.index.name = 'Rank'
    except Exception as e:
        print(f"An error occurred: {e}")
    return data

# Setup ChromeDriver
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
service = Service()  # Replace with the path to your ChromeDriver

driver = webdriver.Chrome(service=service, options=chrome_options)

# Example usage
empt = 0
for n in range(int(START_PAGE_NUM) * 10, MAX_NUM, 10):
    url = construct_url(KEY_WORDS, START_YEAR, END_YEAR, n)
    data = save_website_content(driver, url)
    if n == 0:
        df = data
    else:
        if isinstance(data, pd.DataFrame):    
            df = pd.concat((df, data), ignore_index=True)
    df.to_csv(f'{TAG}_{START_YEAR}_{END_YEAR}_{START_PAGE_NUM}_{MAX_NUM}.csv', index=False)
    if len(data) == 0:
        empt += 1
    print(f'iteration: {n}')
    if empt == 1:
        print('Empty page found. All links grabbed (Most Likely!). Exiting!')
        break
    time.sleep(2 + random() * 10)
driver.quit()
