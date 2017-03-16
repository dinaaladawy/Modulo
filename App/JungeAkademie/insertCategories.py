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
    with open(categoryFile, 'r') as f:
        add = 0
        for line in f:
            line = line.replace("\n", "")
            c, added = Category.objects.get_or_create(name=line)
            add += 1 if added else 0
            #print(line, added, sep=' ', end='\n')
        f.close()
    print("Number of added categories =", add)
    print('Number of categories in database =', len(Category.objects.all()))

insertCategories()
input("Press ENTER to exit program...")