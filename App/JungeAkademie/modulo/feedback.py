# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from django.db.models import F
from .models import Module
import copy


class Feedback():
    def __init__(self, recommendation, selected_module=None, interesting_modules=[],
                 not_for_me_modules=[], seen_modules=[], not_seen_modules=[]):
        self.recommendation = recommendation
        if hasattr(recommendation, 'feedback') and recommendation.feedback != {}:
            self.modules_dict = copy.deepcopy(recommendation.feedback)
        else:
            self.modules_dict = {
                'selected_module': selected_module,
                'interesting_modules': interesting_modules,
                'not_for_me_modules': not_for_me_modules,
                'seen_modules': seen_modules,
                'not_seen_modules': not_seen_modules,
            }

    def update_feedback(self, selected_module=None, interesting_modules=None,
                        not_for_me_modules=None, seen_modules=None, not_seen_modules=None):
        if selected_module is not None and selected_module != self.modules_dict['selected_module']:
            self.modules_dict['selected_module'] = selected_module
        if interesting_modules is not None and interesting_modules != self.modules_dict['interesting_modules']:
            self.modules_dict['interesting_modules'] = interesting_modules
        if not_for_me_modules is not None and not_for_me_modules != self.modules_dict['not_for_me_modules']:
            self.modules_dict['not_for_me_modules'] = not_for_me_modules
        if seen_modules is not None and seen_modules != self.modules_dict['seen_modules']:
            self.modules_dict['seen_modules'] = seen_modules
        if not_seen_modules is not None and not_seen_modules != self.modules_dict['not_seen_modules']:
            self.modules_dict['not_seen_modules'] = not_seen_modules

    def set_feedback(self, save_recommendation=True):
        self.recommendation.incorporateFeedback(self.modules_dict, save_recommendation)
        if self.modules_dict['selected_module'] is not None:
            m = Module.objects.get(title=self.modules_dict['selected_module'])
            m.selected = F('selected') + 1
            # m.save()
