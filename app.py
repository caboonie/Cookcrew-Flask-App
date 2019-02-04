from flask import Flask, request, url_for, redirect,flash,render_template, send_from_directory, jsonify
from database import *
from web_scraping_allrecipe import scrape_allrecipes
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse

from flask_bootstrap import Bootstrap

from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from models import User
from flask import session
import json
import requests
from wit import Wit #language processing api
import speech_recognition as sr

import datetime

audio_data = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'

login = LoginManager(app)
login.login_view = 'login'

bootstrap = Bootstrap(app) #gives me a bootstrap-base.html I can extend

client = Wit('AJIG5BFZ67C6ANTSE7WCCM7OADFGFIK3')
wit_access_token = 'FXNX3SEK6Z4X64TJZ75UDBZLVWBBPUB6'
API_ENDPOINT = 'https://api.wit.ai/speech'

DAY_NAMES = ["Sunday Brunch","Sunday Dinner","Monday Dinner","Tuesday Dinner","Wednesday Dinner","Thursday Dinner"]
DAY_OFFSETS = {"Sunday Brunch":0,"Sunday Dinner":0,"Monday Dinner":1,"Tuesday Dinner":2,"Wednesday Dinner":3,"Thursday Dinner":4}
r = sr.Recognizer()

from groupy.client import Client
token = "d0d1772007dc0137492936e4528fcc3b"
client = Client.from_token(token)

#groups = client.groups.list(omit="memberships")
#To see what groupmes available
#for group in groups.autopage():
#    print(group.name)
group_chat_list = ["DH","2018"] #list of stings that are in the groupchat name
        

def post_to_DH(message):
    groups = client.groups.list(omit="memberships")
    for group in groups.autopage():
        if all([a in group.name for a in group_chat_list]): 
            message = group.post(text=message)

def read_DH(num_messages):
    groups = client.groups.list(omit="memberships")
    #print("READING DH", groups)
    #Return as json object

    for group in groups.autopage():
        #print("GROUP NAME",group.name)
        if all([a in group.name for a in group_chat_list]): 
            num_so_far = 0
            messages = {"length":num_messages}
            for message in group.messages.list_all():
                messages[str(num_so_far)] = {"name":message.name,"avatar":message.avatar_url,"text":message.text}
                num_so_far+=1
                if num_so_far>=num_messages:
                    return jsonify(messages)



def decode_phrase(wav_file_bytes):
    decoder.start_utt()
    decoder.process_raw(wav_file_bytes, False, False)
    decoder.end_utt()
    words = []
    [words.append(seg.word) for seg in decoder.seg()]
    return words

@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='favicon.ico')

