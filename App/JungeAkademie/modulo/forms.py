# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 03:43:16 2017

@author: Andrei
"""
from .models import Module, Interest, Exam, Location#, Category
from django import forms
from django.db import DatabaseError
from dal import autocomplete
import datetime

class AdvancedRecommenderForm(forms.Form):
    try:
        interestChoices = [(i.id, i.name) for i in Interest.objects.all()]
        examChoices = [(e.exam_type, e.exam_type) for e in Exam.objects.all()]
        locationChoices = [(l.location, l.location) for l in Location.objects.all()]
    except DatabaseError:
        interestChoices = []
        examChoices = []
        locationChoices = []
    timeMin = forms.TimeField(initial='00:00', input_formats=['%H:%M'], required=False, label='Min Start Time', widget=forms.TimeInput(format='%H:%M'), error_messages={'invalid': 'Enter a valid time using a "HH:MM" format'}, help_text='This is the lower bound of the starting time interval of your module recommendation. Please use the format "HH:MM".')
    timeMax = forms.TimeField(initial='23:59', input_formats=['%H:%M'], required=False, label='Max Start Time', widget=forms.TimeInput(format='%H:%M'), error_messages={'invalid': 'Enter a valid time using a "HH:MM" format'}, help_text='This is the lower bound of the starting time interval of your module recommendation. Please use the format "HH:MM".')
    creditsMin = forms.FloatField(initial=0, min_value=0.0, label='Min Credits', required=False, help_text='This is the desired lowest amount of credits of your module recommendation.')
    creditsMax = forms.FloatField(min_value=0.0, label='Max Credits', required=False, help_text='This is the desired highest amount of credits of your module recommendation.')
    exam = forms.TypedMultipleChoiceField(choices=examChoices, label='Exam Types', required=False, widget=autocomplete.Select2Multiple(url='modulo:exam-autocomplete', attrs={'data-placeholder': 'Select exam types...'}), help_text='These are the available exam types. You can select multiple exam types.')
    location = forms.TypedMultipleChoiceField(choices=locationChoices, label='Locations', required=False, widget=autocomplete.Select2Multiple(url='modulo:location-autocomplete', attrs={'data-placeholder': 'Select locations...'}), help_text='These are the available locations. You can select multiple locations.')
    interests = forms.TypedMultipleChoiceField(required=False, label='Interests', choices=interestChoices, widget=autocomplete.Select2Multiple(url='modulo:interest-autocomplete', attrs={'data-placeholder': 'Select your interests...'}), help_text='You can type your interests to get module recommendations which have contents according to your interests.')    
    
    def processInterests(self):
        interests = self.cleaned_data['interests']
        if interests is None:
            interests = []
        elif isinstance(interests, list):
            interests = [Interest.objects.get(id=i).name for i in interests]
        else:
            raise ValueError("Unknown type for interests type: "+type(interests))
        return interests
    
    def processTime(self):
        timeMin = self.cleaned_data['timeMin']
        timeMax = self.cleaned_data['timeMax']
        if timeMin is None:
            timeMin = datetime.datetime.strptime('00:00', '%H:%M').time()
        if timeMax is None:
            timeMax = datetime.datetime.strptime('23:59', '%H:%M').time()
        return (timeMin, timeMax)
    
    def processCredits(self):
        creditsMin = self.cleaned_data['creditsMin']
        creditsMax = self.cleaned_data['creditsMax']
        if creditsMin is None:
            creditsMin = 0    
        if creditsMax is None:
            creditsMax = float('inf')
        return (creditsMin, creditsMax)
    
    def processExam(self):
        exam = self.cleaned_data['exam']
        if exam is None:
            exam = []
        elif isinstance(exam, list):
            exam = [Exam.objects.get(exam_type=e).exam_type for e in exam]
        else:   
            raise ValueError("Unknown type for exam type: "+type(exam))
        return exam
    
    def processLocation(self):
        location = self.cleaned_data['location']
        if location is None:
            location = []
        elif isinstance(location, list):
            location = [Location.objects.get(location=l).location for l in location]
        else:
            raise ValueError("Unknown type for location type: "+type(location))
        return location
    
    def getInitialValuesFromRecommendation(rec):
        init_interests = [Interest.objects.get(name=i).id for i in rec.interests]
        init_exam = rec.filters['exam'] #[Exam.objects.get(exam_type=e).exam_type for e in rec.filters['exam']] if isinstance(rec.filters['exam'], list) else None #list
        init_location = rec.filters['location'] #[Location.objects.get(location=l).location for l in rec.filters['location']] if isinstance(rec.filters['location'], list) else None #list
        init_timeMin = rec.filters['time'][0] #tuple
        init_timeMax = rec.filters['time'][1] #tuple
        init_creditsMin = rec.filters['credits'][0] #tuple
        init_creditsMax = rec.filters['credits'][1] #tuple
        return {'interests': init_interests, 'location': init_location, 'exam': init_exam, 'creditsMax': init_creditsMax, 'creditsMin': init_creditsMin, 'timeMax': init_timeMax, 'timeMin': init_timeMin}
    
    def clean(self):
        cleaned_data = super(AdvancedRecommenderForm, self).clean()
        timeMin = cleaned_data.get('timeMin')
        timeMax = cleaned_data.get('timeMax')
        creditsMin = cleaned_data.get('creditsMin')
        creditsMax = cleaned_data.get('creditsMax')

        if timeMin is not None and timeMax is not None:
            if timeMin > timeMax:
                msg = "The value of field 'Min Start Time' must be less or equal than the value of the field 'Max Start Time'"
                self.add_error('timeMin', msg)
                self.add_error('timeMax', msg)
            
        if creditsMin is not None and creditsMax is not None:
            if creditsMin > creditsMax:
                msg = "The value of the field 'Min Credits' must be less or equal the the value of the field 'Max Credits'"
                self.add_error('creditsMin', msg)
                self.add_error('creditsMax', msg)
    
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
    interests = forms.TypedMultipleChoiceField(required=False, choices=choices, widget=autocomplete.Select2Multiple(url='modulo:interest-autocomplete', attrs={'data-placeholder': 'Select your interests...'}), help_text='You can type your interests to get module recommendations which have contents according to your interests.')
    time = forms.TimeField(initial='00:00', input_formats=['%H:%M'], label='Start time', required=False, widget=forms.TimeInput(format='%H:%M'), error_messages={'invalid': 'Enter a valid time using a "HH:MM" format'}, help_text='This desired starting time of your module recommendation. For selecting a starting time interval please use the advanced filter form. Please use the format "HH:MM".')
    credits = forms.FloatField(initial=0, min_value=0.0, required=False, help_text='This is the desired amount of credits of your module recommendation. For selecting credit interval use the advanced filter form.')
    
    class Meta:
        model = Module
        fields = ['time', 'credits', 'exam', 'location']#, 'type', 'language']
        widgets = {
            'exam': autocomplete.ListSelect2(url='modulo:exam-autocomplete', attrs={'data-placeholder': 'Select exam type...'}),
            'location': autocomplete.ListSelect2(url='modulo:location-autocomplete', attrs={'data-placeholder': 'Select location...'}),
        }
        labels = {
            'exam': 'Exam type',
        }
        help_texts = {
            'exam': 'These are the available exam types. You can select one type. For selecting multiple types use the advanced filter form.',
            'location': 'These are the available locations. You can select one location. For selecting multiple locations use the advanced filter form.'
        }
        
    def processInterests(self):
        interests = self.cleaned_data['interests']
        if interests is None:
            interests = []
        elif isinstance(interests, list):
            #print(interests)
            interests = [Interest.objects.get(id=i).name for i in interests]
        else:
            raise ValueError("Unknown type for interests type: "+type(interests))
        return interests
    
    def processTime(self):
        time = self.cleaned_data['time']
        if time is None:
            timeMin = datetime.datetime.strptime('00:00', '%H:%M').time()
            timeMax = datetime.datetime.strptime('23:59', '%H:%M').time()
        else:
            timeMin = time
            timeMax = time
        return (timeMin, timeMax)
    
    def processCredits(self):
        credits = self.cleaned_data['credits']
        if credits is None:
            creditsMin = 0
            creditsMax = float('inf')
        else:
            creditsMin = credits
            creditsMax = credits
        return (creditsMin, creditsMax)
    
    def processExam(self):
        exam = self.cleaned_data['exam']
        if exam is None:
            exam = []
        elif isinstance(exam, Exam):
            exam = [exam.exam_type]
        else:
            raise ValueError("Unknown type for exam type: "+type(exam))
        return exam
        
    def processLocation(self):
        location = self.cleaned_data['location']
        if location is None:
            location = []
        elif isinstance(location, Location):
            location = [location.location]
        else:
            raise ValueError("Unknown type for location type: "+type(location))
        return location
    
    def getInitialValuesFromRecommendation(rec):
        init_interests = [Interest.objects.get(name=i).id for i in rec.interests]
        init_exam = rec.filters['exam'][0] if (isinstance(rec.filters['exam'], list) and rec.filters['exam']) else None #list
        init_location = rec.filters['location'][0] if (isinstance(rec.filters['location'], list) and rec.filters['location']) else None #list
        init_time = rec.filters['time'][0] #tuple
        init_credits = rec.filters['credits'][0] #tuple
        return {'interests': init_interests, 'location': init_location, 'exam': init_exam, 'time': init_time, 'credits': init_credits}