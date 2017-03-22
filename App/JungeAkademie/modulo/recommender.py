# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from .models import Exam, Location, Interest, Category, Module
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
import numpy as np
import tensorflow as tf
import datetime

#matrix must be a numpy 2d array (matrix..)
#accepted is also a 1d array...
def normalizeProbabilitiesCol(matrix):
    compare = 1.0
    if len(matrix.shape) > 1:
        #dealing with matrix
        compare = np.ones((matrix.shape[1],))
        
    if (np.abs(np.sum(matrix, axis=0) - compare) >= 1e-9).any():
        #use softmax-type normalization
        matrix = np.divide(np.exp(matrix), np.sum(np.exp(matrix), axis=0))
    
    #assert that column sum is 1
    assert((np.abs(np.sum(matrix, axis=0) - compare) < 1e-9).all())
    return matrix

class Recommender():
    #tensorflow session for training
    session = None
    #weights
    W = tf.Variable([], validate_shape=False)
    #biases
    b = tf.Variable([], validate_shape=False)
    #input vector
    x = tf.placeholder(tf.float32)
    #label vector
    y = tf.placeholder(tf.float32)
    #name of all categories
    category_names=[]
    #name of all interests
    interest_names=[]
    #learning rate
    alpha = 0.0
    #regularization rate
    beta = 0.0
    
    def __init__(self, timeInterval=(datetime.datetime.strptime('00:00', '%H:%M').time(), datetime.datetime.strptime('23:59', '%H:%M').time()), location=[Location.NOT_SPECIFIED], examType=[Exam.NOT_SPECIFIED], credits=(0, float('inf')), interests=[]):
        self.filters = {'time': timeInterval,  #tuple with range of starting time of course
                        'exam': examType,      #list of acceptable exam types
                        'place': location,     #list of locations
                        'credits': credits}     #tuple with range of acceptable credits
        self.interests = interests #list of id's of interests from models.Interests
            
    #this algorithm uses a linear classifier to map the interests to categories
    #returns a sorted list of category_names based on the interests of the student
    def __algorithm1(self):
        # multiply the matrix W with the {0, 1}-vector of interests selected by the student
        # "linear classifier" style: out = softmax(W*x+b)
        nrInter = len(self.interest_names) #Interest.objects.count()
        
        # 1) check if all interests are in the interests database
        #    if there is an interest not in the database, add it to db 
        #    (the increase in dimensions of the weight matrix is handled by the signal)
        # 2) create boolean vector of positions of interests
        if not self.interests: #if list is empty
            x = np.ones((1, nrInter))
        else:
            x = np.zeros((1, nrInter))
            for i in self.interests:
                if not i in Recommender.interest_names:
                    print("Interest %s not found in database!" % i)
                    inp = input("What to do?\nEnter \"add\" to add to database or press ENTER to skip interest... ")
                    if inp == "add":
                        #interest not in database, add it...
                        Interest.objects.create(name=i)
                        x = np.append(x, [[1]], axis=1)
                else:
                    x[0, Recommender.interest_names.index(i)] = 1

        #linear classifier: res = softmax(W*x+b); 
        self.input = x
        self.op = tf.nn.softmax(tf.add(tf.matmul(Recommender.x, Recommender.W), Recommender.b));
        #FIXME: problem with multithreadding; just one global session???
        output = Recommender.session.run(self.op, {Recommender.x: self.input}); output = output[0]
        
        sortedIndices = sorted(range(len(Recommender.category_names)), key=lambda k: output[k])
        return [Recommender.category_names[i] for i in sortedIndices], [output[i] for i in sortedIndices]
    
    #apply learning algorithm to map the selected interests to categories
    #returns sorted list of category_names according to the user interests
    def __getCategoriesFromInterests(self):
        categories_sorted, probs = self.__algorithm1()
        nrCategs = len(categories_sorted)
        threshhold = 0.1 if nrCategs > 100 else 0.2 if nrCategs > 50 else 0.5 if nrCategs > 20 else 1
        threshhold = int(threshhold*len(categories_sorted))
        return categories_sorted[:threshhold], probs[:threshhold]
    
    #checks if the module is in compliance with the filters
    def __checkModule(self, m):
        for key, value in self.filters.items():
            module_value = getattr(m, key)
            if key == 'time':
                if not (value[0] <= module_value <= value[1]):
                    return False
            if key == 'exam':
                if module_value != Exam.NOT_SPECIFIED and module_value not in value:
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
        
        #normalize the data: column sum must be 1!!! why??? -> linear classifier...
        #W = np.random.normal(loc=0.0, scale=1.0, size=(nrCateg, nrInter))
        #W = normalizeProbabilitiesCol(W)
        
        Recommender.W = tf.Variable(tf.random_normal([nrInter, nrCateg], mean=0, stddev=1), validate_shape=False) #weights
        Recommender.b = tf.Variable(tf.random_normal([nrCateg], mean=0, stddev=1), validate_shape=False) #biases
        #print("Recommender.W = ", Recommender.W, sep='')
        #print("Recommender.b = ", Recommender.b, sep='')
        Recommender.session = tf.Session()
        Recommender.session.run(tf.global_variables_initializer())
        
        Recommender.category_names = [c.name for c in categories]
        #print("Recommender.category_names = ", Recommender.category_names, sep='')
        Recommender.interest_names = [i.name for i in interests]
        #print("Recommender.interest_names = ", Recommender.interest_names, sep='')
        Recommender.alpha = 0.5
        #print("Recommender.alpha = ", Recommender.alpha, sep='')
        Recommender.beta = 0.01
        #print("Recommender.beta = ", Recommender.beta, sep='')
    
    def updateFilters(self, timeInterval=None, location=None, examType=None, credits=None, interests=None):
        if not timeInterval is None:
            self.filters['time'] = timeInterval
        if not location is None:
            self.filters['place'] = location
        if not examType is None:
            self.filters['exam'] = examType
        if not credits is None:
            self.filters['credits'] = credits
        if not interests is None:
            self.interests = interests
    
    def recommend(self):
        # map the interests to the module categories (learning algorithm 1)
        self.filters['categories'] = self.__getCategoriesFromInterests()
        
        # apply the filters on the list of modules (use objects.filter(...))
        modules = self.__filterModules()
        
        # sort the remaining modules (according to what???: learning algorithm 2?)
        # current: sort according to relevance (number of selections of module)
        # self.modules = self.__sortModules(modules)
        return self.__sortModules(modules)
    
    def incorporateFeedback(self, modules_dict):
        try:
            #list of selected module (-> selected by the student)
            selected_modules = [Module.objects.get(title=modules_dict['selected'])]
        except Module.DoesNotExist:
            #list of interesting modules (-> selected by the student)
            selected_modules = [Module.objects.get(title=t).val for t in modules_dict['interesting']]
        
        # get category names of the selected_modules and create "correct label" for this query
        #selected_categories = {c.name for m in selected_modules for c in m.categories.all()};
        selected_categories = [c.name for m in selected_modules for c in m.categories.all()];
        self.label = normalizeProbabilitiesCol(np.array([selected_categories.count(name) for name in Recommender.category_names]))
        
        #update the weights...
        op = tf.nn.softmax(tf.add(tf.matmul(self.x, Recommender.W), Recommender.b))
        loss = tf.reduce_sum(tf.square(op - self.y)) + Recommender.beta * tf.nn.l2_loss(Recommender.W) #add regularization
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=Recommender.alpha)
        train = optimizer.minimize(loss)        
        #print(Recommender.session.run([Recommender.W, Recommender.b]))
        #print("loss = ", Recommender.session.run(loss, {self.x: self.input, self.y: self.label}))
        Recommender.session.run(train, {Recommender.x: self.input, Recommender.y: self.label})        
    
    def save(self):
        #TODO!!!
        #what do save? what are relevant information needed to retrain the system?
        #filters, myRecomandation, userFeedback
        pass
    
    def getWeights():
        temp_W = tf.slice(Recommender.W, begin=[0, 0], size=tf.shape(Recommender.W))
        temp_b = tf.slice(Recommender.b, begin=[0], size=tf.shape(Recommender.b))
        value_W = Recommender.session.run(temp_W)
        value_b = Recommender.session.run(temp_b)
        return value_W, value_b


