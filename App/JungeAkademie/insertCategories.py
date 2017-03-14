# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = "JungeAkademie.settings"
django.setup()
from modulo.models import Category

categoryFile = "./categories.txt"

def insertCategories():
    #test = Category(name='TestCategory')
    #c = Category(name='Ausgrenzung')
    with open(categoryFile, 'r') as f:
        for line in f:
            line = line.replace("\n", "")
            c, add = Category.objects.get_or_create(name=line)
            print(line, add, sep=' ', end='\n')
        f.close()
    #input()

insertCategories()