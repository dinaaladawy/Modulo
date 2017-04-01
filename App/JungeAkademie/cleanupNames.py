# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 20:11:47 2017

@author: Andrei
"""

import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = "JungeAkademie.settings"
django.setup()
from modulo.models import Exam, Location, CourseFormat, Language, Personality, Category, Interest, Module, TestPerson
from openpyxl import load_workbook

def cleanupString(s):
    #– -> -
    #„“ -> ""
    try:
        s = s.replace("–", "-")
        s = s.replace("„", "\"")
        s = s.replace("“", "\"")
        s = s.replace("”", "\"")
        s = s.replace("’", "'")
    except AttributeError:
        #print(s, "is not a string.")
        pass
    return s

def cleanupExcel():
    excelFile = "./database.xlsx"
    worksheetNames = ["interests", "categories", "modules", "exams", "languages", "courseFormats", "locations", "personalities"]
	workbook = load_workbook(excelFile)
	counter = 0
    for name in worksheetNames:
        worksheet = workbook[name]
        nrRows = len(tuple(worksheet.rows))
        nrCols = len(tuple(worksheet.columns))
        for row in worksheet.iter_rows(min_row=1, min_col=1, max_row=nrRows, max_col=nrCols):
            for cell in row:
                cleanup = cleanupString(cell.value)
                if cell.value != cleanup:
                    print("Cleaned-up string:", cleanup, "\ncell.value: ", cell.value, "\n", sep='\n')
                    cell.value = cleanup
                    counter += 1
        print("Cleaned-up %s entries in \'%s\' worksheet of the %s file" % (counter, name, excelFile))
	if counter > 0:
		workbook.save(filename=excelFile)
	
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
        
cleanupExcel()
cleanupModules()
cleanupInterests()
cleanupCategories()
input("Press ENTER to exit programm...")