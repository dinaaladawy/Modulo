# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 15:21:01 2017

@author: Andrei
"""

import os

#delete database
try:
    #os.remove('./db_copy.sqlite3')
    os.remove('./db_copy.sqlite3')
except FileNotFoundError:
    pass

#populate database
import populateDatabase
populateDatabase.populateDatabase()

#train the system
from modulo.training import Training
t = Training()
t.train()

#start the server
os.system("python manage.py runserver")