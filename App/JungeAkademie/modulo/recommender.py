# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from .algorithms import UpdateType, LinearClassifier
from .models import Interest, Category, Module
from django.db.models.signals import pre_save, pre_delete
from django.db import DatabaseError
from django.dispatch import receiver
import datetime, json, copy, threading

class HandleRecommender(json.JSONEncoder):
     """ json.JSONEncoder extension: handle Recommender """
     def default(self, obj):
         if isinstance(obj, Recommender):
             return Recommender.get_json_from_recommendation(obj)
         return json.JSONEncoder.default(self, obj)

class Recommender():
    savedRecommendationsFile = '../recommendations.txt'
    savedRecommendationsFileLock = None
    #name of all categories
    category_names = []
    #name of all interests
    interest_names = []
    #selected learning algorithm
    learning_algorithm = None
    
    def __init__(self, 
                 id=None, 
                 timeInterval=(datetime.datetime.strptime('00:00', '%H:%M').time(), datetime.datetime.strptime('23:59', '%H:%M').time()), 
                 credits=(0, float('inf')),
                 exam_types=[],
                 locations=[],
                 interests=[]):
        self.id = id
        self.filters = {'time': timeInterval,   #tuple with range of starting time of course
                        'credits': credits,     #tuple with range of acceptable credits
                        'exam': exam_types,     #list of acceptable exam types
                        'location': locations}  #list of locations
        
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
        '''
        print("Checking module", m.title)
        print("Filters:")
        for key, value in self.filters.items():
            print('\tkey = ', key, '; value = ', value, sep='')
        print('Module:')
        for key in self.filters.keys():
            if key != 'categories':
                print('\tkey = ', key, '; m.', key, ' = ', getattr(m, key), sep='')
            else:
                print('\tkey = ', key, '; m.', key, ' = [', sep='', end='')
                module_value = getattr(m, key)
                for c in module_value.all():
                    print(c.name, ', ', sep='', end='')
                print(']')
        #'''
        for key, value in self.filters.items():
            module_value = getattr(m, key)
            if key == 'time':
                if not (value[0] <= module_value <= value[1]):
                    #print("Module", m.title, "doesn't respect time filter!")
                    return False
            if key == 'credits':
                if module_value != 0.0 and not (value[0] <= module_value <= value[1]):
                    #print("Module", m.title, "doesn't respect credits filter!")
                    return False
            if key == 'exam':
                if module_value is not None and value != [] and module_value.exam_type not in value:
                    #print("Module", m.title, "doesn't respect exam filter!")
                    return False
            if key == 'location':
                if module_value is not None and value != [] and module_value.location not in value:
                    #print("Module", m.title, "doesn't respect location filter!")
                    return False
            if key == 'categories':
                module_category_in_selected_categories = False or (module_value.all().count() == 0)
                for c in module_value.all():
                    if c.name in value:
                        module_category_in_selected_categories = True
                        break
                if not module_category_in_selected_categories:
                    #print("Module", m.title, "doesn't respect categories filter!")
                    return False
        #print("Module", m.title, "respects the filters!")
        return True
    
    #apply the filters (categories_sorted, time, location, exam, etc.) on the modules
    #return list of modules (not just module titles...) matching all filters...
    def __filterModules(self):
        return [m for m in Module.objects.all() if self.__checkModule(m)]
        
    #sort the selected/filtered modules according to relevance
    #return sorted list of modules (not module titles, actual modules...)
    def __sortModules(self, modules):
        order = sorted(range(len(modules)), key=lambda i: (modules[i].selections, modules[i].title)) #sort according to choices?!?!?!
        return [modules[i] for i in order]
    
    def initialize():
        Recommender.savedRecommendationsFileLock = threading.Lock()
        #get the number of categories in the database
        try:
            categories = list(Category.objects.all())
        except DatabaseError:
            categories = []
        nrCateg = len(categories)
        #print("Number of categories = ", nrCateg, sep='')
        
        #get the number of interests in the database
        try:
            interests = list(Interest.objects.all())
        except DatabaseError:
            interests = []
        nrInter = len(interests)
        #print("Number of interests = ", nrInter, sep='')
        
        Recommender.category_names = [c.name for c in categories]
        #print("Recommender.category_names = ", Recommender.category_names, sep='')
        Recommender.interest_names = [i.name for i in interests]
        #print("Recommender.interest_names = ", Recommender.interest_names, sep='')
        
        Recommender.learning_algorithm = LinearClassifier
        Recommender.learning_algorithm.initialize(num_interests=nrInter, num_categories=nrCateg)
        
        print("Recommender initialized")
    
    def updateFilters(self, timeInterval=None, credits=None, exam_types=None, locations=None, categories=None, interests=None):
        if timeInterval is not None and timeInterval != self.filters['time']:
            self.filters['time'] = timeInterval
        if credits is not None and credits != self.filters['credits']:
            self.filters['credits'] = credits
        if exam_types is not None and exam_types != self.filters['exam']:
            self.filters['exam'] = exam_types
        if locations is not None and locations != self.filters['location']:
            self.filters['location'] = locations
        if categories is not None:
            if not 'categories' in self.filters.keys() or ('categories' in self.filters.keys() and categories != self.filters['categories']):
                self.filters['categories'] = categories
        if interests is not None and interests != self.interests:
            self.interests = interests
    
    def recommend(self):
        # map the interests to the module categories (learning algorithm)
        selected_categories, probabilities = self.__getCategoriesFromInterests()
        #print(selected_categories, probabilities, sep='\n')
        self.filters['categories'] = copy.deepcopy(selected_categories)
        
        # apply the filters on the list of modules (use objects.filter(...))
        modules = self.__filterModules()
        
        # current: sort according to relevance (number of selections of module)
        # self.modules = self.__sortModules(modules)
        return self.__sortModules(modules)
    
    def incorporateFeedback(self, modules_dict, save_recommendation=True):
        self.feedback = copy.deepcopy(modules_dict)
        self.algorithm.run_algorithm(train=True)
        if save_recommendation:
            self.save()
    
    def save(self):
        with Recommender.savedRecommendationsFileLock, open(Recommender.savedRecommendationsFile, "a") as file:
            rec_serialized = json.dumps(self, cls=HandleRecommender)
            file.write(rec_serialized + "\n")
        
    def get_json_from_recommendation(rec):
        filters = copy.deepcopy(rec.filters)
        format = '%H:%M'; timeInterval = filters['time']
        filters['time'] = (timeInterval[0].strftime(format), timeInterval[1].strftime(format))
        
        json_object = {}
        json_object['feedback'] = copy.deepcopy(getattr(rec, 'feedback', {}))
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
            if 'time' in filters:
                #2-tuple of datetime.time
                format = '%H:%M'
                timeInterval = (datetime.datetime.strptime(filters['time'][0], format).time(), datetime.datetime.strptime(filters['time'][1], format).time())
                r.updateFilters(timeInterval=timeInterval)
            if 'credits' in filters:
                #2-tuple of Integers; 
                #filters['credits'] is a list!!! -> convert it to tuple
                credit_tuple = (filters['credits'][0], filters['credits'][1])
                r.updateFilters(credits=credit_tuple)
            if 'exam' in filters:
                #list of strings or empty list
                if isinstance(filters['exam'], str): filters['exam'] = [filters['exam']]
                r.updateFilters(exam_types=filters['exam'])
            if 'location' in filters:
                #list of strings or empty list
                if isinstance(filters['location'], str): filters['location'] = [filters['location']]
                r.updateFilters(locations=filters['location'])
            if 'categories' in filters:
                #list of strings
                r.updateFilters(categories=filters['categories'])
        
        if 'interests' in cleanup_json_object:
            #list of strings
            r.updateFilters(interests=cleanup_json_object['interests'])
        
        if 'feedback' in cleanup_json_object:
            #(module titles) dictionary
            r.feedback = cleanup_json_object['feedback']
        
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
