# PQ3-Smart-Cookies
Jack Beckitt-Marshall, Yvonne Fang, Kevin Li – Bowdoin College – CSCI 3725

This project uses cookie recipes on the internet to generate a selection of new, unique recipes based off of the popularity and the compatibility of its ingredients. We then created a food2vec fitness function that uses Markov Chains to determine the fittest of the offspring to produce the next generation. We get our final cookie recipe by doing 50 iterations and getting the offspring with the highest fitness level.

# How to Run
1. Install the required packages (inflect, numpy, joblib, and tqdm) on your terminal

`$ pip install inflect numpy joblib tqdm`

or if you're using Anaconda:

`$ conda install inflect numpy joblib tqdm`

2. Run program under the format: `python3.7 cookie_generation.py [number of iterations] [name of save file] (recommended 50 iterations)`
3. Open saved file in Markdown format.
4. Enjoy baking!

# Works Cited

Altosaar, Jaan. _Food2vec - Augmented Cooking with Machine Intelligence (version Master)._ Windows/Mac/Linux. Princeton, 2017. https://jaan.io/food2vec-augmented-cooking-machine-intelligence/.

Schollz, Zack. _Meanrecipe_ (version Master). Windows/Mac/Linux. Seattle, 2019. https://github.com/schollz/meanrecipe.

Also used StackOverflow as well as Python and BeautifulSoup documentation.
