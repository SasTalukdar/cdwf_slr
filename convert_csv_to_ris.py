#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 18:11:44 2024

@author: sasankatalukdar
"""

import datetime
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

df=pd.read_csv('Monsoon_AND_weather_OR_climate_OR_river_OR_cloud_OR_rain_OR_rainfall_OR_precipitation_OR_temperature_OR_wind_OR_premonsoon_Northeast_India_2001_2021.csv')

ris=''
for i, row in df.iterrows():
    if row.Source[:4]=='http':
        url=row.Source
        title=row.Title
        authors=format_author(row.Author)
        journal=row.Venue
        doi=find_doi(row.Source)
    if doi!='':
        sec=f'TY  - JOUR\nTI  - {title}{authors}\nDO  - {doi}\nDP  - DOI.org (Crossref)\nLA  - en\nUR  - {url}\nER  -\n\n'
    ris=ris+sec
    if i==20:
        break

with open("sample1.ris", "w") as file:
    file.write(ris)