"""
thesaurus.py - Jack Beckitt-Marshall, Kevin Li, Yvonne Fang, PQ3, CSCI 3725
18 October 2019

Scraper for foodsubs.com
"""

import re
import os
import urllib.parse
import collections
import json
import argparse

from bs4 import BeautifulSoup
import requests # To be able to fetch webpages off the internet.


def scrape_urls(start_url):
    """
    This function scrapes URLs, given a start URL, which is useful for when
    we're trying to get all possible ingredient substitutions!

    Arguments:
        start_url: The URL from which we start the scraping process.
    """
    # Create a queue of new URLs to start crawling.
    new_urls = collections.deque([start_url])
    # Set of URLs we've already processed.
    used_urls = set()

    # Keep track of URLs that are local
    local_urls = set()

    while new_urls:
        url = new_urls.popleft()
        used_urls.add(url)
        print("Processing {0}".format(url))

        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
            continue

        # Extract base URL so we can differentiate the parts.
        # extract base url to resolve relative links
        parts = urllib.parse.urlsplit(url)
        base = "{0.netloc}".format(parts)
        strip_base = base.replace("www.", "")
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url


        soup = BeautifulSoup(response.text, "html5lib")

        for link in soup.find_all('a'):
            anchor = link.attrs['href'] if 'href' in link.attrs else ''
            if anchor.startswith('/'):
                local_link = urllib.parse.urljoin(base_url, anchor)
                local_urls.add(local_link)
            elif anchor.startswith("#"):
                pass
            elif strip_base in anchor:
                local_urls.add(anchor)
            elif not anchor.startswith('http'):
                local_link = urllib.parse.urljoin(path, anchor)
                local_urls.add(local_link)


        for i in local_urls:
            if not i in new_urls and not i in used_urls:
                new_urls.append(i)
                print(i + " Appended")
                print(used_urls)

    return list(local_urls)


def get_list_and_subs(content):
    """
    From content, this function will give us a pair of lists: a list of
    equivalent ingredients and a list of substitutes.

    Arguments:
        content: The HTML content we want to retrieve the two components from.
    """
    final_list = []
    for _, item in enumerate(content):
        if "Substitutes:" in item.get_text() and item.find_all('b'):
            ingredient_names = item.find_all('b')[0].find(text=True) \
                .replace('\n', ' ').replace('\r', '')
            ingredient_names = ingredient_names.split("=")
            for i, name in enumerate(ingredient_names):
                ingredient_names[i] = name.rstrip().lstrip()
                # Remove extraneous spaces from the ingredient names.
                ingredient_names[i] = re.sub(' +', ' ', ingredient_names[i])

            substitutes = item.get_text().split("Substitutes:")[1]\
                .replace('\n', ' ').replace('\r', '')
            substitutes = substitutes.split("Links")[0]
            substitutes = substitutes.split("Cooking notes")[0]
            substitutes = substitutes.split("Notes")[0]
            substitutes = substitutes.split("OR")

            for i, sub in enumerate(substitutes):
                substitutes[i] = sub.rstrip().lstrip()
                # Remove extraneous spaces and bracketed comments.
                substitutes[i] = re.sub(r' +', ' ', substitutes[i])
                substitutes[i] = re.sub(r'\(.*\)', '', substitutes[i]).rstrip()

            final_list.append((ingredient_names, substitutes))

    return final_list

def main():
    """
    Main function: starts the URL scraping process.
    """
    parser = argparse.ArgumentParser(
        description="Scrape ingredient categories and substitions from Cook's Thesarus")
    parser.add_argument("--urls", default=None, help="Locations of URL JSON file")

    args = parser.parse_args()

    if args.urls is None:
        urls = scrape_urls('http://foodsubs.com')
        with open("urllist.json", 'w') as file:
            json.dump(urls, file)
    else:
        with open(args.urls, "r") as file:
            urls = json.load(file)

    translation_dicts = []
    sub_dicts = []

    for url in urls:
        print("Processing {0}.".format(os.path.basename(url).split(".")[0]))
        try:
            response = requests.get(url)
        except requests.exceptions.InvalidSchema:
            pass

        soup = BeautifulSoup(response.content, "lxml")

        all_tds = soup.find_all('td')

        all_ps = [elem for elem in list(soup.find_all('p'))\
                    if elem.parent.name != "td"]

        list_part = get_list_and_subs(all_tds) + get_list_and_subs(all_ps)

        translation_dict = dict()
        sub_dict = dict()

        for ingredient_names, subs in list_part:
            initial_name = ingredient_names[0]
            for name in ingredient_names:
                translation_dict[name] = initial_name

            sub_dict[initial_name] = {"subs": subs,
                                      "category": os.path.basename(url)\
                                      .split(".")[0]}

        translation_dicts.append(translation_dict)
        sub_dicts.append(sub_dict)

    translation_dict = {k: v for d in translation_dicts for k, v in d.items()}
    sub_dict = {k: v for d in sub_dicts for k, v in d.items()}

    with open("translation_dict.json", "w") as file:
        json.dump(translation_dict, file)
    with open("sub_dict.json", "w") as file:
        json.dump(sub_dict, file)

if __name__ == "__main__":
    main()
