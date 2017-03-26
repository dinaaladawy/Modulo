# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 03:43:16 2017

@author: Andrei
"""
from .models import Interest, Module
from django import forms

class RecommenderForm(forms.Form):
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value=[], required=False)
    place = forms.TypedChoiceField(choices=Module.LOCATIONS, required=False)
    time = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    credits = forms.FloatField(required=False)
    exam = forms.TypedChoiceField(choices=Module.EXAM_TYPES, required=False)
    
class ModuleForm(forms.ModelForm):
    #interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value="Please enter your interests", required=False)
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value=[], required=False)
    
    class Meta:
        model = Module
        fields = ['time', 'exam', 'place', 'credits']#, 'interests']
        '''
        labels = {
            'interests': ('Interests'),
        }
        help_texts = {
            'interests': ('Select your interests.'),
        }
        error_messages = {
            'interests': {
                'max_length': ("This interest is too long."),
            },
        }
        widgets = {
            'interests': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        #'''
    pass