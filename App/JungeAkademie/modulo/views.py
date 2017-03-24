# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse
from .models import Exam, Location, Category, Interest, Module
from .recommender import Recommender, HandleRecommender
from .feedback import Feedback
from .forms import RecommenderForm, ModuleForm
import datetime

activeRecommendationList = []

def index(request):
    return HttpResponse("Hello, world. You're at the \"Modulo\" homepage.")

def recommender_thanks(request):
    return render(request, 'modulo/recommender_thanks.html', {})

def recommendation(request, recommendation_id='0'):
    #search the activeRecommendationList for the recommendation with the parameter id
    global activeRecommendationList
    print(repr(activeRecommendationList))
    
    recommendation = None
    recommendation_id = int(recommendation_id)
    for r in activeRecommendationList[:]:
        print("Checking recommendation r.id = ", r.id, " versus parameter id = ", recommendation_id, sep='')
        if r.id == recommendation_id:
            print("Found match!", sep='')
            recommendation = r
            activeRecommendationList.remove(r)
            
    if recommendation is None:
        request_string = (request.META['SERVER_NAME']+":"+request.META['SERVER_PORT']+request.path)
        return render(request, 'modulo/recommender_error.html', {'error_msg': "No recommendation available with id %d at request %s" % (recommendation_id, request_string)})
        #return render(request, x, {'error_message': ("No recommendation available with id %d at request %s" % (recommendation_id, request_string))})
    
    if request.method == 'POST':            
        f = Feedback(recommendation=recommendation); 
        f.setFeedback()
        return HttpResponseRedirect(reverse('modulo:modulo-recommender-thanks'))
    
    elif request.method == 'GET':
        modules = recommendation.recommend()
        print(modules)
            
        return render(request, 'modulo/doc_list.html', {'class': 'Recommendation', 'class_objects': modules})
    else:
        return HttpResponse("Unknown method for request %s" % request)

def recommend(request):
    print("This request", request, "was called using the", request.method, "method")
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ModuleForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            global activeRecommendationList, id_counter
            
            # process the data in form.cleaned_data as required
            place = form.cleaned_data['place']
            time = form.cleaned_data['time']
            exam = form.cleaned_data['exam']
            credits = form.cleaned_data['credits']
            interests = form.cleaned_data['interests']
            
            if time is None:
                timeMin = datetime.datetime.strptime('00:00', '%H:%M').time()
                timeMax = datetime.datetime.strptime('23:59', '%H:%M').time()
            else:
                timeMin = time
                timeMax = time
            
            if credits is None:
                creditsMin = 0
                creditsMax = float('inf')
            else:
                creditsMin = credits
                creditsMax = credits
                
            if exam is None:
                exam = Exam.NOT_SPECIFIED
                
            if place is None:
                place = Location.NOT_SPECIFIED
                
            if interests is None:
                interests = []
            
            r = Recommender(id=id_counter, location=place, timeInterval=(timeMin, timeMax), examType=exam, credits=(creditsMin, creditsMax), interests=interests)
            
            activeRecommendationList.append(r)
            id_counter += 1
            
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('modulo:modulo-recommendation', args=[r.id]))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ModuleForm()

    #return HttpResponse("Hi, we are currently developing this webpage. Please visit the page later to use the recommender system...")
    return render(request, 'modulo/recommender_filterSelection.html', {'form': form})

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

def initialize():
    global activeRecommendationList, id_counter
    activeRecommendationList = []
    id_counter = 0
    print("views initialized")