"""
cookie_generation.py - Jack Beckitt-Marshall, Kevin Li, and Yvonne Fang
CSCI 3725, PQ3

Generates cookie recipes from an inspiring set and knowledge base!
"""

import random
import argparse
import os
import shutil
import json
import math
import itertools
import statistics

import inflect
import numpy as np
from joblib import Parallel, delayed
from tqdm import tqdm


import recipe_markov
import food2vec

# Opens both the translation and substitution data.
with open('translation_dict2.json', 'r') as json_file:
    TRANS_DATA = json.load(json_file)
with open('sub_dict2.json', 'r') as json_file:
    SUB_DATA = json.load(json_file)

UT = food2vec.Word2VecUtils()

# Microsoft Azure subscription key for
SUBSCRIPTION_KEY = "f4451d41dab44995b84a8475ba8ec1b5"
WORD_EMBED_VALS = np.load('ingred_word_emb.npy', allow_pickle=True).item()
INGRED_CATEGORIES = np.load('ingred_categories.npy', allow_pickle=True).item()
INGREDIENT_LIST = sorted(WORD_EMBED_VALS.keys())



def similarity(ing_1, ing_2):
    """Returns the similarity between two ingredients based on our data."""
    embed_ing_1 = WORD_EMBED_VALS[ing_1]
    embed_ing_2 = WORD_EMBED_VALS[ing_2]
    return np.dot(embed_ing_1, embed_ing_2)

class Category:
    """
    Defines a category.
    """
    def __init__(self, category_name):
        self.category_name = category_name

    def __str__(self):
        return str(self.category_name)

    def __repr__(self):
        return "Category({0})".format(self.category_name)

class Ingredient:
    """
    Defines an ingredient.
    """
    def __init__(self, ingredient_name):
        self.ingredient_name = ingredient_name

    def __str__(self):
        return str(self.ingredient_name)

    def __repr__(self):
        return "Ingredient({0})".format(self.ingredient_name)



class Amount:
    """
    Defines an amount of an ingredient.
    """
    def __init__(self, amount):
        self.amount = float(amount)

    def get_num(self):
        """
        Gets amount as integer/float.
        """
        return self.amount

    def __str__(self):
        return str(self.amount) + " oz"

    def __repr__(self):
        return "Amount({0})".format(self.amount)

    def __add__(self, amount):
        return Amount(self.get_num() + amount.get_num())

    def __sub__(self, amount):
        return Amount(self.get_num() - amount.get_num())

    def __mul__(self, amount):
        return Amount(self.get_num() * amount.get_num())

    def __truediv__(self, amount):
        return Amount(self.get_num() / amount.get_num())