@login.user_loader
def wrapper(id):
    return load_user(id)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("Already logged in")
        return redirect(url_for("/"))
    if request.method == 'POST':
        user = get_user_name(request.form["username"])
        if user is None or not check_password_hash(user.password_hash,request.form["password"]):
            flash("Invalid username or password")
            return redirect(url_for('login'))
        if "remember" in request.form:
            login_user(user, remember=True)
        else:
            login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != "":
            next_page = "/"
        return redirect(next_page)
    return render_template('login.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash("Already logged in")
        return redirect("/")
    if request.method == 'POST':
        user = get_user_name(request.form["username"])
        if user is not None:
            flash("Username already exists")
            return redirect(url_for('signup'))
        else:
            keys = [key for key in request.form]
            general_schedule = {}
            for i in range(len(keys)):
                if "Meal" in keys[i]:
                    if request.form[keys[i]]: #if the meal is included in weekly meals
                        day_count = int(keys[i][4:])
                        day_name = DAY_NAMES[day_count]
                        general_schedule[day_name] = request.form["day_"+day_count+"_names"].split(',')
                        
            user = create_user(request.form["username"],request.form["password"],general_schedule)
            user.set_password(request.form["password"])

            login_user(user)
            return redirect("/")
    return render_template('signup.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/', methods=['GET', 'POST'])
def cookbook_home():
    date = datetime.datetime.now()
    date = datetime.date(date.year,date.month,date.day)
    if request.method == 'POST':
        print(request.form)
        if "previous" in request.form:
            date -= datetime.timedelta(days=(7))
            print("DATE",date)
            return redirect('/week_menus/'+str(date))
        elif "next" in request.form:
            date += datetime.timedelta(days=(7))
            return redirect('/week_menus/'+str(date))
        elif "this" in request.form:
            return redirect('/week_menus/'+str(date))
    if current_user.is_authenticated:
        menus = get_menu_date(date,current_user.id)
    else:
        menus = []
    
    
    return render_template("home.html", menu_exist = menus!=[], menus=menus)

    

@app.route('/recipes', methods=['GET', 'POST'])
def recipes_page():
    recipes = get_all_recipes()
    recipes_api = []
    
    if request.method == 'POST':
        print(request.form)
        
        if "recipe_name" in request.form: #find specific recipe:
            print("FILTERING BY RECIPE")
            recipe = get_recipe_name(request.form['recipe_name'])
            return redirect('/recipes/'+str(recipe.id))
        
        else: #filter based on ingredients:

            #API STUFF: http://www.recipepuppy.com/api/?i=onions,garlic&q=omelet&p=1
            
            ingredients = [request.form[key] for key in request.form if request.form[key]!=""]
            
            response = requests.get("http://www.recipepuppy.com/api/?i="+",".join(ingredients)+"&p=1")
            recipes_api = json.loads(response.content)['results']
            
            recipes = [recipe for recipe in recipes if all([ingredient in recipe.ingredients for ingredient in ingredients])]
    
    recipes.sort(key = lambda x:x.name.lower())
    
    return render_template("recipes.html", recipes=recipes, ingredient_list = get_ingredients()['ing_list'],
                           recipe_list=[recipe.name for recipe in get_all_recipes()],recipes_api=recipes_api)

@app.route('/recipes/filter/<string:category>', methods=['GET', 'POST'])
def recipes_filter_page(category):
    recipes = get_all_recipes()
    recipes_api = []
    
    if request.method == 'POST':
        print(request.form)
        
        if "recipe_name" in request.form: #find specific recipe:
            print("FILTERING BY RECIPE")
            recipe = get_recipe_name(request.form['recipe_name'])
            return redirect('/recipes/'+str(recipe.id))
        
        else: #filter based on ingredients:

            #API STUFF: http://www.recipepuppy.com/api/?i=onions,garlic&q=omelet&p=1
            
            ingredients = [request.form[key] for key in request.form if request.form[key]!=""]
            
            response = requests.get("http://www.recipepuppy.com/api/?i="+",".join(ingredients)+"&p=1")
            recipes_api = json.loads(response.content)['results']
            
            recipes = [recipe for recipe in recipes if all([ingredient in recipe.ingredients for ingredient in ingredients])]
            
    recipes.sort(key = lambda x:x.name)
    if category not in  ["","All"]:
        recipes = [recipe for recipe in recipes if recipe.category==category]
        #print(recipes)
  
    return render_template("recipes.html", recipes=recipes, ingredient_list = get_ingredients()['ing_list'],
                           recipe_list=[recipe.name for recipe in get_all_recipes()],recipes_api=recipes_api)

@app.route('/menus')
@login_required
def menus_page():
    menus = get_all_menus(current_user.id)
    print("MENUS",[menu.day_name for menu in menus])
    return render_template("menus.html", menus=menus)

def ingredient_check(ing,sunday):
    menus = get_menus_week(sunday,current_user.id)
    days_using_ingredient = [ing,[]] #list starting with ingredient, and then tuples of days, amounts, and measures
    for single_menu in menus:
        for dish in single_menu.dishes:
            recipe = get_recipe_name(dish)
            for ingredient in recipe.ingredients:
                if ing.lower() in ingredient.lower():
                    amount,measure = recipe.ingredients[ingredient]
                    days_using_ingredient[1].append((single_menu.day_name,float(amount)*single_menu.servings/recipe.servings,measure,ingredient))
    return days_using_ingredient
    

@app.route('/menus/<string:menu_id>',methods=['GET', 'POST'])
@login_required
def menu_page(menu_id):
    print("ID NUM:",menu_id)
    session["current_menu_url"] = request.url
    menu = get_menu(menu_id)
    days_using_ingredient = []
    if request.method == 'POST':
        print("-------------------------")
        print("updating menu",menu_id)
        print(request.form)
        if "late_plate_submit" in request.form:
            names = [request.form[key] for key in request.form if request.form[key]!="" and key != "late_plate_submit"]
            print("names",names)
            edit_late_plate(menu_id,names)
        elif "ingredient_check_submit" in request.form:
            ing = request.form["ingredient"]
            sunday = menu.sunday
            days_using_ingredient = ingredient_check(ing,sunday)
                            
    print("PLATES:",menu.late_plates)
    dish_objects = []
    for dish in menu.dishes:
        dish_objects.append(get_recipe_name(dish))
    print(dish_objects)
    print("MENU",menu)
    
    playlists = load_user(current_user.id).playlists
  
    return render_template("menu.html", menu=menu, dishes = dish_objects,ingredient_list = get_ingredients()['ing_list'],
        ing_check=days_using_ingredient, playlists = playlists)

@app.route('/week_menus')
@login_required
def week_menus_redirect():
    date = datetime.datetime.now()
    num = date.weekday()
    #print(num)
    if num != 6:
        date -= datetime.timedelta(days=(num+1)) #now it is the sunday
    date = datetime.date(date.year,date.month,date.day)
    print(date)
    sunday = datetime.date(date.year,date.month,date.day)
    return redirect('/week_menus/'+str(sunday))

@app.route('/week_menus/<string:sunday>', methods=['GET', 'POST'])
@login_required
def week_menus_page(sunday):
    date = sunday.split("-")
    date = datetime.date(int(date[0]),int(date[1]),int(date[2]))
    num = date.weekday()
    print(num)
    if num != 6:
        date -= datetime.timedelta(days=(num+1)) #now it is the sunday
        
    if request.method == 'POST':
        print(request.form)
        if "previous" in request.form:
            date -= datetime.timedelta(days=(7))
            print("DATE",date)
            return redirect('/week_menus/'+str(date))
        elif "next" in request.form:
            date += datetime.timedelta(days=(7))
            return redirect('/week_menus/'+str(date))
        elif "this" in request.form:
            date = datetime.datetime.now()
            date = datetime.date(date.year,date.month,date.day)
            return redirect('/week_menus/'+str(date))

        
    print(date)
    menus = get_menus_week(date,current_user.id)
    print("MENUS",menus, menus!=[])
    return render_template("week_menus.html", menu_exists = menus!=[], menus=menus, date=sunday)

@app.route('/search')
def search_page():
    return render_template("search.html")

@app.route('/plan', methods=['GET', 'POST'])
@login_required
def plan_page():
    if request.method == 'POST':
        if True: #try:
            servings = request.form['servings']
            date_list = request.form['sunday_date'].split(',')
            sunday = datetime.date(int(date_list[0]),int(date_list[1])+1,int(date_list[2]))
            print("SUNDAY:",sunday)
            clear_menu(sunday)
            keys = [key for key in request.form]
            #meals = {}
            for i in range(len(keys)):
                if "Meal" in keys[i]:
                    if request.form[keys[i]]: #if the meal is being served that week
                        dishes = []
                        j=i+1
                        while j<len(keys) and "dish" in keys[j]:
                            dishes.append(request.form[keys[j]])
                            #If dish not in database, raise a flag TODO!
                            j+=1
                        print(dishes,"DISHES FOR MENU")
                        if dishes!=[]:
                            #meals[keys[i][4]] = dishes #the fourth character is the day number
                            day_count = int(keys[i][4:])
                            day_name = DAY_NAMES[day_count]
                            day = sunday + datetime.timedelta(days=DAY_OFFSETS[day_name])
                            day = datetime.date(day.year,day.month,day.day)
                            #print("day",day)
                            create_menu(current_user.id,sunday,day,day_name,int(servings),dishes)
            print("made a menu")
        else:
            print("couldn't make menu")
    recipes = get_all_recipes()
    recipe_list = []
    for recipe in recipes:
        recipe_list.append(recipe.name)
    return render_template("plan.html", recipe_list = recipe_list)

@app.route('/recipes/<string:id>', methods=['GET', 'POST'])
def recipe_page(id):
    if request.method == 'POST':
        '''
        print("POSTING")
        #API for nutritional info
        APP_ID = "5b415a68"
        APP_KEY = "45457d075f44f019a7d1a6b97625a11c"
        recipe_json = open("recipe.json")
        headers = {
            'Content-Type': 'application/json',
        }

        params = (
            ('app_id', APP_ID),
            ('app_key', APP_KEY),
        )

        response = requests.post('https://api.edamam.com/api/nutrition-details', headers=headers, params=params, data=recipe_json)

        print(response.content)
        #nutritional_api = json.loads(response.content)
        #print(nutritional_api)
        '''
        
        #print(request.form)
        ingredients={}
        for key in request.form:
            #print("key",key)
            if 'ingredient_' in key:
                  number = key[11:]
                  #print(number)
                  tup = (request.form["amount_"+number],request.form["measurement_"+number])
                  #print("ing",request.form[key],tup)
                  ingredients[request.form[key]]=tup
                  add_ingredient(request.form[key])
                  add_measure(request.form["measurement_"+number])
            #print("ingreds",ingredients)
        #print("REZEPT:",request.form['recipe'].replace('\r\n','<br>'))
        edit_recipe(id,request.form['name'],request.form['servings'],ingredients,request.form['recipe'],request.form['category'])

    recipe = get_recipe(id)
    #print(recipe.ingredients)
    #print(recipe.recipe)

    return render_template("recipe.html", recipe=recipe, ingredient_list = get_ingredients()['ing_list'],measure_list = get_ingredients()['meas_list'])

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_page():
    if request.method == 'POST':
        print(request.files)
        print(request.form)
        if "url" in request.form and request.form["url"]!="":
            name,servings,ingredients,recipe = scrape_allrecipes(request.form['url'])
            for ing in ingredients:
                add_ingredient(ing)
                add_measure(ingredients[ing][1])
            create_recipe(name,servings,ingredients,recipe,request.form['category'])
        else:
            ingredients={}
            for key in request.form:
                print("key",key)
                if 'ingredient_' in key:
                      number = key[11:]
                      print(number)
                      tup = (request.form["amount_"+number],request.form["measurement_"+number])
                      print("ing",request.form[key],tup)
                      ingredients[request.form[key]]=tup
                      add_ingredient(request.form[key])
                      add_measure(request.form["measurement_"+number])
                print("ingreds",ingredients)
            print("REZEPT:",request.form['recipe'].replace('\r\n','<br>'))
            create_recipe(request.form['name'],request.form['servings'],ingredients,request.form['recipe'],request.form['category'])

    return render_template("add.html", ingredient_list = get_ingredients()['ing_list'],measure_list = get_ingredients()['meas_list'])

@app.route('/shopper')
@login_required
def shopper_page():
    date = datetime.datetime.now()
    num = date.weekday()
    #print(num)
    if num != 6:
        date -= datetime.timedelta(days=(num+1)) #now it is the sunday
    date = datetime.date(date.year,date.month,date.day)
    print(date)
    sunday = datetime.date(date.year,date.month,date.day)
    return redirect('/shopper/'+str(sunday))


BULK_ITEMS = ["milk","sugar","flour","butter","oil"]
NOT_BUY = ["water","ice"]

@app.route('/shopper/<string:sunday>', methods=['GET', 'POST'])
@login_required
def shopper_page_specific(sunday):
    try:
        date = sunday.split("-")
        date = datetime.date(int(date[0]),int(date[1]),int(date[2]))
        num = date.weekday()
        print(num)
        if num != 6:
            date -= datetime.timedelta(days=(num+1)) #now it is the sunday
    except:
        return redirect('/error/incorrect-date')
        
    if request.method == 'POST':
        print(request.form)
        if "previous" in request.form:
            date -= datetime.timedelta(days=(7))
            print("DATE",date)
            return redirect('/shopper/'+str(date))
        elif "next" in request.form:
            date += datetime.timedelta(days=(7))
            return redirect('/shopper/'+str(date))
        
    menus = get_menus_week(date,current_user.id)
    amounts_total = {}
    for menu in menus:
        total_servings = float(menu.servings)
        for dish in menu.dishes:
            recipe = get_recipe_name(dish)
            recipe_servings = float(recipe.servings)
            for ingred in recipe.ingredients:
                amount,measure = recipe.ingredients[ingred]
                if any([i in ingred.lower() for i in NOT_BUY]) or "taste"in measure:
                    break
                if ingred == "unsalted butter":
                    ingred = "butter"
                if "clove" in measure:
                    measure = "unit(s)"
                if "teaspoon" in measure:
                    measure = "tsp(s)"
                if "tablespoon" in measure:
                    measure = "tbsp(s)"
                if "cup" in measure:
                    measure = "cup(s)"
                if "unit" in measure:
                    measure = "unit(s)"
                if any([i in ingred.lower() for i in BULK_ITEMS]):
                    if measure == "tbsp(s)":
                        measure = "cup(s)"
                        amount = float(amount)/16
                    if measure == "oz(s)":
                        measure = "cup(s)"
                        amount = float(amount)/8
                if ingred in amounts_total:
                    if measure in amounts_total[ingred]:
                        amounts_total[ingred][measure] += float(amount)*total_servings/recipe_servings
                    elif "tsp" in measure and "tbsp(s)" in amounts_total[ingred]:
                        amounts_total[ingred]["tbsp(s)"] += float(amount)*total_servings/recipe_servings/3
                    elif "tbsp" in measure and "tsp(s)" in amounts_total[ingred]:
                        amounts_total[ingred]["tsp(s)"] += float(amount)*total_servings/recipe_servings*3
                    else:
                        amounts_total[ingred][measure] = float(amount)*total_servings/recipe_servings
                else:
                    amounts_total[ingred] = {measure:float(amount)*total_servings/recipe_servings}
    sorted_ingred = list(amounts_total.keys())
    sorted_ingred.sort(key = lambda x:x.lower())
                                     
    return render_template("shopper.html",sunday=sunday,amounts_total=amounts_total, sorted_ingred= sorted_ingred, menu_exist=len(sorted_ingred)!=0)
    
@app.route('/error/<string:report>')
def error_page(report):
    return render_template("error.html", report=report)

@app.route('/speech_start')
def speech_page_start():
    return redirect(url_for("speech_page",start_record=True))

@app.route('/speech',methods=['GET', 'POST'])
def speech_page(start_record=False):
    print(start_record)
    if request.method == 'POST':
        if True:
            f = request.files['file']
            print("filename",f.filename)
            audio = f.read() #as bytes
            
            if f.filename=="stream.WAV":
                savefile=open('audio.wav','wb')
                savefile.write(audio)
                savefile.close()
                audio_for_sr = sr.AudioFile("audio.wav") #WavFIle
                with audio_for_sr as source:
                    audio_for_sr = r.record(source)
                print("audio for sr type: ",type(audio_for_sr))
                try:
                    speech = r.recognize_sphinx(audio_for_sr)
                    print("Sphinx thinks you said '" + speech + "'")
                    if "voice" in speech and "command" in speech:
                        session['url'] = request.path
                        print("activating voice command")
                        return jsonify({"task":"record","url":"/speech_start"})
                    if "scroll" in speech and "down" in speech:
                        print("scroll command")
                        return jsonify({"task":"scroll down"})
                    if "scroll" in speech and "up" in speech:
                        return jsonify({"task":"scroll up"})
                except:  
                    print("Sphinx could not understand audio")
                return jsonify({"task":False})  
                
            else:
                headers = {'authorization': 'Bearer ' + wit_access_token,
                           'Content-Type': 'audio/wav'}

                # making an HTTP post request
                resp = requests.post(API_ENDPOINT, headers = headers,
                                     data = audio)

                # converting response content to JSON format
                resp = json.loads(resp.content)
                print(resp)
            
                if 'intent' in resp['entities']:
                    if resp['entities']['intent'][0]['value']=="search recipes":
                        print('searching recipes')
                        recipes = get_all_recipes()
                        recipes_api = []
            
                        recipe_name = resp['entities']['local_search_query'][0]['value']
                    
                        response = requests.get("http://www.recipepuppy.com/api/?q="+recipe_name+"&p=1")
                        recipes_api = json.loads(response.content)['results']

                        recipes_cookcrew = []
                        for recipe in recipes:
                            words_present = 0
                            for word in recipe_name.split(' '):
                                if word.lower() in recipe.name.lower():
                                    words_present+=1
                            if words_present>0:
                                recipes_cookcrew.append((recipe,words_present))
                        print("sorting recipes")
                        recipes_cookcrew.sort(key = lambda x:x[0].name.lower())
                        recipes_cookcrew.sort(key=lambda x:-x[1])
                        recipes_cookcrew = recipes_cookcrew[:10]
                        recipes_cookcrew = [x[0] for x in recipes_cookcrew]
                        
                        #return render_template("recorder.html",message="recipe!")
                        return jsonify({"redirect":False,"stay":False, "template":render_template("recipes.html", recipes=recipes_cookcrew, ingredient_list = get_ingredients()['ing_list'],
                                               recipe_list=[recipe.name for recipe in get_all_recipes()],recipes_api=recipes_api)})
                    elif resp['entities']['intent'][0]['value']=="add recipe":
                        print("redirecting to add recipe")
                        return jsonify({"redirect":True,"stay":False, "url":"/add"})
                    elif resp['entities']['intent'][0]['value']=="shopping list":
                        date = datetime.datetime.now()
                        if 'datetime' in resp['entities']:
                            date = resp['entities']['datetime'][0]['value']
                            date = datetime.date(int(date[:4]),int(date[5:7]),int(date[8:10]))
                        num = date.weekday()
                        if num != 6:
                            date -= datetime.timedelta(days=(num+1)) #now it is the sunday
                        date = datetime.date(date.year,date.month,date.day)
                        return jsonify({"redirect":True,"stay":False, "url":'/shopper/'+str(date)})
                    elif resp['entities']['intent'][0]['value']=="search menus week":
                        date = datetime.datetime.now()
                        if 'datetime' in resp['entities']:
                            date = resp['entities']['datetime'][0]['value']
                            date = datetime.date(int(date[:4]),int(date[5:7]),int(date[8:10]))
                        num = date.weekday()
                        if num != 6:
                            date -= datetime.timedelta(days=(num+1)) #now it is the sunday
                        date = datetime.date(date.year,date.month,date.day)
                        return jsonify({"redirect":True,"stay":False, "url":'/week_menus/'+str(date)})
                    elif resp['entities']['intent'][0]['value']=="search menus":
                        date = datetime.datetime.now()
                        if 'datetime' in resp['entities']:
                            date = resp['entities']['datetime'][0]['value']
                            date = datetime.date(int(date[:4]),int(date[5:7]),int(date[8:10]))
                        date = datetime.date(date.year,date.month,date.day)
                        menus = get_menu_date(date,current_user.id) #because menu_date returns list (some days have multiple
                        if menus==[]:
                            return jsonify({"redirect":False,"stay":True, "message":"No menu for "+str(date)})
                        menu = menus[0]
                        return jsonify({"redirect":True,"stay":False, "url":'/menus/'+str(menu.id)})
                    elif resp['entities']['intent'][0]['value']=="ingredient check":
                        date = datetime.datetime.now()
                        if 'datetime' in resp['entities']:
                            date = resp['entities']['datetime'][0]['value']
                            date = datetime.date(int(date[:4]),int(date[5:7]),int(date[8:10]))
                        num = date.weekday()
                        if num != 6:
                            date -= datetime.timedelta(days=(num+1)) #now it is the sunday
                        date = datetime.date(date.year,date.month,date.day)
                        ing = resp['entities']['local_search_query'][0]['value']
                        days_using_ingredient = ingredient_check(ing,date)
                        
                        if days_using_ingredient[1]==[]:
                            output = "No day this week needs "+ing
                        else:
                            output = ing+":"
                            last_day = None
                            for day_tuple in days_using_ingredient[1]:
                                if last_day != day_tuple[0]:
                                    output += " "+day_tuple[0]+" needs "+str(day_tuple[1])+" "+day_tuple[2]+" of "+day_tuple[3]
                                else:
                                    output += " and "+str(day_tuple[1])+" "+day_tuple[2]+" of "+day_tuple[3] 
                                last_day = day_tuple[0]
                        print(output)
                        flash("output")
                        #if 'url' in session:
                        #    print("redirecting to",session['url'])
                        #    return redirect(session['url'])
                            
                        return jsonify({"redirect":False,"stay":True, "message":output})
                        
                    else:
                        return jsonify({"redirect":False,"stay":True, "message":resp})       
                else:
                    print("unclear intent")
                    return jsonify({"redirect":False,"stay":True, "message":"I couldn't understand "+resp["_text"]+", try again."})
        else:
            return jsonify({"redirect":False,"stay":True, "message":"Speech Recognition is down, sorry"})  
    else:      
        return render_template("recorder.html",message="",start_record=start_record)

@app.route('/postGroupMe', methods=['GET', 'POST'])
def group_me():
    if request.method == 'POST':
        if request.form["message"] and request.form["message"] != "NO-POST":
            post_to_DH(request.form["message"])
            #then return json of messages 
    return read_DH(5)
    

@app.route('/addSpotify', methods=['GET', 'POST'])
def addSpotify():
    if request.method == 'POST':
        add_spotify(current_user.id,request.form['name'],request.form['link'])
        next_page = session["current_menu_url"] #request.form.get('next')
        print("NEXT PAGE:",next_page)
        if not next_page:
            next_page = "/"
        return redirect(next_page)

app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    date = datetime.datetime.now()
    date = datetime.date(date.year,date.month,date.day)
    next_week = date + datetime.timedelta(days=(7))
    if request.method == 'POST':
        print(request.form)
        if "previous" in request.form:
            date -= datetime.timedelta(days=(7))
            print("DATE",date)
            return redirect('/week_menus/'+str(date))
        elif "next" in request.form:
            date += datetime.timedelta(days=(7))
            return redirect('/week_menus/'+str(date))
        elif "this" in request.form:
            return redirect('/week_menus/'+str(date))
        else:  #Swap post!
            cook_1 = request.form['cook_1']
            meal_1 = request.form['meal_1']
            date_1 = request.form['date_1']
            cook_2 = request.form['cook_2']
            meal_2 = request.form['meal_2']
            date_2 = request.form['date_2']
            menu_1 = get_menu_date(date_1,current_user.id)
            menu_2 = get_menu_date(date_2,current_user.id)
            if cook_1 in menu_1.cook_list and cook_2 in menu2.cook_list:
                swap_cooks(menu_1,cook_1,menu_2,cook_2)
                flash("Cooks have been swapped!")
            else:
                flash("One or more cooks are not scheduled for those days.")
    if current_user.is_authenticated:
        menus = get_menu_date(date,current_user.id)
        next_menus = get_menu_date(next_week,current_user.id)
        cook_list = []
        for day_name in current_user.general_schedule:
            cook_list += current_user.general_schedule[day_name]
    else:
        menus = []
        next_menus = []
        cook_list = []
    
    
    return render_template("schedule.html", this_menus=menus, next_menus=next_menus, cook_list=cook_list)

if __name__ == '__main__':
    #port = int(os.environ.get("PORT", 5000))
    #app.run(host='0.0.0.0', port=port)
    app.run(debug = True)

