# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 03:43:16 2017

@author: Andrei
"""
from .models import Exam, Location, Interest, Category, Module
from django import forms

class RecommenderForm(forms.Form):
    #filters
    interests = forms.TypedMultipleChoiceField(required=False)
    place = forms.ChoiceField(required=False)
    time = forms.TimeField(required=False, input_formats='%H:%M')
    credits = forms.FloatField(required=False)
    exam = forms.ChoiceField(required=False)
    
class ModuleForm(forms.ModelForm):
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()] , empty_value="Please enter your interests" , required=False)
    
    class Meta:
        model = Module
        fields = ['time', 'exam', 'place', 'credits']
        '''
        labels = {
            'name': _('Writer'),
        }
        help_texts = {
            'name': _('Some useful help text.'),
        }
        error_messages = {
            'name': {
                'max_length': _("This writer's name is too long."),
            },
        }
        widgets = {
            'name': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        '''
    pass