class Recipe:
    """
    Recipe class: defines a recipe for our purposes.
    """
    def __init__(self, recipe_dict=None):
        if not recipe_dict:
            self.recipe_dict = dict()
        else:
            self.recipe_dict = recipe_dict

    def add_ingredient(self, category, ingredient, amount):
        """
        Adds ingredient to the recipe, checking for existing ingredients and
        adding amounts if necessary.

        Arguments:
            category: Category of ingredient to add.
            ingredient: Ingredient to add
            amount: Amount to add.
        """
        ing = [ingredient, amount]
        if category not in self.recipe_dict:
            self.recipe_dict[category] = []
        for key, _ in self.recipe_dict.items():
            if str(key) == str(category):
                for i, existing_ingredient in enumerate(self.recipe_dict[key]):
                    if str(existing_ingredient[0]) == str(ingredient):
                        self.recipe_dict[key][i] = [ingredient,
                                                    existing_ingredient[1]]
                        return
                self.recipe_dict[key].append(ing)

    def remove_ingredient(self, category, ingredient):
        """
        Remove ingredient based on category and ingredient.

        Arguments:
            Category: category containing ingredient to be removed.
            ingredient: Ingredient to remove
        """
        for key, value in self.recipe_dict.items():
            if str(key) == str(category):
                for i in len(value):
                    if self.recipe_dict[key][i][0] == ingredient:
                        del self.recipe_dict[key][i]
                        break

    def change_ingredient_name(self, category, old_name, new_name):
        """
        Changes ingredient name based on category and and old name and new name.

        Arguments:
            category: Category of ingredient to change.
            old_name: Old name of ingredient.
            new_name: New name of ingredient.
        """
        for key, value in self.recipe_dict.items():
            if str(key) == str(category):
                for i in len(value):
                    if self.recipe_dict[key][i][0] == old_name:
                        self.recipe_dict[key][i][0] = new_name
                    else:
                        print("Error: old ingredient not found in the recipe")
            else:
                print("Error: category not found in the recipe.")


    def get_category(self):
        """
        Gets list of recipe categories.
        """
        return list(self.recipe_dict.keys())

    def get_category_tuples(self):
        """
        Gets the tuples containing ingredients from each category.
        """
        return list(itertools.chain.from_iterable(self.recipe_dict.values()))

    def get_ingredient_amount(self, category, ingredient):
        """
        For an ingredient in a category, get its amount.

        Arguments:
            category: Category of the wanted ingredient.
            ingredient: The ingredient we want to find.
        """
        for key, value in self.recipe_dict.items():
            if str(key) == str(category):
                for i in len(value):
                    if self.recipe_dict[key][i][0] == ingredient:
                        return self.recipe_dict[key][i][1]

                    print("Error: ingredient not found in the recipe")
                    return None
            else:
                print("Error: category not found in the recipe.")
                return None

    def food2vec_score(self):
        """
        This function essentially takes a recipe and performs a Bing search on
        all of the ingredients, and we want to get the count of the number of
        results we get - higher number of results probably means that the recipe
        uses a known good combination of ingredients.

        Arguments:
            recipe: The recipe to be evaluated.
        """
        query = []
        for ingredient, _ in itertools.chain.from_iterable(self.recipe_dict.values()):
            query.append(str(ingredient))

        return UT.food2vec_score(query)

    def result_score(self):
        """
        This function essentially takes a recipe and performs a Bing search on
        all of the ingredients, and we want to get the count of the number of
        results we get - higher number of results probably means that the recipe
        uses a known good combination of ingredients.

        Arguments:
            recipe: The recipe to be evaluated.
        """
        query = []
        for ingredient, _ in itertools.chain.from_iterable(self.recipe_dict.values()):
            query.append(str(ingredient))
        return recipe_markov.get_probability(query)

    def pair_score(self):
        """
        This function takes a recipe and then checks all combinations of
        ingredient pairs to see whether the flavours compliment each other,
        by using Prof Harmon's model. It will return the mean similarity score
        of all possible ingredient pairs.
        """
        ingredients_in_model = []
        for ingredient, _ in itertools.chain.from_iterable(self.recipe_dict.values()):
            if str(ingredient) in INGREDIENT_LIST:
                ingredients_in_model.append(ingredient)
            elif "flour" in str(ingredient):
                ingredients_in_model.append("wheat")
            else:
                for ingredient_part in str(ingredient).split(" "):
                    if ingredient_part in INGREDIENT_LIST:
                        ingredients_in_model.append(Ingredient(ingredient_part))

        pairings = list(itertools.combinations(ingredients_in_model, 2))
        similarities = []

        for ingredient_1, ingredient_2 in pairings:
            similarities.append(float(similarity(str(ingredient_1), str(ingredient_2))))

        if similarities:
            return statistics.mean(similarities)

        return 0.25 # If we can't find similarities.

    def fitness_level(self):
        """
        This fitness function does two things. It first checks all of the
        ingredients to see whether there are any prohibited ingredients (kiwi,
        alcohol or nuts), and will return a score of -inf if that's the case.
        Else it will use a two-pronged strategy of multiplying the amount of
        Bing results we get for the recipe by the similarity score.
        """
        i_engine = inflect.engine()
        banned_categories = ["nuts", "seeds", "liquor", "liqueurs", "brandy",
                             "wines", "aperitif", "beer", "bitters", "fflakfat"]
        for ingredient, _ in itertools.chain.from_iterable(self.recipe_dict.values()):
            translation = TRANS_DATA.get(str(ingredient))
            if not translation:
                # Some ingredients are plural, but plural forms may not appear
                # in translation dictionary, hence we would convert to a singular
                # and see whether it's in there or not.
                translation = TRANS_DATA.get(i_engine.singular_noun(
                    str(ingredient)))
            if translation:
                if translation == "kiwi fruit":
                    return float("inf"), -float("inf"), -float("inf")

                if SUB_DATA[translation]["category"] in banned_categories:
                    return float("inf"), -float("inf"), -float("inf")

        return self.result_score(), self.pair_score(), self.food2vec_score()

    @staticmethod
    def get_ingredient_string(ingredient=None):
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
                if SUB_DATA.get(" ".join(combo)):
                    return " ".join(combo)
        return None

    @staticmethod
    def substitution(ingredient=None):
        """
        This method takes an ingredient and finds a substition for it from our
        knowledge base.

        Arguments:
            ingredient: Ingredient to substitute.
        """
        # We only want to substitute 25% of the time. Hence, we will randomly
        # generate a number from 1 to 4, and make a sub when we get a 1.
        rand = random.randint(1, 4)
        if rand == 1:
            if SUB_DATA.get(TRANS_DATA.get(str(ingredient))):
                num_subs = len(SUB_DATA[TRANS_DATA[str(ingredient)]]["subs"])
                if num_subs == 0:
                    return ingredient
                random_sub = random.randint(0, num_subs - 1)
                sub = SUB_DATA[TRANS_DATA[str(ingredient)]]["subs"][random_sub]
                return Ingredient(sub)

            return ingredient
        return ingredient


    def mystery_ingredient(self):
        """
        This method makes it possible for the recipe to add in a mysterious
        ingredient.
        """
        teehee_specialtreats = ["tapioca", "egg pudding", "red bean", "crushed oreos"]
        add = random.randint(1, 10)
        if add == 1:
            treat = random.randint(0, 4)
            if treat > 3:
                # Get an ingredient using the food2vec model.
                query = []
                for ingredient, _ in itertools.chain.from_iterable(self.recipe_dict.values()):
                    query.append(str(ingredient))

                ingredient, _ = UT.get_new_ingredient(query)
            else:
                ingredient = teehee_specialtreats[treat]
            self.add_ingredient("misc", ingredient.lower(), Amount(5))




    def new_recipe_combo(self, other_recipe):
        """
        Creates a combination of two recipes (self and another recipe),
        iterating through the category lists, and adding ingredients from each
        category and substituting them. Returns a new recipe which is a combo
        of the two.

        Arguments:
            other_recipe: Recipe to combine this one with.
        """
        #create new recipe
        recipe_combo = Recipe()
        category_list = []
        # If category exists in either, add it to the list of categories.
        for category in itertools.chain(self.recipe_dict.keys(), other_recipe.recipe_dict.keys()):
            if category not in category_list:
                category_list.append(category)
        #iterate through category list
        for category in category_list:
            #get the lengths of the ingredients in each category
            if self.recipe_dict.get(category):
                self_ingredient_num = len(self.recipe_dict[category])
            else:
                self_ingredient_num = 0
            if other_recipe.recipe_dict.get(category):
                other_ingredient_num = len(other_recipe.recipe_dict[category])
            else:
                other_ingredient_num = 0

            #add them together ==> total ingredient number
            total_ingredient_num = (self_ingredient_num + other_ingredient_num)
            #extract half: get half of the total
            ingredient_extract_num = total_ingredient_num/2
            #iterate ingredient_extract_num times
            for _ in range(math.ceil(ingredient_extract_num)):
                # randomly generate a number in the range of 0 to
                # total_ingredient_num - 1
                ingredient_index = random.randint(0, total_ingredient_num - 1)
                # if the index is smaller than the self's ingredient number in
                # that category, find a subsititute and substitute it into the
                # ingredient. add that ingredient to the list of the
                # corresponding category in recipe_combo
                if ingredient_index < self_ingredient_num:
                    list(self.recipe_dict[category])[ingredient_index][0] = \
                    self.substitution(list(self.recipe_dict[category]) \
                            [ingredient_index][0])

                    ingredient, amount = list(self.recipe_dict[category]) \
                        [ingredient_index]
                    recipe_combo.add_ingredient(category, ingredient, amount)

                # if the index is equal to or higher than the self's ingredient
                # number in that category, go to the other recipe and find a
                # subsititute and substitute it into the ingredient. add that
                # ingredient to the list of the corresponding category in
                # recipe_combo
                else:
                    ingredient_index -= self_ingredient_num
                    list(other_recipe.recipe_dict[category])[ingredient_index][0] =\
                    self.substitution(list(
                        other_recipe.recipe_dict[category])[ingredient_index][0])

                    ingredient, amount = list(
                        other_recipe.recipe_dict[category])[ingredient_index]
                    recipe_combo.add_ingredient(category, ingredient, amount)
        self.mystery_ingredient()
        return recipe_combo



    def get_recipe_dict(self):
        """
        Gets the recipe in dictionary format.
        """
        return self.recipe_dict

    def normalization(self):
        """
        Normalises the recipe such that the total amount is 100 ounces.
        """
        if self.recipe_dict:
            total_amount = Amount(0)
            for category, info in self.get_recipe_dict().items():
                total_amount += info[1]

            if total_amount.get_num() != 100:
                coefficient = Amount(100)/total_amount
                for category, info in self.recipe_dict.items():
                    self.recipe_dict[category][1] = info[1] * coefficient

    def get_recipe(self, title):
        """
        Gets the recipe in Markdown format, so that it looks pretty!

        Arguments:
            title: The title of the recipe we want.
        """
        copy_dict = self.recipe_dict
        output = ""
        output += "# {0}\n\n".format(title)
        output += "## INGREDIENTS\n"
        output += str(self) + "\n"
        output += "## METHOD\n"
        output += "1. Preheat oven to {0} degrees F\n".format(random.randint(325, 375))
        output += "2. Cream together the {0} until smooth\n".format(
            ", ".join([str(i[0]) for i in copy_dict.pop("fatsoils", [])\
            + copy_dict.pop("sweeten", [])]))
        output += "3. Beat in the {0} one at a time, then stir in the {1}\n".format(
            ", ".join([str(i[0]) for i in copy_dict.pop("eggs", [])]),
            ", ".join([str(i[0]) for i in copy_dict.pop("extracts", [])]))
        output += "4. Dissolve the {0} with hot water, then add to batter along with {1}\n".format(
            ", ".join([str(i[0]) for i in copy_dict.pop("leaven", [])]),
            ", ".join([str(i[0]) for i in copy_dict.pop("salt", [])]))
        copy_dict = self.recipe_dict

        output += "5. Stir in {0}\n".format(
            ", ".join([str(i[0][0]) for i in copy_dict.values()]))
        output += "6. Spoon mixture onto a greased baking tray\n"
        output += "7. Bake for {0} minutes or until golden brown\n".format(random.randint(10, 15))

        return output

    def __str__(self):

        output = ""
        if not self.recipe_dict:
            return "Blank recipe"

        for _, arr in self.recipe_dict.items():
            for ingredient, amount in arr:
                if amount.get_num() < 0:
                    output += "\ta pinch of {0}\n".format(str(ingredient))
                else:
                    output += "\t{0} {1}\n".format(str(amount),
                                                   str(ingredient))
        return output

    def __repr__(self):
        output = ""
        for ingredient, amount in self.recipe_dict.items():
            output += "({0}: {1}),".format(repr(amount), repr(ingredient))
        return "Recipe({0})".format(output)


