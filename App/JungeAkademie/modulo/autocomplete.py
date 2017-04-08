# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 11:28:54 2017

@author: Andrei
"""

from dal import autocomplete
from .models import CourseFormat, Exam, Language, Location, Personality
from .models import Interest

class InterestAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        #print("In InterestAutocomplete:", self.__dict__)
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
            #return Interest.objects.none()
            pass

        qs = Interest.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

class CourseFormatAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
			#return CourseFormat.objects.none()
            pass

        qs = CourseFormat.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs
    
class ExamAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        #print("In ExamAutocomplete:", self.__dict__)
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
            #return Exam.objects.none()
            pass

        qs = Exam.objects.all()

        if self.q:
            qs = qs.filter(exam_type__istartswith=self.q)

        return qs
    
class LanguageAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
			#return Language.objects.none()
            pass

        qs = Language.objects.all()

        if self.q:
            qs = qs.filter(language__istartswith=self.q)

        return qs
    
class LocationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        #print("In LocationAutocomplete:", self.__dict__)
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
            #return Location.objects.none()
            pass

        qs = Location.objects.all()

        if self.q:
            qs = qs.filter(location__istartswith=self.q)

        return qs
    
class PersonalityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            #print("User not authenticated..")
			#return Personality.objects.none()
            pass

        qs = Personality.objects.all()

        if self.q:
            qs = qs.filter(personality__istartswith=self.q)

        return qs