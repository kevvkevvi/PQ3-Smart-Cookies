"""
parserecipe.py - Recipe parser that collects an inspiring set from the internet.

Jack Beckitt-Marshall, Kevin Li and Yvonne Fang - CSCI 3725 - PQ1
16 October 2019
"""

# importing libraries
import re
import json
import urllib.request
from fractions import Fraction
from bs4 import BeautifulSoup
from tqdm import tqdm
# -*- coding: utf-8 -*-

# Dictionary mapping vulgar fraction to floats for parsing ingredient amounts.
FRACTIONS = {
    0x2189: 0.0,  # ; ; 0 # No       VULGAR FRACTION ZERO THIRDS
    0x2152: 0.1,  # ; ; 1/10 # No       VULGAR FRACTION ONE TENTH
    0x2151: 0.11111111,  # ; ; 1/9 # No       VULGAR FRACTION ONE NINTH
    0x215B: 0.125,  # ; ; 1/8 # No       VULGAR FRACTION ONE EIGHTH
    0x2150: 0.14285714,  # ; ; 1/7 # No       VULGAR FRACTION ONE SEVENTH
    0x2159: 0.16666667,  # ; ; 1/6 # No       VULGAR FRACTION ONE SIXTH
    0x2155: 0.2,  # ; ; 1/5 # No       VULGAR FRACTION ONE FIFTH
    0x00BC: 0.25,  # ; ; 1/4 # No       VULGAR FRACTION ONE QUARTER
    0x2153: 0.33333333,  # ; ; 1/3 # No       VULGAR FRACTION ONE THIRD
    0x215C: 0.375,  # ; ; 3/8 # No       VULGAR FRACTION THREE EIGHTHS
    0x2156: 0.4,  # ; ; 2/5 # No       VULGAR FRACTION TWO FIFTHS
    0x00BD: 0.5,  # ; ; 1/2 # No       VULGAR FRACTION ONE HALF
    0x2157: 0.6,  # ; ; 3/5 # No       VULGAR FRACTION THREE FIFTHS
    0x215D: 0.625,  # ; ; 5/8 # No       VULGAR FRACTION FIVE EIGHTHS
    0x2154: 0.66666667,  # ; ; 2/3 # No       VULGAR FRACTION TWO THIRDS
    0x00BE: 0.75,  # ; ; 3/4 # No       VULGAR FRACTION THREE QUARTERS
    0x2158: 0.8,  # ; ; 4/5 # No       VULGAR FRACTION FOUR FIFTHS
    0x215A: 0.83333333,  # ; ; 5/6 # No       VULGAR FRACTION FIVE SIXTHS
    0x215E: 0.875,  # ; ; 7/8 # No       VULGAR FRACTION SEVEN EIGHTHS
}

# Read the urls containing recipes stored in a text file
URL_LIST = []
for url in open("urls.txt").readlines():
    URL_LIST.append(url.rstrip())

# List to contain all the inspiring sets.
INSPIRING_SET = []

def convert(amount):
    """
    Converts units in the parsed recipes into oz.
    """
    # Get the unit of ingredient amount.
    try:
        unit = re.findall(r'\w+s?\Z', amount)[0]
    except IndexError:
        # Extracts the count of ingredients without a unit
        amount = re.match(r'[\d]*', amount).group()
        return float(amount)

    # Parse the numerical amount.
    if "and" in amount:
        nums = re.search(r'(\d?/?\d)\sand\s((\d/\d))', amount)
        result = float(nums.group(1)) + float(Fraction(nums.group(2)))
    elif "." in amount:
        result = float(re.search(r'([.\d]+)\s', amount).group(1))
    else:
        result = float(Fraction(re.search(r'(\d?/?\d)\s', amount).group(1)))

    # If unit is cup
    if unit in ("cup", "cups"):
        result = result * 8
    # If unit is teaspoon
    elif unit in ("teaspoon", "teaspoons", "tsp"):
        result = result * 0.17
    # If unit is tablespoon
    elif unit in ("Tablespoon", "Tablespoons", "tbsp"):
        result = result * 0.5
    # Returns result in oz
    return result

