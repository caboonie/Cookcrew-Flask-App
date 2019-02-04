from sqlalchemy import Column, Integer, String, Boolean,PickleType, Date
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
#from app import login

Base = declarative_base()

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    servings = Column(Integer)
    ingredients = Column(PickleType)
    recipe = Column(String)
    category = Column(String)

class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    sunday = Column(Date)
    day = Column(Date)
    day_name = Column(String)
    servings = Column(Integer)
    dishes = Column(PickleType) #list of dishes for that day
    late_plates = Column(PickleType) #list of names for that day
    cook_list = Column(PickleType) #list of names for that day

class Ingredients(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True)
    ingredient_set = Column(PickleType)
    measure_set = Column(PickleType)

class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    password_hash = Column(PickleType)
    username = Column(String)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash,password)
    playlists = Column(PickleType)
    general_schedule = Column(PickleType) #dictionary of day_names to list of cooks

'''
class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    link = Column(String)
'''

#@login.user_loader
#def load_user(id):
#    return User.query.get(int(id))