@receiver(pre_save, sender=Category)
def insertCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']
    
    #if category is already in database, an update was performed and no action necessary
    if category.name in Recommender.category_names:
        return
    
    #if category isn't in database, an insert was performed
    value_W, value_b = Recommender.getWeights()
    value_W = np.append(value_W, np.random.normal(size=[value_W.shape[0]]), axis=1) #add column to weight matrix
    value_b = np.append(value_b, np.random.normal(size=[1]), axis=0) #add row to bias
    Recommender.session.run(tf.assign(Recommender.W, value_W, validate_shape=False)) #reassign variable
    Recommender.session.run(tf.assign(Recommender.b, value_b, validate_shape=False)) #reassign variable
    Recommender.category_names.append(category.name)

@receiver(pre_delete, sender=Category)
def deleteCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']

    #get the index of the category in the category list
    #and delete the index'th column from weight and the index'th row from bias
    index = Recommender.category_names.index(category.name)
    value_W, value_b = Recommender.getWeights()
    value_W = np.delete(value_W, index, axis=1)
    value_b = np.delete(value_b, index, axis=0)
    Recommender.session.run(tf.assign(Recommender.W, value_W, validate_shape=False)) #reassign variable
    Recommender.session.run(tf.assign(Recommender.b, value_b, validate_shape=False)) #reassign variable
    Recommender.category_names.remove(category.name)

@receiver(pre_save, sender=Interest)
def insertInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    
    #if interest is already in database, an update was performed and no action necessary
    if interest.name in Recommender.interest_names:
        return
    
    #if interest isn't in database, an insert was performed
    value_W = Recommender.getWeights()
    value_W = np.append(value_W, np.random.normal(size=[value_W.shape[1]]), axis=0) #add row to weight matrix
    Recommender.session.run(tf.assign(Recommender.W, value_W, validate_shape=False)) #reassign variable
    Recommender.interest_names.append(interest.name)

@receiver(pre_delete, sender=Interest)
def deleteInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    
    #get the index of the interest in the interest list
    #and delete the index'th row from weight
    index = Recommender.interest_names.index(interest.name)
    value_W = Recommender.getWeights()
    value_W = np.delete(value_W, index, axis=0)
    Recommender.session.run(tf.assign(Recommender.W, value_W, validate_shape=False)) #reassign variable
    Recommender.interest_names.remove(interest.name)
