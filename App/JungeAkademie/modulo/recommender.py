# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 14:11:11 2017

@author: Andrei
"""

from .algorithms import UpdateType, LinearClassifier
from .models import Interest, Category, Module
from django.db.models.signals import pre_save, pre_delete
from django.db import DatabaseError
from django.dispatch import receiver
import datetime
import json
import copy
import threading


class HandleRecommender(json.JSONEncoder):
    """ json.JSONEncoder extension: handle Recommender """

    def default(self, obj):
        if isinstance(obj, Recommender):
            return Recommender.get_json_from_recommendation(obj)
        return json.JSONEncoder.default(self, obj)


class Recommender:
    savedRecommendationsFile = 'modulo/recommendations/recommendations.txt'
    savedRecommendationsFileLock = None
    # name of all categories
    category_names = []
    # name of all interests
    interest_names = []
    # selected learning algorithm
    algorithm = None

    def __init__(self, id=None,
                 time_interval=(datetime.datetime.strptime('00:00', '%H:%M').time(),
                                datetime.datetime.strptime('23:59', '%H:%M').time()),
                 credits=(0, float('inf')), exam_types=[], locations=[], interests=[]):
        self.id = id
        self.filters = {'time': time_interval,  # tuple with range of starting time of course
                        'credits': credits,  # tuple with range of acceptable credits
                        'exam': exam_types,  # list of acceptable exam types
                        'location': locations}  # list of locations
        self.feedback = None

        self.interests = interests  # list of id's of interests from models.Interest
        # handle interests that are not in the database
        for i in self.interests[:]:
            if i not in Recommender.interest_names:
                print("Interest %s not found in database!" % i)
                inp = input("What to do?\nEnter \"add\" to add to database or press ENTER to skip interest... ")
                if inp == "add":
                    # interest not in database, add it...
                    Interest.objects.create(name=i)
                else:
                    # if not added in the database, remove it from list
                    self.interests.remove(i)

    '''
    def __get_categories_from_interests(self):
        """
        apply learning algorithm to map the selected interests to categories
        returns sorted list of category_names according to the user interests
        """
        res = self.algorithm.run_algorithm(evaluate=True, all_interests=self.interest_names,
                                           selected_interests=self.interests)

        probs = res['eval'][0]  # 0 because of batch_dimension (in our case: always 1)...
        print(probs)
        sorted_indices = sorted(range(len(Recommender.category_names)), key=lambda k: probs[k], reverse=True)
        categories_sorted = [Recommender.category_names[i] for i in sorted_indices]
        probs[:] = [probs[i] for i in sorted_indices]

        nr_categories = len(categories_sorted)
        threshold = 0.1 if nr_categories > 100 else 0.2 if nr_categories > 50 else 0.5 if nr_categories > 20 else 1
        threshold = int(threshold * len(categories_sorted))
        return categories_sorted[:threshold], probs[:threshold], nr_categories, threshold
    '''

    def __get_categories_from_interests(self):
        """
        apply learning algorithm to map the selected interests to categories
        returns sorted list of category_names according to the user interests
        """
        res = self.algorithm.run_algorithm(evaluate=True, all_interests=self.interest_names,
                                           selected_interests=self.interests)

        selected_categories = [c for i, c in enumerate(self.category_names) if res['eval'][0][i] == 1.0]
        # print(selected_categories)

        nr_categories = len(selected_categories)
        # print("nr_selected_categories =", nr_categories)
        threshold = 0.1 if nr_categories > 100 else 0.2 if nr_categories > 50 else 0.5 if nr_categories > 20 else 1
        threshold = int(threshold * len(selected_categories))
        return selected_categories[:threshold], nr_categories, threshold

    def __check_module(self, m):
        """
        checks if the module is in compliance with the filters:
        
        print("Checking module", m.title)
        print("Filters:")
        for key, filter_value in self.filters.items():
            print('\tkey = ', key, '; filter_value = ', filter_value, sep='')
        print('Module:')
        for key in self.filters.keys():
            if key != 'categories':
                print('\tkey = ', key, '; m.', key, ' = ', getattr(m, key), sep='')
            else:
                print('\tkey = ', key, '; m.', key, ' = [', sep='', end='')
                module_value = getattr(m, key)
                for c in module_value.all():
                    print(c.name, ', ', sep='', end='')
                print(']')
        """
        category_ok = False
        # do this to ensure that the 'categories' filter gets checked first!!!
        # filter_keys = ['categories', 'credits', 'exam', 'location', 'time']
        for key in sorted(self.filters):
            filter_value = self.filters[key]
            module_value = getattr(m, key)
            # print("key =", key)
            # print("filter_value =", filter_value)
            # print("module_value =", module_value)
            if key == 'categories':
                # if module has no categories assigned, consider it ok...
                module_category_in_selected_categories = False or (module_value.all().count() == 0)
                for c in module_value.all():
                    if c.name in filter_value:
                        module_category_in_selected_categories = True
                        break
                if not module_category_in_selected_categories:
                    # print("Module", m.title, "doesn't respect categories filter!")
                    return False, category_ok
                category_ok = True
            if key == 'time':
                if not (filter_value[0] <= module_value <= filter_value[1]):
                    # print("Module", m.title, "doesn't respect time filter!")
                    return False, category_ok
            if key == 'credits':
                if module_value != 0.0 and not (filter_value[0] <= module_value <= filter_value[1]):
                    # print("Module", m.title, "doesn't respect credits filter!")
                    return False, category_ok
            if key == 'exam':
                if module_value is not None and filter_value != [] and module_value.exam_type not in filter_value:
                    # print("Module", m.title, "doesn't respect exam filter!")
                    return False, category_ok
            if key == 'location':
                if module_value is not None and filter_value != [] and module_value.location not in filter_value:
                    # print("Module", m.title, "doesn't respect location filter!")
                    return False, category_ok
        # print("Module", m.title, "respects the filters!")
        return True, category_ok

    def __filter_modules(self):
        """
        apply the filters (categories_sorted, time, location, exam, etc.) on the modules
        return list of modules (not just module titles...) matching all filters...
        """
        nr_modules = Module.objects.count()
        nr_modules_filtered_out = 0  # number of modules where the category was ok, but the other filters were not
        ok_modules = []
        for m in Module.objects.all():
            is_module_ok, category_ok = self.__check_module(m)
            if is_module_ok:
                # print("Module {} has categories {}.".format(m.title, [c.name for c in m.categories.all()]))
                # implies category_ok is TRUE
                ok_modules.append(m)
            elif category_ok:
                # is_module_ok is FALSE -> other filters eliminated it
                nr_modules_filtered_out += 1
        return ok_modules, nr_modules_filtered_out, nr_modules

    def __sort_modules(self, modules):
        """
        sort the selected/filtered modules according to relevance
        return sorted list of modules (not module titles, actual modules...)
        sort according to choices?!?!?!
        """
        categories_matched = []
        set_category_names = set(self.category_names)
        for m in modules:
            categories_matched.append(-len(set([c.name for c in m.categories.all()]).intersection(set_category_names)))
        order = sorted(range(len(modules)),
                       key=lambda i: (categories_matched[i], modules[i].selections, modules[i].title))
        
        '''
        print(categories_matched)
        for i in order:
            print((categories_matched[i], modules[i].selections, modules[i].title))
        '''
        return [modules[i] for i in order]

    def update_filters(self, time_interval=None, credits=None, exam_types=None,
                       locations=None, categories=None, interests=None):
        if time_interval is not None and time_interval != self.filters['time']:
            self.filters['time'] = time_interval
        if credits is not None and credits != self.filters['credits']:
            self.filters['credits'] = credits
        if exam_types is not None and exam_types != self.filters['exam']:
            self.filters['exam'] = exam_types
        if locations is not None and locations != self.filters['location']:
            self.filters['location'] = locations
        if categories is not None:
            if 'categories' not in self.filters.keys() or \
                    ('categories' in self.filters.keys() and categories != self.filters['categories']):
                self.filters['categories'] = categories
        if interests is not None and interests != self.interests:
            self.interests = interests

    def recommend(self):
        # map the interests to the module categories (learning algorithm)
        selected_categories, nr_selected_categories, threshold = self.__get_categories_from_interests()
        # print(selected_categories, probabilities, sep='\n')
        self.filters['categories'] = copy.deepcopy(selected_categories)

        # apply the filters on the list of modules (use objects.filter(...))
        modules, nr_modules_filtered_out, nr_modules = self.__filter_modules()

        recommendation_log = ("The algorithm selected {0} out of {1} categories. "
                              "These are (in order of probabilities):\n{2}\n"
                              "Based on these categories, {3} of {4} modules were selected."). \
            format(threshold, nr_selected_categories, self.filters['categories'],
                   len(modules) + nr_modules_filtered_out, nr_modules)
        recommendation_log = ("Based on your interests, the algorithm selected {0} out of {1} modules."). \
            format(len(modules) + nr_modules_filtered_out, nr_modules)
        if nr_modules_filtered_out > 0:
            recommendation_log += " The other filters reduced the number of modules to {0}.".format(len(modules))
        recommendation_log += "\n"

        # current: sort according to relevance (number of selections of module)
        # self.modules = self.__sort_modules(modules)
        return self.__sort_modules(modules), recommendation_log

    def incorporate_feedback(self, modules_dict, save_recommendation=True):
        self.feedback = copy.deepcopy(modules_dict)
        feedback = {'interesting_modules': [Module.objects.get(title=t) for t in self.feedback['interesting_modules']],
                    'not_for_me_modules': [Module.objects.get(title=t) for t in self.feedback['not_for_me_modules']]}
        self.algorithm.run_algorithm(train=True, all_interests=self.interest_names, selected_interests=self.interests,
                                     all_categories=self.category_names, feedback=feedback)
        if save_recommendation:
            self.save()

    def save(self):
        with Recommender.savedRecommendationsFileLock, open(Recommender.savedRecommendationsFile, "a") as file:
            rec_serialized = json.dumps(self, cls=HandleRecommender)
            file.write(rec_serialized + "\n")

    @staticmethod
    def initialize():
        Recommender.savedRecommendationsFileLock = threading.Lock()
        # get the number of categories in the database
        try:
            categories = list(Category.objects.all())
        except DatabaseError as e:
            print("DATABASE error; message = {}".format(e))
            categories = []
        # nr_categories = len(categories)
        # print("Number of categories = ", nr_categories, sep='')

        # get the number of interests in the database
        try:
            interests = list(Interest.objects.all())
        except DatabaseError as e:
            print("DATABASE error; message = {}".format(e))
            interests = []
        # nr_interests = len(interests)
        # print("Number of interests = ", nr_interests, sep='')

        Recommender.category_names = [c.name for c in categories]
        # print("Recommender.category_names = ", Recommender.category_names, sep='')
        Recommender.interest_names = [i.name for i in interests]
        # print("Recommender.interest_names = ", Recommender.interest_names, sep='')

        print("Recommender initialized")

    @staticmethod
    def get_json_from_recommendation(rec):
        filters = copy.deepcopy(rec.filters)
        time_format = '%H:%M'
        time_interval = filters['time']
        filters['time'] = (time_interval[0].strftime(time_format), time_interval[1].strftime(time_format))

        json_object = {'feedback': copy.deepcopy(rec.feedback), 'filters': filters,
                       'id': rec.id, 'interests': copy.deepcopy(rec.interests)}
        return json_object

    @staticmethod
    def get_recommendation_from_json(json_object):
        # print("JSON Object is", json_object)
        cleanup_json_object = json.loads(json_object)
        r = Recommender()

        if 'id' in cleanup_json_object:
            # Integer
            r.id = cleanup_json_object['id']

        if 'filters' in cleanup_json_object:
            filters = cleanup_json_object['filters']
            if 'time' in filters:
                # 2-tuple of datetime.time
                time_format = '%H:%M'
                time_interval = (datetime.datetime.strptime(filters['time'][0], time_format).time(),
                                 datetime.datetime.strptime(filters['time'][1], time_format).time())
                r.update_filters(time_interval=time_interval)
            if 'credits' in filters:
                # 2-tuple of Integers;
                # filters['credits'] is a list!!! -> convert it to tuple
                credit_tuple = (filters['credits'][0], filters['credits'][1])
                r.update_filters(credits=credit_tuple)
            if 'exam' in filters:
                # list of strings or empty list
                if isinstance(filters['exam'], str):
                    filters['exam'] = [filters['exam']]
                r.update_filters(exam_types=filters['exam'])
            if 'location' in filters:
                # list of strings or empty list
                if isinstance(filters['location'], str):
                    filters['location'] = [filters['location']]
                r.update_filters(locations=filters['location'])
            if 'categories' in filters:
                # list of strings
                r.update_filters(categories=filters['categories'])

        if 'interests' in cleanup_json_object:
            # list of strings
            r.update_filters(interests=cleanup_json_object['interests'])

        if 'feedback' in cleanup_json_object:
            # (module titles) dictionary
            r.feedback = cleanup_json_object['feedback']

        return r


@receiver(pre_save, sender=Category)
def insert_category_signal_handler(sender, **kwargs):
    category = kwargs['instance']

    # if category is already in database, an update was performed and no action necessary
    if category.name in Recommender.category_names:
        return

    # if category isn't in database, an insert was performed
    Recommender.learning_algorithm.updateWeights(UpdateType.INSERT_CATEGORY)
    Recommender.category_names.append(category.name)


@receiver(pre_delete, sender=Category)
def delete_category_signal_handler(sender, **kwargs):
    category = kwargs['instance']

    # get the index of the category in the category list
    # and delete the index'th column from weight and the index'th row from bias
    index = Recommender.category_names.index(category.name)
    Recommender.learning_algorithm.updateWeights(UpdateType.DELETE_CATEGORY, index)
    Recommender.category_names.remove(category.name)


@receiver(pre_save, sender=Interest)
def insert_interest_signal_handler(sender, **kwargs):
    interest = kwargs['instance']

    # if interest is already in database, an update was performed and no action necessary
    if interest.name in Recommender.interest_names:
        return

    # if interest isn't in database, an insert was performed
    Recommender.learning_algorithm.updateWeights(UpdateType.INSERT_INTEREST)
    Recommender.interest_names.append(interest.name)


@receiver(pre_delete, sender=Interest)
def delete_interest_signal_handler(sender, **kwargs):
    interest = kwargs['instance']

    # get the index of the interest in the interest list
    # and delete the index'th row from weight
    index = Recommender.interest_names.index(interest.name)
    Recommender.learning_algorithm.updateWeights(UpdateType.DELETE_INTEREST, index)
    Recommender.interest_names.remove(interest.name)
