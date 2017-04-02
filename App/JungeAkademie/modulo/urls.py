"""
modulo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import include, url
from . import views, views_documentation, views_recommendation
from .autocomplete import ExamAutocomplete, CourseFormatAutocomplete, InterestAutocomplete, LanguageAutocomplete, LocationAutocomplete, PersonalityAutocomplete

app_name = 'modulo'

module_patterns = [
    url(r'^$', views_documentation.module_index, name='modulo-module'),
    url(r'^(?P<module_title>["\'\w\s\-\.?!():&,_/]+)$', views_documentation.module, name='modulo-module-title'),
]

category_patterns = [
    url(r'^$', views_documentation.category_index, name='modulo-category'),
    url(r'^(?P<category_name>[\w\s\-]+)$', views_documentation.category, name='modulo-category-name'),
]

interest_patterns = [
    url(r'^$', views_documentation.interest_index, name='modulo-interest'),
    url(r'^(?P<interest_name>[\w\s\-]+)$', views_documentation.interest, name='modulo-interest-name'),
]

documentation_patterns = [
    url(r'^$', views_documentation.documentation, name='modulo-documentation'),
    url(r'^category/', include(category_patterns)),
    url(r'^interest/', include(interest_patterns)),
    url(r'^module/', include(module_patterns)), 
]

'''
url(r'^$', views_recommendation.recommender_state_machine, name='modulo-recommend'),
url(r'^recommendation/?$', views_recommendation.recommendation, name='modulo-recommendation'),
url(r'^recommendation/(?P<recommendation_id>\d+)$', views_recommendation.recommendation, name='modulo-recommendation'),
url(r'^thanks/?$', views_recommendation.recommender_thanks, name='modulo-recommender-thanks'),
url(r'^recommendation/feedback/?$', views_recommendation.recommender_feedback, name='modulo-recommender-feedback'),
'''
recommender_patterns = [
    url(r'^$', views_recommendation.recommender_state_machine, name='modulo-recommender'),    
    url(r'^(?P<state>\d{1})$', views_recommendation.recommender_state_machine, name='modulo-recommender'),
    url(r'^(?P<state>\d{1})(?P<prev_state>\d{1})$', views_recommendation.recommender_state_machine, name='modulo-recommender'),
    url(r'^(?P<state>\d{1})(?P<prev_state>\d{1})(?P<request_id>\d*)$', views_recommendation.recommender_state_machine, name='modulo-recommender'),
]

autocomplete_patterns = [
    url(r'^exam-autocomplete/$', ExamAutocomplete.as_view(), name='exam-autocomplete'),
    url(r'^interest-autocomplete/$', InterestAutocomplete.as_view(), name='interest-autocomplete'),
    url(r'^language-autocomplete/$', LanguageAutocomplete.as_view(), name='language-autocomplete'),
    url(r'^location-autocomplete/$', LocationAutocomplete.as_view(), name='location-autocomplete'),
    url(r'^personality-autocomplete/$', PersonalityAutocomplete.as_view(), name='personality-autocomplete'),
    url(r'^course-format-autocomplete/$', CourseFormatAutocomplete.as_view(), name='course-format-autocomplete'),
]

urlpatterns = [
    url(r'^$', views.index, name='modulo-index'),
    url(r'^recommender/', include(recommender_patterns)),
    url(r'^autocomplete/', include(autocomplete_patterns)),
    url(r'^documentation/', include(documentation_patterns)),
]