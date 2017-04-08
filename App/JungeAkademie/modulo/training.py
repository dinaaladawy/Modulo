# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 06:11:32 2017

@author: Andrei
"""

from .models import Module, Category, Interest
from .recommender import Recommender
from .feedback import Feedback
import copy

class Training():
    train_data_file = Recommender.savedRecommendationsFile
                                    
    def dict_compare(d1, d2):
        d1_keys = set(d1.keys())
        d2_keys = set(d2.keys())
        intersect_keys = d1_keys.intersection(d2_keys)
        added = d1_keys - d2_keys
        removed = d2_keys - d1_keys
        modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
        same = set(o for o in intersect_keys if d1[o] == d2[o])
        return added, removed, modified, same
                       
    def __cleanup_json_object(line, lineNo):
        #print("Cleaning up json_object ", lineNo)
        return Recommender.get_recommendation_from_json(line)
    
    def __validateRecommendation(rec, rec_no):
        """check that all categories, modules and interests are in the database"""
        #print("Validating recommendation", rec_no)
        #check that categories in recommendation.filters['category'] are also in database
        # -> if not remove category from filter
        allCategories = [c.name for c in Category.objects.all()]
        rec_categories = copy.deepcopy(rec.filters['categories'])
        for c in rec_categories:
            if not c in allCategories:
                rec.filters['categories'].remove(c)
        if rec.filters['categories'] != rec_categories:
            print("Categories of recommendation %s were not consistent with the database" % rec_no)
        
        #check that interests in recommendation.interests are also in database
        # -> if not remove interest from list
        allInterests = [i.name for i in Interest.objects.all()]
        rec_interests = copy.deepcopy(rec.interests)
        for i in rec_interests:
            if not i in allInterests:
                rec.interests.remove(i)
        if rec.interests != rec_interests:
            print("Interests of recommendation %s were not consistent with the database" % rec_no)
                
        #check that all modules in recommendation.feedback are also in database
        # -> if not remove module from feedback
        allModules = [m.title for m in Module.objects.all()]
        rec_modules_dict = copy.deepcopy(rec.feedback)
        if rec_modules_dict['selectedModule'] is not None and not rec_modules_dict['selectedModule'] in allModules:
            print("selectedModule:", rec_modules_dict['selectedModule'], "is not in database")
            rec.feedback['selectedModule'] = None
        for m in rec_modules_dict['interestingModules']:
            if not m in allModules:
                print("interestingModule:", m, "is not in database")
                rec.feedback['interestingModules'].remove(m)
        for m in rec_modules_dict['notForMeModules']:
            if not m in allModules:
                print("notForMeModule:", m, "is not in database")
                rec.feedback['notForMeModules'].remove(m)
        for m in rec_modules_dict['seenModules']:
            if not m in allModules:
                print("seenModule:", m, "is not in database")
                rec.feedback['seenModules'].remove(m)
        for m in rec_modules_dict['notSeenModules']:
            if not m in allModules:
                print("notSeenModule:", m, "is not in database")
                rec.feedback['notSeenModules'].remove(m)
        if rec.feedback != rec_modules_dict:
            print(Training.dict_compare(rec.feedback, rec_modules_dict))
            print("Modules of recommendation %s were not consistent with the database" % rec_no)
                
        return rec
    
    def __train_instance(rec, rec_no):
        #print("Training recommendation", rec_no)
        modules = rec.recommend()
        modules = [m.title for m in modules]
        modulesInRecommendation = [False for m in modules]
        
        modules_dict = copy.deepcopy(rec.feedback)
        if not modules_dict['selectedModule'] in modules:
            rec.feedback['selectedModule'] = None
        else:
            modulesInRecommendation[modules.index(modules_dict['selectedModule'])] = True
        for m in modules_dict['interestingModules']:
            if m not in modules:
                rec.feedback['interestingModules'].remove(m)
            else:
                modulesInRecommendation[modules.index(m)] = True
        for m in modules_dict['notForMeModules']:
            if m not in modules:
                rec.feedback['notForMeModules'].remove(m)
            else:
                modulesInRecommendation[modules.index(m)] = True
        for m in modules_dict['seenModules']:
            if m not in modules:
                rec.feedback['seenModules'].remove(m)
            else:
                modulesInRecommendation[modules.index(m)] = True
        for m in modules_dict['notSeenModules']:
            if m not in modules:
                rec.feedback['notSeenModules'].remove(m)
            else:
                modulesInRecommendation[modules.index(m)] = True
        rec.feedback['notSeenModules'] += [module for module_no, module in enumerate(modules) if not modulesInRecommendation[module_no]]
        
        feedback = Feedback(rec)
        feedback.setFeedback(save_recommendation=False)
    
    def train(self):
        try:
            with open(self.train_data_file, 'r') as old_file:
                for line_no, line in enumerate(old_file):
                    rec = Training.__cleanup_json_object(line, line_no)
                    rec = Training.__validateRecommendation(rec, line_no)
                    Training.__train_instance(rec, line_no)
        except FileNotFoundError as e:
            print('Could not find saved recommendations file...\nNot training the system...')
            print(e.args)