def recipe_pairs(recipe_list):
    """
    This function creates pairs of recipes through using two simple for loops.

    Arguments:
        recipe_list: the list of recipes that we wish to make pairs from.
    """
    pairs = []
    for i in range(len(recipe_list) - 1):
        for j in range(i+1, len(recipe_list)):
            pairs.append((recipe_list[i], recipe_list[j]))
    return pairs


#def natural_selection(offspring_list):
#    offspring_fitness = []
#    selected_offspring = []
#    for recipe in offspring_list:
#        recipe_fitness = recipe.fitness_level()
#        offspring_fitness.append((recipe, recipe_fitness))
#    sorted_fitness = sorted(offspring_fitness, key=lambda x: x[1])
#    selected_offspring = sorted_fitness[int(len(offspring_fitness)/2):]
#    return selected_offspring

def genetic_iteration(recipe_list):
    """
    This function runs an genetic iteration of our recipe algorithm by creating
    pairs of recipes, and combining them and substituting ingredients using our
    knowledge base. It then ranks the recipes that we generate, returning the
    n top recipes (with n being the size of the original list).

    Arguments:
        recipe_list: the recipe list that we start the iteration with.
    """
    orig_len = len(recipe_list)
    pairs = recipe_pairs(recipe_list)
    new_recipes = []
    for recipe1, recipe2 in pairs:
        new_recipe = recipe1.new_recipe_combo(recipe2)
        new_recipes.append(new_recipe)
    # Return list consisting of top 50% of original recipes and top 50% of new recipes, and strip
    # their fitness levels away from them.
    rank = recipe_rankings(new_recipes)

    return [r[0] for r in rank][0:orig_len]

