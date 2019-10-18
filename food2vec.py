"""
food2vec.py - Jack Beckitt-Marshall, Kevin Li and Yvonne Fang, PQ3, CSCI 3725
18 October 2019

A bunch of utilities that allow us to use the food2vec model, found here:
https://jaan.io/food2vec-augmented-cooking-machine-intelligence/
"""

import json
import itertools
import statistics
import random

import numpy as np
import inflect

class Word2VecUtils:
    """
    Word2VecUtils class: defines a bunch of utilities that allow us to use the
    food2vec library in a nice, Pythonic way.
    """

    def get_ingredient_string(self, ingredient):
        """
        This function essentially manipulates the string of the ingredient,
        essentially seeing if we can find one that is within our knowledge
        base so we can get categories and substitutions

        Arguments:
            ingredient - an Ingredient instance where we want to find the
                corresponding string.
        """
        i_engine = inflect.engine()
        string = str(ingredient).capitalize() # Ingredients in sentence case.
        if i_engine.singular_noun(string):
            string = str(i_engine.singular_noun(string)).split(" ")
        else:
            string = string.split(" ")
        for i in range(len(string), -1, -1):
            for combo in itertools.combinations(string, i):
                if self.word_vecs.get(" ".join(combo).capitalize()):
                    return " ".join(combo)
        return None

    def __init__(self, wordvec_file=None):
        if wordvec_file:
            with open(wordvec_file, "r") as wordvec_file_handle:
                self.word_vecs = json.load(wordvec_file_handle)
        else:
            with open("foodVecs.js", "r") as wordvec_file_handle:
                self.word_vecs = json.load(wordvec_file_handle)

    def get_matches(self, vec):
        """
        Takes a vector, and dots it with every other food vector in order to
        get the similarities to every other food. Returns a sorted list of all
        the similarities to other foods as tuples.

        Arguments:
            vec: Food vector to compare to all other foods.
        """
        sims = []
        for word, word_vec in self.word_vecs.items():
            sim = np.dot(vec, np.array(word_vec))
            sims.append((word, sim))
        return sorted(sims, key=lambda x: x[1])

    def recommendation(self, word_list):
        """
        Takes a list of foods, and finds all of the matches to other foods:
        1 represents exact match, and 0 represents no match at all.

        Arguments:
            word_list: List of foods to find recommendations for.
        """
        input_vecs = []
        for word in word_list:
            input_vecs.append(self.word_vecs[word])
        data = np.array(input_vecs)
        sum_vectors = np.sum(data, 0)
        target = sum_vectors * (1.0 / len(input_vecs))
        matches = self.get_matches(target)
        return dict(matches)

    def food2vec_score(self, word_list):
        """
        Given a list of foods, it will get a score based on the similarity of
        all foods to each other, using the recommendation function and
        combinations of 1 and 2 foods.

        Arguments:
            word_list: List of foods to find score for.
        """
        new_word_list = []
        scores = []
        for word in word_list:
            if self.get_ingredient_string(word):
                new_word_list.append(self.get_ingredient_string(word).capitalize())

        combos = []
        for i in range(1, 2):
            combos += list(itertools.combinations(new_word_list, i))

        for combo in combos:
            score = 1.0
            temp_word_list = new_word_list.copy()
            for elem in combo:
                temp_word_list.remove(elem)

            rec = self.recommendation(list(combo))

            for elem in temp_word_list:
                score *= rec[elem]

            scores.append(score)

        return statistics.mean(scores)

    def get_new_ingredient(self, word_list):
        """
        With a list of ingredients, find an ingredient that will go well with
        them!

        Arguments:
            word_list: List of foods to find ingredient for.
        """
        new_word_list = []
        for word in word_list:
            if self.get_ingredient_string(word):
                new_word_list.append(self.get_ingredient_string(word).capitalize())

        rec = self.recommendation(new_word_list)
        rand_ing_choice = random.randint(0, 4)
        return sorted(rec.items(), key=lambda item: item[1],
                      reverse=True)[rand_ing_choice]
