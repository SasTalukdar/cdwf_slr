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

df=pd.read_csv('Monsoon_AND_weather_OR_climate_OR_river_OR_cloud_OR_rain_OR_rainfall_OR_precipitation_OR_temperature_OR_wind_OR_premonsoon_Northeast_India_2001_2021.csv')

ris=''
for i, row in df.iterrows():
    if row.Source[:4]=='http':
        url=row.Source
        title=row.Title
        authors=format_author(row.Author)
        journal=row.Venue
        
    sec=f'TY  - JOUR\nTI  - {title}{authors}\nDP  - DOI.org (Crossref)\nLA  - en\nUR  - {url}\nER  -\n\n'
    ris=ris+sec

with open("sample1.ris", "w") as file:
    file.write(ris)