def convert_format(recipe_list):
    """
    Takes a list of lists that contains the ingredients of our recipe, and
    converts it to our new recipe format.

    Arguments:
        recipe_list: The list of lists that contains the recipe we wish to
        convert.
    """
    new_recipe = Recipe()
    for ingredient, amount in recipe_list:
        working_string = new_recipe.get_ingredient_string(ingredient)
        if working_string:
            category = SUB_DATA[TRANS_DATA[working_string]]["category"]
            new_recipe.add_ingredient(category, Ingredient(working_string),
                                      Amount(amount))
        else:
            category = "misc"
            new_recipe.add_ingredient(category, Ingredient(ingredient),
                                      Amount(amount))
    return new_recipe

def get_fitness(recipe):
    """
    This function is a very simple one: it takes a recipe and returns a tuple of
    the recipe itself and the fitness level. This is so we can parallelise it
    using joblib.

    Arguments:
        recipe: Recipe to find fitness level of and to return.
    """
    return (recipe, recipe.fitness_level())

def recipe_rankings(recipe_list):
    """
    This function takes in the recipe list and gets the result score and pair score given
    in the fitness_level function in the Recipe class. It creates a dictionary with the
    recipe name as the key and the two scores as its value (in the form of a tuple). We
    find the rankings of the individual scores and combine them together to form a final
    ranking to determine the fittest amongst the recipes.
    """
    #create a dictionary to store recipes and its two scores
    recipe_scores = dict()
    #a list containing tuples in the form of (recipe, result_score)
    result_scores = []
    #a list containing tuples in the form of (recipe, pair_score)
    pair_scores = []
    #a list containing tuples in the form of (recipe, food2vec_score)
    food2vec_scores = []
    #a list containing the final rankings of the recipes via fitness level
    final_rankings = []
    #popularizing recipe_scores
    recipe_scores = Parallel(n_jobs=-1,
                             backend="multiprocessing")(delayed
                                                        (get_fitness)(recipe)
                                                        for recipe in
                                                        recipe_list)

    recipe_scores = dict(recipe_scores)
    #popularizing result_scores and pair_scores
    for recipe, fitnesspair in recipe_scores.items():
        result_scores.append((recipe, fitnesspair[0]))
        pair_scores.append((recipe, fitnesspair[1]))
        food2vec_scores.append((recipe, fitnesspair[2]))
    #sort the two scores via descending order, because the higher the score,
    #the smaller your index is.
    result_scores.sort(key=lambda x: x[1], reverse=False)
    pair_scores.sort(key=lambda x: x[1], reverse=True)
    food2vec_scores.sort(key=lambda x: x[1], reverse=True)
    #iterating through the recipes and finding their rankings in each
    #ranking list, and adding the indices together. Append the recipe
    #and its final_ranking to the final_rankings list.
    for recipe in recipe_scores.keys():
        result_ranking = [pair[0] for pair in result_scores].index(recipe)
        pair_ranking = [pair[0] for pair in pair_scores].index(recipe)
        food2vec_ranking = [pair[0] for pair in food2vec_scores].index(recipe)
        final_ranking = result_ranking + pair_ranking + food2vec_ranking
        final_rankings.append((recipe, final_ranking))
    #sort final_rankings
    final_rankings.sort(key=lambda x: x[1])
    #return final_rankings
    return final_rankings

