# Create your views here.

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Category, Interest, Module

def index(request):
    return HttpResponse("Hello, world. You're at the \"Modulo\" homepage.")

def recommend(request):
    return HttpResponse("Hi, we are currently developing this webpage. Please visit the page later to use the recommender system...")

def documentation(request):
    return HttpResponse("Hi, we are currently developing this webpage. Please visit the page later to check out the documentation...")

def module(request, module_title):
    module = get_object_or_404(Module, title=module_title)
    return render(request, 'modulo/doc_object.html', {'class': 'Module', 'documentation_object': module, 'documentation_attributes': []})

def module_index(request):
    #get and show the list of all modules
    #with link to each module for more details
    module_names = [m.title for m in Module.objects.all()]
    return render(request, 'modulo/doc_list.html', {'class': 'Module', 'class_objects': module_names})

def category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    return render(request, 'modulo/doc_object.html', {'class': 'Category', 'documentation_object': category, 'documentation_attributes': []})

def category_index(request):
    #get and show the list of all categories
    #with link to each category for more details
    category_names = [c.name for c in Category.objects.all()]
    return render(request, 'modulo/doc_list.html', {'class': 'Category', 'class_objects': category_names})

def interest(request, interest_name):
    interest = get_object_or_404(Interest, name=interest_name)
    return render(request, 'modulo/doc_object.html', {'class': 'Interest', 'documentation_object': interest, 'documentation_attributes': []})

def interest_index(request):
    #get and show the list of all interests
    #with link to each interest for more details
    interest_names = [i.name for i in Interest.objects.all()]
    return render(request, 'modulo/doc_list.html', {'class': 'Interest', 'class_objects': interest_names})