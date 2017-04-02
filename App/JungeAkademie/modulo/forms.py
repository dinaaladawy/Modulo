# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 03:43:16 2017

@author: Andrei
"""
from .models import Module, Interest#, Category, Exam, Location
from django import forms
from django.db import DatabaseError
from dal import autocomplete

class RecommenderForm(forms.Form):
    try:
        choices = [(i.name, i.name) for i in Interest.objects.all()]
    except DatabaseError:
        choices = []
    interests = forms.TypedMultipleChoiceField(choices=choices, empty_value=[], required=False)
    #location = forms.TypedChoiceField(choices=Location.LOCATIONS, required=False)
    time = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    credits = forms.FloatField(min_value=0.0, required=False)
    #exam = forms.TypedChoiceField(choices=Module.EXAM_TYPES, required=False)
    #exam = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, required=False)

class AdvancedRecommenderForm(forms.Form):
    try:
        choices = [(i.name, i.name) for i in Interest.objects.all()]
    except DatabaseError:
        choices = []
    interests = forms.TypedMultipleChoiceField(choices=choices, empty_value=[], required=False)
    #locationList = forms.TypedChoiceField(choices=Location.LOCATIONS, required=False)
    timeMin = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    timeMax = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    creditsMin = forms.FloatField(min_value=0.0, required=False)
    creditsMax = forms.FloatField(min_value=0.0, required=False)
    #examList = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, required=False)
    #examListDAL = forms.TypedChoiceField(choices=Exam.EXAM_TYPES, widget=autocomplete.Select2Multiple(choices=Exam.EXAM_TYPES), required=False)
    
    
class InterestForm(forms.ModelForm):
    try:
        choices = [(i.id, i.name) for i in Interest.objects.all()]
    except DatabaseError:
        choices = []
    interests = forms.TypedMultipleChoiceField(required=False, choices=choices, widget=autocomplete.Select2Multiple(url='modulo:interest-autocomplete'))

class ModuleForm(forms.ModelForm):
    try:
        #qs = Interest.objects.all()
        choices = [(i.id, i.name) for i in Interest.objects.all()]
    except DatabaseError:
        #qs = Interest.objects.none()
        choices = []
    #interests = forms.ModelChoiceField(required=False, queryset=qs, widget=autocomplete.ModelSelect2Multiple(url='modulo:interest-autocomplete'))
    interests = forms.TypedMultipleChoiceField(required=False, choices=choices, widget=autocomplete.Select2Multiple(url='modulo:interest-autocomplete', attrs={'data-placeholder': 'Select your interests...'}))
    
    time = forms.TimeField(input_formats=["%H:%M"], required=False, widget=forms.TimeInput(format='%H:%M'), initial='00:00')
    credits = forms.FloatField(min_value=0.0, required=False)
    
    class Meta:
        model = Module
        fields = ['time', 'exam', 'location', 'credits']#, 'type', 'language']
        widgets = {
            'exam': autocomplete.ListSelect2(url='modulo:exam-autocomplete', attrs={'data-placeholder': 'Select exam...'}),
            'location': autocomplete.ListSelect2(url='modulo:location-autocomplete', attrs={'data-placeholder': 'Select location...'}),
        }