# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from .algorithms import UpdateType, LinearClassifier
from .models import Exam, Location, Interest, Category, Module
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
import datetime, json, copy

class HandleRecommender(json.JSONEncoder):
     """ json.JSONEncoder extension: handle Recommender """
     def default(self, obj):
         if isinstance(obj, Recommender):
             return Recommender.get_json_from_recommendation(obj)
         return json.JSONEncoder.default(self, obj)

class Recommender():
    savedRecommendationsFile = '../recommendations.txt'
    #name of all categories
    category_names=[]
    #name of all interests
    interest_names=[]
    #selected learning algorithm
    learning_algorithm=None
    
    def __init__(self, 
                 id=None, 
                 timeInterval=(datetime.datetime.strptime('00:00', '%H:%M').time(), datetime.datetime.strptime('23:59', '%H:%M').time()), 
                 location=[Location.NOT_SPECIFIED], 
                 examType=[Exam.NOT_SPECIFIED], 
                 credits=(0, float('inf')), 
                 interests=[]):
        self.id = id
        self.filters = {'time': timeInterval,   #tuple with range of starting time of course
                        'exam': examType,       #list of acceptable exam types
                        'place': location,      #list of locations
                        'credits': credits}     #tuple with range of acceptable credits
        
        self.interests = interests #list of id's of interests from models.Interests
        #handle interests that are not in the database
        for i in self.interests[:]:
            if not i in Recommender.interest_names:
                print("Interest %s not found in database!" % i)
                inp = input("What to do?\nEnter \"add\" to add to database or press ENTER to skip interest... ")
                if inp == "add":
                    #interest not in database, add it...
                    Interest.objects.create(name=i)
                else:
                    #if not added in the database, remove it from list
                    self.interests.remove(i)
        
        self.algorithm = Recommender.learning_algorithm(self)
    
    #apply learning algorithm to map the selected interests to categories
    #returns sorted list of category_names according to the user interests
    def __getCategoriesFromInterests(self):
        res = self.algorithm.run_algorithm(eval=True)
        probs = res['eval'][0]
        sortedIndices = sorted(range(len(Recommender.category_names)), key=lambda k: probs[k], reverse=True)
        categories_sorted = [Recommender.category_names[i] for i in sortedIndices]
        probs[:] = [probs[i] for i in sortedIndices]
        
        nrCategs = len(categories_sorted)
        threshold = 0.1 if nrCategs > 100 else 0.2 if nrCategs > 50 else 0.5 if nrCategs > 20 else 1
        threshold = int(threshold*len(categories_sorted))
        return categories_sorted[:threshold], probs[:threshold]
    
    #checks if the module is in compliance with the filters
    def __checkModule(self, m):
        for key, value in self.filters.items():
            module_value = getattr(m, key)
            if key == 'time':
                if not (value[0] <= module_value <= value[1]):
                    return False
            if key == 'exam':
                if module_value != Exam.NOT_SPECIFIED and module_value != value:
                    return False
            if key == 'place':
                if module_value != Location.NOT_SPECIFIED and module_value not in value:
                    return False
            if key == 'credits':
                if module_value != 0.0 and not (value[0] <= module_value <= value[1]):
                    return False
            if key == 'categories':
                module_category_in_selected_categories = False or (module_value.all().count() == 0)
                for c in module_value.all():
                    if c.name in value:
                        module_category_in_selected_categories = True
                        break
                if not module_category_in_selected_categories:
                    return False
        return True
    
    #apply the filters (categories_sorted, time, place, exam, etc.) on the modules
    #return list of modules (not just module titles...) matching all filters...
    def __filterModules(self):
        return [m for m in Module.objects.all() if self.__checkModule(m)]
        
    #sort the selected/filtered modules according to relevance
    #return sorted list of modules (not module titles, actual modules...)
    def __sortModules(self, modules):
        order = sorted(range(len(modules)), key=lambda i: (modules[i].selections, modules[i].title)) #sort according to choices?!?!?!
        return [modules[i] for i in order]
    
    def initialize():
        #print("Initializing the weight matrix of the recommender system!")
        #get the number of categories in the database
        categories = list(Category.objects.all())
        nrCateg = len(categories)
        #print("Number of categories = ", nrCateg, sep='')
        
        #get the number of interests in the database
        interests = list(Interest.objects.all())
        nrInter = len(interests)
        #print("Number of interests = ", nrInter, sep='')
        
        Recommender.category_names = [c.name for c in categories]
        #print("Recommender.category_names = ", Recommender.category_names, sep='')
        Recommender.interest_names = [i.name for i in interests]
        #print("Recommender.interest_names = ", Recommender.interest_names, sep='')
        
        Recommender.learning_algorithm = LinearClassifier
        Recommender.learning_algorithm.initialize(num_interests=nrInter, num_categories=nrCateg)
        
        print("Recommender initialized")
    
    def updateFilters(self, timeInterval=None, location=None, examType=None, credits=None, categories=None, interests=None):
        if timeInterval is not None:
            self.filters['time'] = timeInterval
        if location is not None:
            self.filters['place'] = location
        if examType is not None:
            self.filters['exam'] = examType
        if credits is not None:
            self.filters['credits'] = credits
        if categories is not None:
            self.filters['categories'] = categories
        if interests is not None:
            self.interests = interests
    
    def recommend(self):
        # map the interests to the module categories (learning algorithm 1)
        selected_categories, probabilities = self.__getCategoriesFromInterests()
        #print(selected_categories, probabilities, sep='\n')
        self.filters['categories'] = copy.deepcopy(selected_categories)
        
        # apply the filters on the list of modules (use objects.filter(...))
        modules = self.__filterModules()
        
        # TODO: sort the remaining modules (according to what???: learning algorithm 2?)
        # current: sort according to relevance (number of selections of module)
        # self.modules = self.__sortModules(modules)
        return self.__sortModules(modules)
    
    def incorporateFeedback(self, modules_dict):
        self.feedback = copy.deepcopy(modules_dict)
        self.algorithm.run_algorithm(train=True)
        self.save()
    
    def save(self):
        with open(Recommender.savedRecommendationsFile, "a") as file:
            rec_serialized = json.dumps(self, cls=HandleRecommender)
            file.write(rec_serialized + "\n")
        
    def get_json_from_recommendation(rec):
        filters = copy.deepcopy(rec.filters)
        format = '%H:%M'; timeInterval = filters['time']
        filters['time'] = (timeInterval[0].strftime(format), timeInterval[1].strftime(format))
        
        feedback = copy.deepcopy(getattr(rec, 'feedback', {}))
        for key, value in feedback.items():
            #save the id of the modules
            if isinstance(value, str):
                feedback[key] = value 
            elif isinstance(value, list):
                feedback[key] = [m for m in value]
            elif value is None:
                    feedback[key] = value
            else:
                raise Exception("Cannot create json object for (key, value) pair: (", repr(key), ", ", repr(value), ")")
        
        json_object = {}
        json_object['feedback'] = feedback
        json_object['filters'] = filters
        json_object['id'] = rec.id
        json_object['interests'] = copy.deepcopy(rec.interests)
        return json_object
    
    def get_recommendation_from_json(json_object):
        #print("JSON Object is", json_object)
        cleanup_json_object = json.loads(json_object)
        r = Recommender()
        if 'id' in cleanup_json_object:
            #Integer
            r.id = cleanup_json_object['id']
        if 'filters' in cleanup_json_object:
            filters = cleanup_json_object['filters']
            if 'exam' in filters:
                #Integer
                r.updateFilters(examType=filters['exam'])
            if 'time' in filters:
                #Tuple of datetime.time
                format = '%H:%M'
                timeInterval = (datetime.datetime.strptime(filters['time'][0], format).time(), datetime.datetime.strptime(filters['time'][1], format).time())
                r.updateFilters(timeInterval=timeInterval)
            if 'place' in filters:
                #Integer
                r.updateFilters(location=filters['place'])
            if 'credits' in filters:
                #tuple of Integers
                credit_tuple = (filters['credits'][0], filters['credits'][1])
                r.updateFilters(credits=credit_tuple)
            if 'categories' in filters:
                #list of strings
                r.updateFilters(categories=filters['categories'])
        if 'interests' in cleanup_json_object:
            #list of strings
            r.updateFilters(interests=cleanup_json_object['interests'])
        if 'feedback' in cleanup_json_object:
            #(module id) dictionary
            feedback = cleanup_json_object['feedback']
            for key, value in feedback.items():
                #save the id of the modules
                if isinstance(value, str):
                    feedback[key] = Module.objects.get(title=value)
                elif isinstance(value, list):
                    feedback[key] = [Module.objects.get(title=i) for i in value]
                elif value is None:
                    feedback[key] = value
                else:
                    raise Exception("Cannot re-create recommendation object for (key, value) pair: (", repr(key), ", ", repr(value), ")")
            r.feedback = feedback
            
        return r
    

