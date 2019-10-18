"""
recipe_markov.py: Jack Beckitt-Marshall, Kevin Li, Yvonne Fang, PQ3, CSCI3725.
18 October 2019

Allows us to create and use a Markov chain to establish the "probability" of
recipes.
"""

import os
import json
import itertools

import inflect

# Opens both the translation and substitution data.
with open('translation_dict2.json', 'r') as json_file:
    TRANS_DATA = json.load(json_file)
with open('sub_dict2.json', 'r') as json_file:
    SUB_DATA = json.load(json_file)


with open("recipe_markov.json", "r") as markov_file:
    MARKOV_DATA = json.load(markov_file)

def substitutions(ingredient=None):
    """
    This method takes an ingredient and gets subs for it from our
    knowledge base.

    Arguments:
        ingredient: Ingredient to substitute.
    """
    # We only want to substitute 25% of the time. Hence, we will randomly
    # generate a number from 1 to 4, and make a sub when we get a 1.
    if SUB_DATA.get(TRANS_DATA.get(str(ingredient))):
        return SUB_DATA[TRANS_DATA[str(ingredient)]]["subs"]
    return []

def get_ingredient_string(ingredient):
    """
    This function essentially manipulates the string of the ingredient,
    essentially seeing if we can find one that is within our knowledge
    base so we can get categories and substitutions

    Arguments:
        ingredient - an Ingredient instance where we want to find the
            corresponding string.
    """


    i_engine = inflect.engine()
    string = str(ingredient).lower()
    if i_engine.singular_noun(string):
        string = str(i_engine.singular_noun(string)).split(" ")
    else:
        string = string.split(" ")
    for i in range(len(string), -1, -1):
        for combo in itertools.combinations(string, i):
            if MARKOV_DATA.get(" ".join(combo)):
                return " ".join(combo)
    return ingredient

def get_probability(search_terms):
    """
    Given a list of search terms (such as ingredients, get the probability
    of the recipe by comparing pairs of ingredients (in alphabetical order) and
    seeing how they correspond to one another.

    Arguments:
        search_terms: Recipe search terms to use.
    """
    result = 1.0

    search_terms = sorted(search_terms)

    search_pairs = zip(search_terms, search_terms[1:])

    result = 1.0

    for ing1, ing2 in search_pairs:
        probabilities = []
        ing1_subs = substitutions(ing1) + [ing1]
        ing2_subs = substitutions(ing2) + [ing2]
        for i_1, i_2 in itertools.product(ing1_subs, ing2_subs):
            ing1_string = get_ingredient_string(i_1)
            ing2_string = get_ingredient_string(i_2)
            if not ing1_string or not ing2_string:
                probabilities.append(0.01)
            else:
                probabilities.append(MARKOV_DATA.get(ing1_string, dict()).get(ing2_string, 0.01))
                probabilities.append(MARKOV_DATA.get(ing2_string, dict()).get(ing1_string, 0.01))

        result *= max(probabilities)
    return result

def create_markov_chain(folder):
    """
    Creates a Markov chain based on a bunch of recipe JSON files downloaded
    using meanrecipe (https://github.com/schollz/meanrecipe).

    Arguments:
        folder: The folder where the recipes are stored.
    """
    with open(os.path.join(folder, "recipes.json"), "r") as recipe_data:
        recipes = json.load(recipe_data)

    print("Using {0} recipes for learning".format(len(recipes)))
    all_ingredients_map = dict()

    for recipe in recipes:
        for ing in recipe.get("ingredients", []):
            all_ingredients_map[ing["ingredient"]] = 0

    all_ingredients = []
    i = 0
    for ing in all_ingredients_map:
        all_ingredients.append(map)
        all_ingredients_map[ing] = i
        i += 1

    print("Got {0} ingredients".format(len(all_ingredients)))

    recipe_num = dict()

    for _, recipe in enumerate(recipes):
        if len(recipe.get("ingredients", [])) < 3:
            continue

        recipe_ingredients = []
        for ing in recipe.get("ingredients", []):

            recipe_ingredients.append(ing["ingredient"])


        recipe_ingredients = sorted(recipe_ingredients)
        for ing1, ing2 in zip(recipe_ingredients, recipe_ingredients[1:]):
            if ing1 in TRANS_DATA:
                ing1 = TRANS_DATA[ing1]
            if ing2 in TRANS_DATA:
                ing2 = TRANS_DATA[ing2]
            if ing1 not in recipe_num:
                recipe_num[ing1] = {ing2: 1}
            else:
                if ing2 not in recipe_num[ing1]:
                    recipe_num[ing1][ing2] = 1
                else:
                    recipe_num[ing1][ing2] += 1


    for _, dict_val in recipe_num.items():
        for follower, _ in dict_val.items():
            dict_val[follower] /= sum(dict_val.values())

    with open("recipe_markov.json", "w") as file:
        json.dump(recipe_num, file)
