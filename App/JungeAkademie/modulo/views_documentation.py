# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 11:14:23 2017

@author: Andrei
"""

#from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render#, reverse
from .models import Category, Interest, Module

def documentation(request):
    return render(request, 'modulo/documentation_index.html', {})
    #return HttpResponse("Hi, we are currently developing this webpage. Please visit the page later to check out the documentation...")

def module(request, module_title):
    module = get_object_or_404(Module, title=module_title)
    return render(request, 'modulo/documentation_object.html', {'class': 'Module', 'documentation_object': module, 'documentation_attributes': []})

def module_index(request):
    #get and show the list of all modules
    #with link to each module for more details
    module_titles = [m.title for m in Module.objects.all()]
    return render(request, 'modulo/documentation_list.html', {'class': 'Module', 'class_objects': module_titles})

def category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    return render(request, 'modulo/documentation_object.html', {'class': 'Category', 'documentation_object': category, 'documentation_attributes': []})

def category_index(request):
    #get and show the list of all categories
    #with link to each category for more details
    category_names = [c.name for c in Category.objects.all()]
    return render(request, 'modulo/documentation_list.html', {'class': 'Category', 'class_objects': category_names})

def interest(request, interest_name):
    interest = get_object_or_404(Interest, name=interest_name)
    return render(request, 'modulo/documentation_object.html', {'class': 'Interest', 'documentation_object': interest, 'documentation_attributes': []})

def interest_index(request):
    #get and show the list of all interests
    #with link to each interest for more details
    interest_names = [i.name for i in Interest.objects.all()]
    return render(request, 'modulo/documentation_list.html', {'class': 'Interest', 'class_objects': interest_names})

def initialize():
    print("views_documentation initialized")