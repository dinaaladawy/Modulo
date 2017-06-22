# -*- coding: utf-8 -*-
"""
Created on 15 Jun 2017 at 19:39 

@author: Andrei
"""

from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    '''
    print(dictionary)
    print(key)
    print(dictionary.get(key))
    '''
    return dictionary.get(key)
