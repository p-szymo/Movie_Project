import requests as rq
from bs4 import BeautifulSoup as BS
import pandas as pd
import numpy as np
import time
import re

### Turn a table on IMDB into a useable soup list.
### Return all but the first entry because that is just the IMDB table column names.
def table_list_creator(url):
    page = rq.get(url)
    soup = BS(page.content, 'html.parser')
    table = soup.find('table')
    table_list = table.find_all('tr')
    return table_list[1:]

### Create a dictionary for a show from its soup entry.
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

### Make a dataframe from a list of show dictionaries.
def dataframe_creator(show_dict_list):
    columns = show_dict_list[0].keys()
    return pd.DataFrame(show_dict_list, columns=columns)

### Enter IMDB url to an IMDB table and turn it into a dataframe!
def imdb_scrape(url):
    table_list = table_list_creator(url)
    show_dict_list = [show_dict_creator(show) for show in table_list]
    df = dataframe_creator(show_dict_list)
    return df

### Capture television rating for a show, given the correct elements in a soup. Used in imdb_scraper below.
def tv_rating(soup_elements):
    for element in soup_elements:
        try:
            element.find('h4').text
            if element.find('h4').text == 'Certificate:':
                return element.find('span').text
        except AttributeError:
            continue

### Capture release for a show, given the correct elements in a soup. Used in imdb_scraper below.
def release_year(soup_elements):
    for element in soup_elements:
        if 'TV' in element.text:
            return int(re.search('\(([^)]+)', element.text).group(1)[:4])

### Scrape through each IMDB page given a list of IMDB urls.
def imdb_scraper(url_list):
    show_dict_list = []
    for url in url_list:
        page = rq.get(url)
        soup = BS(page.content, 'html.parser')
        show_dict = {}
        show_dict['title'] = soup.find('div', {'class': 'title_wrapper'}).find('h1').text.strip()
        genre_loc = soup.find_all('div', {'class': 'see-more inline canwrap'})[-1]
        show_dict['genres'] = [genre.text.lower().strip() for genre in genre_loc.find_all('a')]
        show_dict['tv_rating'] = tv_rating(soup.find_all('div', {'class': 'txt-block'}))
        try:
            show_dict['release_year'] = release_year(soup.find('div', {'class': 'subtext'}).find_all('a'))
        except AttributeError as A:
            show_dict['release_year'] = np.nan
            print(show_dict['title'])
            print(A)
            pass
        try:
            show_dict['runtime_mins'] = int(soup.find_all('time')[1].text[:2])
        except IndexError as e:
            show_dict['runtime_mins'] = np.nan
            print(show_dict['title'])
            print(e)
            pass
        show_dict_list.append(show_dict)
        print(url)
        time.sleep(.25)
    return show_dict_list

### Function to get rid of unwanted characters, in order to turn into a useable url for Rotten Tomatoes.
def char_replacer(title):
    bad_chars = ["!","@","#","$","%","^","/","&","*",",",".",";",":"]
    for i in bad_chars :
        title = title.replace(i, '')
    return title

### Capture information for a show, given the correct elements in a soup, and the term one is searching for. Used in rt_scraper below.
### NOTE: now only used for network grab, since release_year was not reliably on most RT pages.
def rt_item_get(tv_elements, term):
    for element in tv_elements:
        try:
            element.find('td').text
            if element.find('td').text == term:
                return element.find('td', class_=None).text
        except AttributeError:
            continue

### Capture ratings for each season of a show, given the correct elements in a soup. Used in rt_scraper below.
def season_ratings(seasons):
    season_ratings = []
    for season in seasons[::-1]:
        try:
            season.find('span', {'class': 'meter-value'}).text
            season_ratings.append(int(season.find('span', {'class': 'meter-value'}).text.replace('%','')))
        except AttributeError:
            season_ratings.append(np.nan)
    return season_ratings

### Scrape through each Rotten Tomatoes page given a dictionary of titles and urls.
def rt_scraper(url_dict):
    show_dict_list = []
    for title, url in url_dict.items():
        try:
            page = rq.get(url)
        except:
            print(title)
            continue
        soup = BS(page.content, 'html.parser')
        show_dict = {}
        show_dict['title'] = title
        show_ratings = soup.find_all('span', {'class': 'mop-ratings-wrap__percentage'})
        try:
            show_dict['rt_critic_rating'] = int(show_ratings[0].text.strip().replace('%',''))
        except IndexError as e:
            try:
                show_dict['rt_critic_rating'] = int(show_ratings.text.strip().replace('%',''))
            except AttributeError as A:
                print(title)
                print(A)
                pass
            print(title)
            print(e)
            pass
        try:
            show_dict['rt_audience_rating'] = int(show_ratings[1].text.strip().replace('%',''))
        except IndexError as e:
            show_dict['rt_audience_rating'] = np.nan
            print(title)
            print(e)
            pass
        show_dict['network'] = rt_item_get(soup.find_all('tr'), 'TV Network:')
        seasons = soup.find_all('div', {'class': 'bottom_divider media seasonItem'})
        show_dict['season_ratings'] = season_ratings(seasons)
        show_dict_list.append(show_dict)
        print(url)
        time.sleep(.5)
    return show_dict_list