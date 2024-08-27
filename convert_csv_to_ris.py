#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 18:11:44 2024

@author: sasankatalukdar
"""

import pandas as pd

def format_author(x):
    aut_str=''
    authors=x.split(',')
    for author in authors:
        last, _, first=author.rpartition(' ')
        aut_str=aut_str+f'\nAU  - {last}, {first}'
    return aut_str

def find_doi(x):
    doi=''
    if '/doi/' in x:
        doi=x.split('/doi/')[1][4:]
        if '#page=' in doi:
            doi=doi.split('#page=')[0]
    elif 'springer.com' in x:
        doi='10.1007/'+x.split('/')[-1]
    elif 'wiley.com' in x:
        doi='10.1029/'+x.split('/')[-1]
    elif 'nature.com' in x:
        doi='10.1038/'+x.split('/')[-1]
    elif 'copernicus.org' in x:
        if '/'+x.split('.')[0][8:]+'-' in x:
            x=x.split('/'+x.split('.')[0][8:]+'-')[0]
        doi='10.5194/'+x.split('.')[0][8:]+x.split('articles')[-1].replace('/','-')
        if doi[-1]=='-':
            doi=doi[:-1]
    return doi
        
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

df=pd.read_csv(f'{TAG}_{START_YEAR}_{END_YEAR}_{START_PAGE_NUM}_{MAX_NUM}.csv')

ris=''
for i, row in df.iterrows():
    if row.Source[:4]=='http':
        url=row.Source
        title=row.Title
        authors=format_author(row.Author)
        journal=row.Venue
        doi=find_doi(row.Source)
    sec=f'TY  - JOUR\nTI  - {title}{authors}\nDO  - {doi}\nDP  - DOI.org (Crossref)\nLA  - en\nUR  - {url}\nER  -\n\n'
    ris=ris+sec

with open(f'{TAG}_{START_YEAR}_{END_YEAR}_{START_PAGE_NUM}_{MAX_NUM}.ris', "w") as file:
    file.write(ris)
