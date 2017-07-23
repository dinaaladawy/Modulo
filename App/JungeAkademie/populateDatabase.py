# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = "JungeAkademie.settings"
django.setup()
from databaseHelpers.insertModules import insertModules
from databaseHelpers.insertInterests import insertInterests
from databaseHelpers.insertCategories import insertCategories
# from databaseHelpers.insertTestPersons import insertTestPersons
from databaseHelpers.insertExams import insertExams
from databaseHelpers.insertLanguages import insertLanguages
from databaseHelpers.insertLocations import insertLocations
from databaseHelpers.insertCourseFormats import insertCourseFormats
from databaseHelpers.insertPersonalities import insertPersonalities

databaseFile = './database.xlsx'

def populateDatabase():
    insertExams(databaseFile)
    insertLanguages(databaseFile)
    insertLocations(databaseFile)
    insertCourseFormats(databaseFile)
    insertPersonalities(databaseFile)
    
    insertInterests(databaseFile)
    insertCategories(databaseFile)
    # insertTestPersons(databaseFile)
    insertModules(databaseFile) #MUST BE LAST THING TO BE UPDATED
             
if __name__ == '__main__':
    populateDatabase()
    input("Press ENTER to exit program...")