def main():
    """
    Main function - loads recipe files and runs iterations of the genetic algorithm.
    """

    # Start off by parsing arguments from the command line.
    parser = argparse.ArgumentParser(description="Genetic algorithm-based cookie recipe maker!")
    parser.add_argument("iterations", type=int, help="Number of iterations to run.")
    parser.add_argument("filename", type=str, help="Save final recipe")

    args = parser.parse_args()

    # Load all of the recipes from the directory to create both our inspiring set and lists of each
    # recipe.
    recipes_list = []
    inspiring_set = []
    with open("inspiring_set.json", "r") as iset_file:
        inspiring_set_lists = json.load(iset_file)
        for set_list in inspiring_set_lists:
            inspiring_set += set_list
            recipes_list.append(convert_format(set_list))
    # Remove existing iterations directory if it exists.
    if os.path.exists("iterations"):
        shutil.rmtree("iterations")
    os.mkdir("iterations")

    for _ in tqdm(range(0, args.iterations)):
        recipes_list = genetic_iteration(recipes_list)

    dish_names = ["cookies", "biscuits", "shortbread"]
    recipe_sorted = sorted(recipes_list[0].get_category_tuples(),
                           key=lambda x: x[1].get_num(),
                           reverse=True)
    recipe_title = "{0} star {1} and {2} {3}".format(args.iterations,
                                                     recipe_sorted[0][0],
                                                     recipe_sorted[1][0],
                                                     random.choice(dish_names))

    #recipes_list[0].normalization()
    with open(args.filename, 'w') as output_file:
        output_file.write(recipes_list[0].get_recipe(recipe_title))

if __name__ == "__main__":
    main()
