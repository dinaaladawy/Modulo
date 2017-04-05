# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from django.db.models import F
from .models import Module
import copy

class Feedback():    
    def __init__(self, recommendation, selectedModule=None, interestingModules=[], notForMeModules=[], seenModules=[], notSeenModules=[]):
        self.recommendation = recommendation
        if hasattr(recommendation, 'feedback') and recommendation.feedback != {}:
            self.modules_dict = copy.deepcopy(recommendation.feedback)
        else:
            self.modules_dict = {
                'selectedModule': selectedModule,
                'interestingModules': interestingModules,
                'notForMeModules': notForMeModules,
                'seenModules': seenModules,
                'notSeenModules': notSeenModules,
            }
    
    def updateFeedback(self, selectedModule=None, interestingModules=None, notForMeModules=None, seenModules=None, notSeenModules=None):
        if selectedModule is not None and selectedModule != self.modules_dict['selectedModule']:
            self.modules_dict['selectedModule'] = selectedModule
        if interestingModules is not None and interestingModules != self.modules_dict['interestingModules']:
            self.modules_dict['interestingModules'] = interestingModules
        if notForMeModules is not None and notForMeModules != self.modules_dict['notForMeModules']:
            self.modules_dict['notForMeModules'] = notForMeModules
        if seenModules is not None and seenModules != self.modules_dict['seenModules']:
            self.modules_dict['seenModules'] = seenModules
        if notSeenModules is not None and notSeenModules != self.modules_dict['notSeenModules']:
            self.modules_dict['notSeenModules'] = notSeenModules
    
    def setFeedback(self, save_recommendation=True):
        self.recommendation.incorporateFeedback(self.modules_dict, save_recommendation)
        if self.modules_dict['selectedModule'] is not None:
            m = Module.objects.get(title=self.modules_dict['selectedModule'])
            m.selected = F('selected') + 1
            #m.save()