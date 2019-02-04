# import libraries
from urllib.request import urlopen
from bs4 import BeautifulSoup

MEASURES = ["pound","cup", "spoon", "liter", "pint", "quart", "taste","tsp","tbsp"]

def scrape_allrecipes(url):
    # query the website and return the html to the variable ‘page’
    page = urlopen(url)

    # parse the html using beautiful soup and store in variable `soup`
    soup = BeautifulSoup(page, 'html.parser')

    title = soup.find('h1', { 'id': "recipe-main-content"}).text.strip()
    
    servings = soup.find('span', {'class':"recipe-ingredients__header__toggles"}).find('meta')['content']
    #print(servings)
   
    
    #print(title)
    ingred_list_1 = soup.find('ul', { 'class': "checklist dropdownwrapper list-ingredients-1"})
    ingred_list_2 = soup.find('ul', { 'class': "checklist dropdownwrapper list-ingredients-2"})
    ingred_list = ingred_list_1.find_all('span') + ingred_list_2.find_all('span')
    ingredients = {}
    for item in ingred_list[:-1]: #don't include the add to list item
        #tokenize and parse
        tokens = item.text.split()

        step=0
        number = 0
        measure = "unit"
        ingredient = ""
        for token in tokens:
            if step==0:
                try:
                    number+=float(token)
                except:
                    if '/' in token:
                        try:
                            number+= float(token.split('/')[0])/float(token.split('/')[1])
                        except:
                            step=1
                            if any([i in token for i in MEASURES]):
                                measure = token
                                step = 2
                            else:
                                step = 2
                                ingredient = token
                    else:
                        step=1
                        if any([i in token for i in MEASURES]):
                            measure = token
                            step = 2
                        else:
                            step = 2
                            ingredient = token
            elif step == 2:
                ingredient += " "+token
        ingredients[ingredient] = (number,measure)
    #print(ingredients)

    instruct_list = soup.find('ol', { 'class': "list-numbers recipe-directions__list"}).find_all("span")
    instructions = ""
    for line in instruct_list:
        instructions += line.text+"\r\n"
    #print(instructions)
    return title,servings,ingredients,instructions
    
                            
        
    


#url = 'https://www.allrecipes.com/recipe/16354/easy-meatloaf/'
#url = 'https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/'
#url = 'https://www.allrecipes.com/recipe/20144/banana-banana-bread/'
#scrape_allrecipes(url)


