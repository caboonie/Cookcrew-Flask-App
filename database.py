from models import *
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

#from app import login

engine = create_engine('sqlite:///cookcrew.db?check_same_thread=False')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
'''
engine2 = create_engine('sqlite:///menus.db?check_same_thread=False')
Base.metadata.create_all(engine2)
DBSession2 = sessionmaker(bind=engine2)
session2 = DBSession2()
'''

def create_recipe(name,servings,ingredients,recipe,category):
    #name = name.replace("'","")
    #name = name.replace("'","")
    recipe_object = session.query(Recipe).filter_by(name=name).first()
    if recipe_object == None:
        recipe_object = Recipe(name=name,servings=servings,ingredients=ingredients,recipe=recipe,category=category)
        session.add(recipe_object)
    else:
        recipe_object.servings = servings
        recipe_object.ingredients = ingredients
        recipe_object.recipe = recipe
        recipe_object.category = category
    session.commit()

def get_all_recipes():
    recipes = session.query(Recipe).all()
    return recipes

def get_recipe(id):
    recipe = session.query(Recipe).filter_by(id=id).first()
    return recipe

def get_recipe_name(name):
    recipe = session.query(Recipe).filter_by(name=name).first()
    return recipe

def edit_recipe(id,name=None,servings=None,ingredients=None,recipe=None,category=None):
    recipe_object = session.query(Recipe).filter_by(id=id).first()
    if recipe_object != None:
        if name != None:
            recipe_object.name = name
        if servings != None:
            recipe_object.servings = servings
        if ingredients != None:
            recipe_object.ingredients = ingredients
        if recipe != None:
            recipe_object.recipe = recipe
        if category != None:
            recipe_object.category = category 
        session.commit()


def clear_menu(sunday):
    menus = session.query(Menu).filter_by(sunday=sunday).delete()
    session.commit()

'''
sunday =  datetime.date(2018,12,16)
clear_menu(sunday)
print([menu.sunday for menu in session.query(Menu).all()])#.filter_by(sunday=sunday)])
'''

def create_menu(user_id,sunday,day,day_name,servings,dishes):
    menu = session.query(Menu).filter_by(day=day).filter_by(day_name=day_name).filter_by(user_id=user_id).first()
    #print("DATE:",day)
    #print("CURRENT MENU:",menu)
    cooks = load_user(user_id).general_schedule[day_name]
    if menu == None:
        menu_object = Menu(user_id=user_id,sunday=sunday,day=day,day_name=day_name,servings=servings,dishes=dishes,late_plates=[],cook_list=cooks)
        session.add(menu_object)
    else:
        #print("+++++++++++++++++++++++")
        #print("menu exists, updating")
        menu.servings = servings
        menu.dishes = dishes
    session.commit()

def get_all_menus(user_id):
    menus = session.query(Menu).filter_by(user_id=user_id).all()
    return menus

def get_menu(id):
    menus = session.query(Menu).filter_by(id=id).first()
    return menus

def get_menu_date(date,user_id):
    menus = session.query(Menu).filter_by(user_id=user_id).filter_by(day=date).all()
    return menus

def get_menus_week(date,user_id):
    menus = session.query(Menu).filter_by(user_id=user_id).filter_by(sunday=date).all()
    return menus

def add_late_plate(id,name):
    menu = session.query(Menu).filter_by(id=id).first()
    if name not in menu.late_plates:
        menu.late_plates = menu.late_plates+[name]
        print("UPDATED:",menu.late_plates)
        session.commit()

def edit_late_plate(id,names):
    menu = session.query(Menu).filter_by(id=id).first()
    menu.late_plates = names
    session.commit()
    



def create_ingredients():
    ing_object = Ingredients(ingredient_set=set(),measure_set=set())
    session.add(ing_object)
    session.commit()


def add_ingredient(ingredient):
    ing = session.query(Ingredients).all()[0]
    old_id = ing.id
    set_boi = ing.ingredient_set
    set_boi.add(ingredient)
    meas_set = ing.measure_set
    #print(set_boi)
    ing_object = Ingredients(ingredient_set=set_boi,measure_set=meas_set)
    session.add(ing_object)
    session.commit()
    session.query(Ingredients).filter_by(id=old_id).delete()
    session.commit()

def add_measure(measure):
    ing = session.query(Ingredients).all()[0]
    old_id = ing.id
    set_boi = ing.ingredient_set
    
    meas_set = ing.measure_set
    meas_set.add(measure)
    #print(set_boi)
    ing_object = Ingredients(ingredient_set=set_boi,measure_set=meas_set)
    session.add(ing_object)
    session.commit()
    session.query(Ingredients).filter_by(id=old_id).delete()
    session.commit()
    
def get_ingredients():
    try:
        ing_list = list(session.query(Ingredients).all()[0].ingredient_set)
        measure_list = list(session.query(Ingredients).all()[0].measure_set)
        return {"ing_list":ing_list,"meas_list":measure_list}
    except: #if for some reason ingredients is empty
        return {"ing_list":[],"meas_list":[]}


def create_user(username,password,schedule):
    password_hash = generate_password_hash(password)
    user = User(username=username, password_hash = password_hash,playlists = [],general_schedule=schedule)
    #user.set_password(password)
    session.add(user)
    session.commit()
    return user

def get_user_name(username):
    return session.query(User).filter_by(username=username).first()

def load_user(id):
    return session.query(User).get(int(id))

def add_spotify(user_id,name,link):
    user = session.query(User).get(int(user_id))
    user.playlists = user.playlists+[(name,link)]
    session.add(user)
    session.commit()

def swap_cooks(menu_1,cook_1,menu_2,cook_2):
    cook_list = menu_1.cook_list
    cook_list.replace(cook_1,cook_2)
    menu_1.cook_list = cook_list
    cook_list = menu_2.cook_list
    cook_list.replace(cook_2,cook_1)
    menu_2.cook_list = cook_list
    session.add(menu_2)
    session.add(menu_1)
    session.commit()

print([(a.username,a.playlists) for a in session.query(User).all()])


if get_recipe_name("Grapes Epic")==None:
    user = create_user('caleb','caleb',{"Sunday Brunch":['caleb','also caleb']})
    create_menu(user.id,datetime.date(1998, 8, 28),datetime.date(1998, 8, 28),"Sunday Brunch",24,["Grapes Epic"])
    create_ingredients()
    create_recipe("Grapes Epic",6,{"grapes":(1,"pound")},"Rinse and serve","Dessert")


#add_ingredient("grapes")
#session.query(Ingredients).delete()

#print(session.query(Ingredients).all())

#print(get_ingredients().ingredient_set)
