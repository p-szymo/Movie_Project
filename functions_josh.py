import requests as rq
from bs4 import BeautifulSoup as BS
import pandas as pd
import numpy as np

def table_list_creator(url):
    page = rq.get(url)
    soup = BS(page.content, 'html.parser')
    table = soup.find('table')
    table_list = table.find_all('tr')
    return table_list[1:]

def show_dict_creator(show):
    base_url = 'https://www.imdb.com'
    show_dict = {}
    show_dict['title'] = show.find('a').find('img')['alt']
    for item in show.find_all('span',attrs={'class': None}):
        try:
            if item['name'] == 'ir':
                show_dict['imdb_rating'] = item['data-value']
            if item['name'] == 'nv':
                show_dict['num_imdb_ratings'] = item['data-value']
        except KeyError:
            continue
    show_dict['url'] = base_url + show.find('a')['href']
    return show_dict

def dataframe_creator(show_dict):
    columns = show_dict[0].keys()
    return pd.DataFrame(show_dict, columns=columns)

def imdb_scrape(url):
    table_list = table_list_creator(url)
    show_dict = [show_dict_creator(show) for show in table_list]
    columns = show_dict[0].keys()
    df = pd.DataFrame(show_dict, columns=columns)
    return df