# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from .models import Exam, Location, CourseFormat, Language, Interest, Category, Module
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
import numpy as np

#matrix must be a numpy 2d array (matrix..)
def normalizeProbabilitiesCol(matrix):
    if (np.abs(np.sum(matrix, axis=0) - np.ones((matrix.shape[1], ))) >= 1e-9).any():
        #use softmax-type normalization
        matrix = np.divide(np.exp(matrix), np.sum(np.exp(matrix), axis=0))
    
    #assert that column sum is 1
    assert((np.abs(np.sum(matrix, axis=0) - np.ones((matrix.shape[1],))) < 1e-9).all())
    return matrix

class Recommender():    
    # weight matrix in [0; 1]^(nrCategories x nrInterests)
    # W[i, j] = the probability of mapping interest j to category i
    # the column sum must always be equal to 1 !!!
    W = np.zeros((1, 1))
    
    def __init__(self, timeInterval=('00:00', '23:59'), location=[Location.NOT_SPECIFIED], examType=[Exam.NOT_SPECIFIED], credits=(0, float('inf')), interests=[]):
        #filters: {interests, time, location, credits, exam type, ...}
        self.timeInterval = timeInterval #tuple with range of starting time of course
        self.location = location #list of locations
        self.examType = examType #list of acceptable exam types
        self.credits = credits #tuple with range of acceptable credits
        self.interests = interests #list of id's of interests from models.Interests
    
    #this algorithm uses a weight matrix W to map the interests to categories
    #returns a sorted list of categories based on the interests of the student
    def __algorithm1(self):
        # multiply the matrix W with the {0, 1}-vector of interests selected by the student
        categories = list(Category.objects.all())
        nrInter = Interest.objects.count()
        
        # 1) check if all interests are in the interests database
        #    if there is an interest not in the database, 
        #    add it to db and increase the dimension of the weight matrix
        # 2) create boolean vector of positions of interests
        if not self.interests: #list is empty
            x = np.ones((nrInter, 1))
        else:
            x = np.zeros((nrInter, 1))
            interests = list(Interest.objects.values_list('name', flat=True).order_by('id'))
            for i in self.interests:
                if not i in interests:
                    print("Interest %s not found in database!" % i)
                    '''
                    #interest not in database, add it...
                    Interest.objects.create(name=i)            
                    x = np.append(x, [[1]], axis=0)
                    '''
                else:
                    x[interests.index(i)] = 1
                
        res = np.dot(Recommender.W, x)
        sortedIndices = sorted(range(len(categories)), key=lambda k: res[k])
        categories[:] = [categories[i] for i in sortedIndices]
        return categories
    
    #apply learning algorithm to map the selected interests to categories
    #returns sorted list of categories according to the user interests
    def __getCategoriesFromInterests(self):
        return self.__algorithm1()
    
    #apply the rest of filters (time, place, exam, etc.) on the modules
    #return list of modules matching all filters...
    def __filterModules(self):
        #TODO!!!
        modules = Module.objects.filter()
        return modules
    
    #sort the selected/filtered modules according to relevance
    #return sorted list of modules
    def __sortModules(self, modules):
        #TODO!!!
        return modules
    
    def initialize():
        #print("Initializing the weight matrix of the recommender system!")
        #get the number of categories in the database
        nrCateg = Category.objects.all().count()
        #print("Number of categories = ", nrCateg, sep='')
        
        #get the number of interests in the database
        nrInter = Interest.objects.all().count()
        #print("Number of interests = ", nrInter, sep='')
        
        W = np.random.normal(loc=0.0, scale=1.0, size=(nrCateg, nrInter))
        #normalize the data: column sum must be 1!!!
        W = normalizeProbabilitiesCol(W)
        Recommender.W = W
        
        #print("Recommender.W = ", Recommender.W, sep='')
    
    def updateFilters(self, timeInterval=None, location=None, examType=None, credits=None, interests=None):
        if not timeInterval is None:
            self.timeInterval = timeInterval
        if not location is None:
            self.location = location
        if not examType is None:
            self.examType = examType
        if not credits is None:
            self.credits = credits
        if not interests is None:
            self.interests = interests
    
    def recommend(self):
        # map the interests to the module categories (learning algorithm 1)
        self.categories = self.__getCategoriesFromInterests()
        
        # apply the filters on the list of modules (use objects.filter(...))
        modules = self.__filterModules()
        
        # sort the remaining modules (according to what???: learning algorithm 2?)
        self.modules = self.__sortModules(modules)
        
        return self.modules
    
    def incorporateFeedback(self, selected_modules):
        #TODO!!!
        pass
    
    def save(self):
        #TODO!!!
        #what do save? what are relevant information needed to retrain the system?
        #filters, myRecomandation, userFeedback
        pass

@receiver(pre_save, sender=Category)
def insertCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']
    #if category is already in database, an update was performed and no action necessary
    if category in Category.objects.all():
        return
    #if category isn't in database, an insert was performed and add line! to weight matrix
    #+normalize probabilities
    # TODO!!!
    pass

@receiver(pre_delete, sender=Category)
def deleteCategorySignalHandler(sender, **kwargs):
    category = kwargs['instance']
    #get the index of the category in the category list
    #and delete the index'th row from Recommender.W
    categories = list(Category.objects.values_list('name', flat=True).order_by('id'))
    index = categories.index(category)
    np.delete(Recommender.W, index, axis=0) #delete from rows
    #+ update weights so that the columns sum up to 1
    Recommender.W = normalizeProbabilitiesCol(Recommender.W)

@receiver(pre_save, sender=Interest)
def insertInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    #if interest is already in database, an update was performed and no action necessary
    if interest in Interest.objects.all():
        return
    #if interest isn't in database, an insert was performed and add column! to weight matrix
    #append the interest on axis=1 of Recommender.W
    col = np.random.normal(size=(Category.objects.count(), 1))
    Recommender.W = np.append(Recommender.W, np.divide(np.exp(col), np.sum(np.exp(col), axis=0)), axis=1)

@receiver(pre_delete, sender=Interest)
def deleteInterestSignalHandler(sender, **kwargs):
    interest = kwargs['instance']
    #get the index of the interest in the interest list
    #and delete the index'th column from Recommender.W
    interests = list(Interest.objects.values_list('name', flat=True).order_by('id'))
    index = interests.index(interest)
    Recommender.W = np.delete(Recommender.W, index, axis=1) #delete from columns