#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 21:09:22 2024

@author: sasankatalukdar
"""

import requests
from random import random
from bs4 import BeautifulSoup
import time
import warnings
import pandas as pd
# from fp.fp import FreeProxy

def read_variables(file_path):
    variables = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            key=key.strip(' ')
            value=value.strip(' ')
            if value.isdigit():
                value = int(value)
            else:
                value=value.strip("'")
            variables[key] = value
    return variables

# Example usage
file_path = 'input.txt'  # Replace with your actual file path
variables = read_variables(file_path)

# Assign variables
TAG=variables.get('TAG')
KEY_WORDS = variables.get('KEY_WORDS')
START_YEAR = variables.get('START_YEAR')
END_YEAR = variables.get('END_YEAR')
START_PAGE_NUM = variables.get('START_PAGE_NUM')
MAX_NUM = variables.get('MAX_NUM')

ROBOT_KW=['unusual traffic from your computer network', 'not a robot']

def contruct_url(kw,st_yr,ed_yr,n):
    kw=kw.replace(' ','+')
    kw=kw.replace('"','%22')
    kw=kw.replace("'",'%22')
    st_yr_url = f'&as_ylo={st_yr}'
    ed_yr_url = f'&as_yhi={ed_yr}'
    url = f'https://scholar.google.com/scholar?start={n}&q={kw}&hl=en&as_sdt=0,5{st_yr_url}{ed_yr_url}'
    return url

def get_author(content):
    for char in range(0,len(content)):
        if content[char] == '-':
            out = content[2:char-1]
            break
    return out

def get_citations(content):
    out = 0
    for char in range(0,len(content)):
        if content[char:char+9] == 'Cited by ':
            init = char+9
            for end in range(init+1,init+6):
                if content[end] == '<':
                    break
            out = content[init:end]
    return int(out)

def get_year(content):
    for char in range(0,len(content)):
        if content[char] == '-':
            out = content[char-5:char-1]
    if not out.isdigit():
        out = 0
    return int(out)

def save_website_content(url):
    # Variables
    data=[]
    links = []
    title = []
    citations = []
    year = []
    author = []
    venue = []
    publisher = []
    rank = [0]

    try:
        # proxy = FreeProxy(rand=True, timeout=1, country_id=["US", "CA"]).get()
        session = requests.Session()
        # page = session.get(url, proxies={'http': proxy,
        #                                  'https': proxy})
        page = session.get(url)

        c = page.content
        if any(kw in c.decode('ISO-8859-1') for kw in ROBOT_KW):
            print("Ooh no! Are are caught!")
        
        # Create parser
        soup = BeautifulSoup(c, 'html.parser', from_encoding='utf-8')

        # Get stuff
        mydivs = soup.findAll("div", { "class" : "gs_or" })

        for div in mydivs:
            try:
                links.append(div.find('h3').find('a').get('href'))
            except: # catch *all* exceptions
                links.append('Look manually at: '+url)

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
                year.append(get_year(div.find('div',{'class' : 'gs_a'}).text))
            except:
                warnings.warn("Year not found for {}, appending 0".format(title[-1]))
                year.append(0)

            try:
                author.append(get_author(div.find('div',{'class' : 'gs_a'}).text))
            except:
                author.append("Author not found")

            try:
                publisher.append(div.find('div',{'class' : 'gs_a'}).text.split("-")[-1])
            except:
                publisher.append("Publisher not found")

            try:
                venue.append(" ".join(div.find('div',{'class' : 'gs_a'}).text.split("-")[-2].split(",")[:-1]))
            except:
                venue.append("Venue not fount")
            # try:
            #     data_cid=div['data-cid']
            #     url_cite = "https://scholar.google.com/scholar?q=info:%s:scholar.google.com/&output=cite&scirp=0&hl=fr" % (data_cid)
            #     session = requests.Session()
            #     page = session.get(url_cite)
            #     c = page.content
            #     soup = BeautifulSoup(c, 'html.parser', from_encoding='utf-8')
            #     mydivs = soup.findAll("div")
                
            rank.append(rank[-1]+1)
        # Create a dataset and sort by the number of citations
        data = pd.DataFrame(list(zip(author, title, citations, year, publisher, venue, links)), index = rank[1:],
                            columns=['Author', 'Title', 'Citations', 'Year', 'Publisher', 'Venue', 'Source'])
        data.index.name = 'Rank'
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return data

# Example usage
empt=0
for n in range(int(START_PAGE_NUM/10),MAX_NUM,10):
    url = contruct_url(KEY_WORDS,START_YEAR,END_YEAR,n)
    data=save_website_content(url)
    if n==0:
        df=data
    else:
        df=pd.concat((df,data), ignore_index=True)
    df.to_csv(f'{TAG}_{START_YEAR}_{END_YEAR}_{START_PAGE_NUM}_{MAX_NUM}.csv',index=False)
    if len(data)==0:
        empt+=1
    print(f'iteration: {n}')
    if empt==1:
        print('Empty page found. All links grabbed (Most Likely!). Exiting!')
        break
    time.sleep(60+random()*100)
    if n%200==0 and n!=0:
        print('Ooof! So many papers! Are you sure you are going to read them all? I am exhausted! I am taking a short nap!')
        time.sleep(500+random()*1000)
        print('Okay! I am refreshed from the nap. Downloading again...')
    