# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

#import django
from models import Exam, Location, Module, Category

class Recommender():
    
    def __init__(self, timeInterval=('00:00', '23:59'), location=[Location.EITHER], examType=[Exam.EITHER], credits=(0, float('inf')), interests=[]):
        #possible filters:
        #   - interests
        #   - time
        #   - location
        #   - credits
        #   - exam type
        self.timeInterval = timeInterval #tuple with range of starting time of course
        self.location = location #list of locations
        self.examType = Exam.EITHER #list of acceptable exam types
        self.credits = credits #tuple with range of acceptable credits
        self.interests = interests #list of id's of interests from models.Interests
    
    def updateFilters(self, timeInterval=None, location=None, examType=None, credits=None, interests=None):
        if timeInterval != None:
            self.timeInterval = timeInterval
        if location != None:
            self.location = location
        if examType != None:
            self.examType = examType
        if credits != None:
            self.credits = credits
        if interests != None:
            self.interests = interests
    
    def __getCategoriesFromInterests():
        categories = Category.objects.filter()
        return categories
    
    def __filterModules(self):
        modules = Module.objects.filter()
        return modules
    
    def __sortModules(self, modules):
        return modules
    
    def recommend(self):
        # map the interests to the module categories (learning algorithm...)
        self.categories = self.__getCategoriesFromInterests()
        
        # apply the filters on the list of modules (use objects.filter(...))
        modules = self.__filterModules()
        
        # sort the remaining modules (according to what???: learning algorithm)
        modules = self.__sortModules(modules)
        
        return modules