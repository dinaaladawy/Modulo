# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 20:11:47 2017

@author: Andrei
"""

import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = "JungeAkademie.settings"
django.setup()
from modulo.models import Category, Interest, Module

def cleanupString(s):
    #– -> -
    #„“ -> ""
    s = s.replace("–", "-")
    s = s.replace("„", "\"")
    s = s.replace("“", "\"")
    return s
	
def cleanupModules():
    counter = 0
    for m in Module.objects.all():
        old = m.title
        m.title = cleanupString(old)
        if m.title != old:
            m.save()
            counter += 1
    print("Cleaned-up %s modules." % counter)
        
def cleanupInterests():
    counter = 0
    for i in Interest.objects.all():
        old = i.name
        i.name = cleanupString(old)
        if i.name != old:
            i.save()
            counter += 1
    print("Cleaned-up %s interests." % counter)
        
def cleanupCategories():
    counter = 0
    for c in Category.objects.all():
        old = c.name
        c.name = cleanupString(old)
        if c.name != old:
            c.save()
            counter += 1
    print("Cleaned-up %s categories." % counter)
        
cleanupModules()
cleanupInterests()
cleanupCategories()
#m = Module.objects.get(title__icontains='Weizsäcker')
#print(m)