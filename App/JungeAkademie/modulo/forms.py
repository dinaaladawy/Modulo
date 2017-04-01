# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 03:43:16 2017

@author: Andrei
"""
from .models import Exam, Location, Interest, Category, Module
from django import forms
from dal import autocomplete
from dal.widgets import SelectMultiple

class RecommenderForm(forms.Form):
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value=[], required=False)
    #location = forms.TypedChoiceField(choices=Location.LOCATIONS, required=False)
    time = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    credits = forms.FloatField(min_value=0.0, required=False)
    #exam = forms.TypedChoiceField(choices=Module.EXAM_TYPES, required=False)
    #exam = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, required=False)

class AdvancedRecommenderForm(forms.Form):
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value=[], required=False)
    #locationList = forms.TypedChoiceField(choices=Location.LOCATIONS, required=False)
    timeMin = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    timeMax = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    creditsMin = forms.FloatField(min_value=0.0, required=False)
    creditsMax = forms.FloatField(min_value=0.0, required=False)
    #examList = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, required=False)
    #examListDAL = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, widget=autocomplete.Select2Multiple(choices=Exam.EXAM_TYPES), required=False)
    
class ModuleForm(forms.ModelForm):
    #interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value="Please enter your interests", required=False)
    interests = forms.TypedMultipleChoiceField(choices=[(i.name, i.name) for i in Interest.objects.all()], empty_value=[], required=False)
    
    #time = forms.TimeField(widget=forms.widgets.TimeInput(input_formats=["%H:%M"]))
    time = forms.TimeField(input_formats=["%H:%M"], required=False, widget=forms.TimeInput(format='%H:%M'), initial='00:00')
    
    class Meta:
        model = Module
        fields = ['time', 'exam', 'location', 'credits']#, 'interests']
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