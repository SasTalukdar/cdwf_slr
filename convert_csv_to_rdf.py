#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 20:48:25 2024

@author: sasankatalukdar
"""


import datetime
import pandas as pd

def format_author(x):
    aut_str='''<bib:authors>\n            <rdf:Seq>'''
    authors=x.split(',')
    for author in authors:
        last, _, first=author.rpartition(' ')
        temp_str=f'''
                    <rdf:li>
                       <foaf:Person>
                           <foaf:surname>{first}</foaf:surname>
                           <foaf:givenName>{last}</foaf:givenName>
                       </foaf:Person>
                    </rdf:li>'''
        aut_str=aut_str+temp_str
    aut_str=aut_str+'\n            </rdf:Seq>\n        </bib:authors>'
    return aut_str

url=''
issn=''
title=''
authors=''
title=''
date=''
page=''
lib_cat='DOI.org (Crossref)'
vol=''
journal=''
doi=''

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

rdf='''
<rdf:RDF
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns:z="http://www.zotero.org/namespaces/export#"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:bib="http://purl.org/net/biblio#"
 xmlns:foaf="http://xmlns.com/foaf/0.1/"
 xmlns:link="http://purl.org/rss/1.0/modules/link/"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:prism="http://prismstandard.org/namespaces/1.2/basic/">
'''

for i, row in df.iterrows():
    if row.Source[:4]=='http' and i not in [74,103,107,131,179,181,308,336,379]:
        url=row.Source
        title=row.Title
        authors=format_author(row.Author)
        journal=row.Venue
        sec=f'''
        <bib:Article rdf:about="{url}">
            <z:itemType>journalArticle</z:itemType>
            <dcterms:isPartOf rdf:resource="{issn}"/>
            {authors}
            <dc:title>{title}</dc:title>
            <dcterms:abstract></dcterms:abstract>
            <dc:date>{date}</dc:date>
            <z:language>en</z:language>
            <z:libraryCatalog>{lib_cat}</z:libraryCatalog>
            <dc:identifier>
                <dcterms:URI>
                    <rdf:value>{url}</rdf:value>
                </dcterms:URI>
            </dc:identifier>
            <dcterms:dateSubmitted>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</dcterms:dateSubmitted>
            <bib:pages>{page}</bib:pages>
        </bib:Article>'''
        rdf=rdf+sec
    else:
        print(row)
rdf=rdf+'\n</rdf:RDF>'
with open(f'{TAG}_{START_YEAR}_{END_YEAR}_{START_PAGE_NUM}_{MAX_NUM}.rdf', "w") as file:
    file.write(rdf)