@receiver(pre_save, sender=Category)
def insertCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']
    
    #if category is already in database, an update was performed and no action necessary
    if category.name in Recommender.category_names:
        return
    
    #if category isn't in database, an insert was performed
    Recommender.learning_algorithm.updateWeights(UpdateType.INSERT_CATEGORY)
    Recommender.category_names.append(category.name)

@receiver(pre_delete, sender=Category)
def deleteCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']

    #get the index of the category in the category list
    #and delete the index'th column from weight and the index'th row from bias
    index = Recommender.category_names.index(category.name)
    Recommender.learning_algorithm.updateWeights(UpdateType.DELETE_CATEGORY, index)
    Recommender.category_names.remove(category.name)

@receiver(pre_save, sender=Interest)
def insertInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    
    #if interest is already in database, an update was performed and no action necessary
    if interest.name in Recommender.interest_names:
        return
    
    #if interest isn't in database, an insert was performed
    Recommender.learning_algorithm.updateWeights(UpdateType.INSERT_INTEREST)
    Recommender.interest_names.append(interest.name)

@receiver(pre_delete, sender=Interest)
def deleteInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    
    #get the index of the interest in the interest list
    #and delete the index'th row from weight
    index = Recommender.interest_names.index(interest.name)
    Recommender.learning_algorithm.updateWeights(UpdateType.DELETE_INTEREST, index)
    Recommender.interest_names.remove(interest.name)
