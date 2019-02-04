# import libraries
from urllib.request import urlopen
from bs4 import BeautifulSoup
from database import get_all_recipes, get_recipe, create_recipe, get_recipe_name, edit_recipe, add_late_plate, add_measure, create_menu, get_menu, get_menu_date, get_menus_week, get_all_menus, add_ingredient, get_ingredients


# specify the url
quote_page = 'http://dh.scripts.mit.edu/essen/recipes/'
#'https://www.bloomberg.com/quote/SPX:IND'

# query the website and return the html to the variable ‘page’
page = urlopen(quote_page)

# parse the html using beautiful soup and store in variable `soup`
soup = BeautifulSoup(page, 'html.parser')

#print(soup.prettify())
rezept_table = soup.find('table', { 'class': "table table-bordered table-striped"})

recipe_urls = []
prefix = 'http://dh.scripts.mit.edu/'
all_links = rezept_table.find_all('a')
for link in all_links:
    recipe_urls.append(prefix+link.get("href"))
#print(recipe_urls)

def scrape_dh(url):
    # query the website and return the html to the variable ‘page’
    page = urlopen(url)

    # parse the html using beautiful soup and store in variable `soup`
    soup = BeautifulSoup(page, 'html.parser')

    #print(soup.prettify())
    title = soup.find('div', { 'class': "page-header"}).find('h1').text.strip()
    print(title)

    recipe = soup.find('div', { 'class': "span7 offset1"})
    servings = recipe.find('h2').text.strip()[8:]
    ingred_table = recipe.find('table', {'class':'table'}).find_all('tr')
    ingredients = {}
    for row in ingred_table:
        ingredients[row.find_all('td')[0].text.strip()] = (row.find_all('td')[1].text.strip(),row.find_all('td')[2].text.strip())
    instruct = recipe.find('div',{'class':'code'}).find('pre').text.strip()
    return title, servings, ingredients, instruct


for url in recipe_urls[200:]:
    #print(url)
    name, serv, ingreds, inst = scrape_dh(url)
    #print(name, serv, ingreds, inst)
    for ing in ingreds:
        add_ingredient(ing)
        add_measure(ingreds[ing][1])
    create_recipe(name,serv,ingreds,inst,"Other")


