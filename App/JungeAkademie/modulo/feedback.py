# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

class Feedback():    
    def __init__(self, recommendation, selectedModule=None, interestingModules=[], notForMeModules=[], seenModules=[], notSeenModules=[]):
        self.recommendation = recommendation
        self.selectedModule = None
        self.interestingModules = interestingModules
        self.notForMeModules = notForMeModules
        self.seenModules = seenModules
        self.notSeenModules = notSeenModules
    
    def updateFeedback(self, selectedModule=None, interestingModules=None, notForMeModules=None, seenModules=None, notSeenModules=None):
        if not selectedModule is None:
            self.selectedModule = selectedModule
        if not interestingModules is None:
            self.interestingModules = interestingModules
        if not notForMeModules is None:
            self.notForMeModules = notForMeModules
        if not seenModules is None:
            self.seenModules = seenModules
        if not notSeenModules is None:
            self.notSeenModules = notSeenModules
    
    def setFeedback(self):
        modules_dict = {}
        modules_dict['selected'] = self.selectedModule
        modules_dict['interesting'] = self.interestingModules
        modules_dict['notForMe'] = self.notForMeModules
        modules_dict['seen'] = self.seenModules
        modules_dict['notSeen'] = self.notSeenModules
        self.recommendation.incorporateFeedback(modules_dict)
    