# Use BeautifulSoup to parse recipe from websites in the URL_LIST.
for url in tqdm(URL_LIST):
    recipe = []
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        page = urllib.request.urlopen(req) # conntect to website
    except SyntaxError:
        print("There's an error!")

    soup = BeautifulSoup(page, 'html.parser')

    # Find the div that contains the recipe
    recipe_div = soup.find('div', attrs={'class': 'tasty-recipes-ingredients'})
    if recipe_div is None:
        recipe_div = soup.find('div', attrs={'class': 'recipe-ingredients-wrapper'})

    ingredient_list = [] # List of ingredients and amounts
    ingredient = '' # Ingredient string
    ing_amount = '' # Ingredient amount

    # Extracts the text from all the li items within the div
    for li in recipe_div.find_all('li'):
        try:
            clean_li = li.text.replace('Ingredients', '') # Remove heading
            clean_li = clean_li.replace('\xa0', ' ') # Remove meaningless string
            ingredient_list.append(clean_li)
        except:
            pass

    for item in ingredient_list:
        # When item in the unit of "oz"
        if 'oz' in item:
            ingredient = re.search(r'oz\s([\w\s\-\’/]+)', item).group(1)
            rx = r'(\d*)(%s)' % '|'.join(map(chr, FRACTIONS))
            ing_amount = re.search(r'([\d]+)oz', item)
            if ing_amount is None:
                for d, f in re.findall(rx, item):
                    d = float(d) if d else 0
                    ing_amount = d + FRACTIONS[ord(f)]
            else:
                ing_amount = float(ing_amount.group(1))

        #When there is "()" in item
        elif ')' in item:
            try:
                ingredient = re.search(r'\)\s([\w\s\-\’/]+)', item).group(1)
                # Note: This cannot extract extra units like "Tablespoons"
                ing_amount = re.match(r'\d?/?\d\s(?!and\s)\w+|\d\sand\s\d/\d\s\w+'
                                      r'|\d?/?\d\s\w+\s\+\s\d\s\w+', item).group()
                ing_amount = convert(ing_amount)
            except AttributeError:
                pass

        # This part parses ingredients with no units, or ingredients with misc
        # units; plus optional ingredients
        else:
            try:
                unit_list = ['cup', 'cups', 'tsp', 'teaspoon', 'tbsp', 'Tablespoon', 'Tablespoons']
                if any(u in item for u in unit_list):
                    r = r'(tsp|tbsp|teaspoon|cups?|Tablespoons?)\s([\w\s\-\’\/]+)'
                    ingredient = re.search(r, item).group(2)
                else:
                    r = r'\d+\s(?!tsp|tbsp|teaspoon|cups?|Tablespoons?)([\w\s\-\’\/]+)'
                    ingredient = re.search(r, item).group(1)
                # Ignoring small units like the tablespoon part in "2 cups + 1 tablespoon"
                ing_amount = re.match(r'\d?/?\d\s(?!and\s)(tsp|tbsp|teaspoon|cups?|Tablespoons?)?'
                                      r'|\d\sand\s\d/\d\s(tsp|tbsp|teaspoon|cups?|Tablespoons?)'
                                      r'|\d?/?\d\s\w+\s\+\s\d\s(tsp|tbsp|teaspoon'
                                      r'|cups?|Tablespoons?)', item).group()
                ing_amount = convert(ing_amount)
            # If there is vulgar fraction in ingredient amount
            except AttributeError:
                try:
                    # Matches 1/2 in vulgar fraction
                    ing_unit = re.search(r'\u00BD\s(\w+)', item).group(1)
                    ing_amount = convert("1/2 " + ing_unit)
                # For optional ingredients
                except AttributeError:
                    ingredient = item
                    ing_amount = -1.0
        recipe.append((ingredient, ing_amount))
    INSPIRING_SET.append(recipe)
    
with open("inspiring_set.json", "w") as f:
    json.dump(INSPIRING_SET, f)
