# Create your views here.

#from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .views_documentation import initialize as doc_init
from .views_recommendation import initialize as rec_init

def index(request):
    return render(request, 'modulo/index.html', {})
    #return HttpResponse("Hello, world. You're at the \"Modulo\" homepage.")

def initialize():
    doc_init()
    rec_init()
    print("views initialized")