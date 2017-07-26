# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 11:13:26 2017

@author: Andrei
"""

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, reverse
from .forms import ModuleForm, AdvancedRecommenderForm
from .feedback import Feedback
from .models import Module, HandleModule
from .recommender import Recommender, HandleRecommender
import copy, datetime, enum, json, re, threading

allowed_transitions = None
id_counter = None


class UserState(enum.Enum):
    SELECT_FILTERS = 0
    DISPLAY_MODULES = 1
    UPDATE_FILTERS = 2
    SEE_FEEDBACK = 3
    THANKS = 4

    def from_string(val):
        # camel-case because value from templates...
        if val == "selectFilters":
            return UserState.SELECT_FILTERS
        elif val == "displayModules":
            return UserState.DISPLAY_MODULES
        elif val == "updateFilters":
            return UserState.UPDATE_FILTERS
        elif val == "seeFeedback":
            return UserState.SEE_FEEDBACK
        elif val == "thanks":
            return UserState.THANKS
        else:
            return None

    def to_string(self):
        if self.value == 0:
            return "select_filters"
        elif self.value == 1:
            return "display_modules"
        elif self.value == 2:
            return "update_filters"
        elif self.value == 3:
            return "see_feedback"
        elif self.value == 4:
            return "thanks"
        else:
            return None


def print_session_content(session):
    for key, value in session.items():
        print("Key:", key, "with value:", value, "and value type:", type(value))


def validate_session_state(session_current_state, session_previous_state):
    global allowed_transitions
    return (session_previous_state, session_current_state) in allowed_transitions


def process_form(form, rec):
    # process the data in form.cleaned_data as required
    rec.update_filters(time_interval=form.processTime(), credits=form.processCredits(), exam_types=form.processExam(),
                       locations=form.processLocation(), interests=form.processInterests())
    return rec


def process_display_modules_post_data(post_data, displayed_modules):
    valid = False
    data = {}
    keys = list(post_data.keys())
    # INFO: submit can only occur as key in module (e.g. 'submit5') not as 'submitFeedback' -> handled before
    module_button_pressed = \
        displayed_modules[int(keys[['submit' in key for key in keys].index(True)].split('submit')[1]) - 1] \
            if any(['submit' in key for key in keys]) else None
    mods = ['module' in key for key in keys]
    dets = ['details' in key for key in keys]
    if any(mods) and mods.count(True) == 1:
        valid = True
        d = {}
        module_key = keys[mods.index(True)]
        module_index = int(module_key.split('module')[1])
        d['module_display_nr'] = module_index  # starting at 1 not at 0
        module = displayed_modules[module_index - 1]
        d['module_title'] = module.title
        if post_data[module_key] == 'selected':
            d['feedback_type'] = 'selected_module'
        elif post_data[module_key] == 'interesting':
            d['feedback_type'] = 'interesting_modules'
        elif post_data[module_key] == 'not-for-me':
            d['feedback_type'] = 'not_for_me_modules'
        else:
            raise Exception('Unknown feedback received...')
        data['feedback'] = d
    if any(dets):
        valid = True
        d = {}
        details_key = keys[dets.index(True)]
        details_index = int(details_key.split('details')[1])
        d['module_display_nr'] = details_index  # starting at 1 not at 0
        module = displayed_modules[details_index - 1]
        d['module_title'] = module.title
        d['type'] = 'see' if post_data[details_key] == 'More details' else 'hide'
        data['details'] = d
    return valid, data, module_button_pressed


def process_see_feedback_post_data(post_data, module_dict):
    valid = False
    data = {}
    keys = list(post_data.keys())
    # INFO: submit can occur as key either in module (e.g. 'submit5') or as 'submitFeedback'
    # INFO: but not at the same time...
    module_button_pressed = keys[['submit' in key for key in keys].index(True)].split('submit')[1] \
        if any(['submit' in key for key in keys]) else None
    mods = ['_module_' in key for key in keys]
    dets = ['details' in key for key in keys]
    if 'submitFeedback' in keys:
        valid = True
        data['submitFeedback'] = True
    if any(mods):
        valid = True
        d = {}
        module_key = keys[mods.index(True)]
        d['current_feedback'] = module_key.split('_module_')[0]
        d['module_title'] = module_key.split('_module_')[1]
        d['new_feedback'] = post_data[module_key]
        data['feedback'] = d
    if any(dets):
        valid = True
        d = {}
        details_key = keys[dets.index(True)]
        d['module_title'] = details_key.split('details')[1]
        d['type'] = 'see' if post_data[details_key] == 'More details' else 'hide'
        data['details'] = d
    return valid, data, module_button_pressed


def submit_feedback(rec, modules_dict):
    # incorporate feedback into the system
    f = Feedback(recommendation=rec)
    f.update_feedback(**modules_dict)
    f.set_feedback()


def session_is_valid(request):
    if 'in_system' not in request.session:
        # print("Session has expired...")
        return False

    session_information = False

    if request.session.get('current_state', None) is None and request.session.get('next_state', None) is None:
        # print("First time in the system!")
        request.session['first_time'] = False
    else:
        assert (request.session.get('current_state', None) is not None and
                request.session.get('next_state', None) is not None)
        session_information = True

    # my session keys:
    # recommendation, modules, module_display_indices,
    # module_remaining_indices, detailed_views, feedback,
    # advancedForm, current_state, next_state
    all_keys_present = 'recommendation' in request.session and \
                       'modules' in request.session and \
                       'module_display_indices' in request.session and \
                       'module_remaining_indices' in request.session and \
                       'detailed_views' in request.session and \
                       'feedback' in request.session and \
                       'advancedForm' in request.session
    keys_present = 'recommendation' in request.session or \
                   'modules' in request.session or \
                   'module_display_indices' in request.session or \
                   'module_remaining_indices' in request.session or \
                   'detailed_views' in request.session or \
                   'feedback' in request.session or \
                   'advancedForm' in request.session
    no_keys_present = not keys_present
    some_keys_present = keys_present and not all_keys_present
    assert ((all_keys_present or no_keys_present) and not some_keys_present)

    if request.method == 'POST' and (('nextState' in request.POST and no_keys_present) or (not session_information)):
        # session has expired
        return False
    return True


def recommender_state_machine(request):
    if not session_is_valid(request):
        # session has expired
        # display message that the session has expired
        # and go to select filters after 3s..
        request.session['in_system'] = None
        return render(request, 'modulo/recommender_session_expired.html')

    if request.method == 'POST' and 'nextState' in request.POST:
        session_current_state = UserState.from_string(request.POST['nextState'])
        session_previous_state = UserState(request.session.get('current_state', 0))
        request.session['next_state'] = UserState.from_string(request.POST['nextState']).value

        if not validate_session_state(session_current_state, session_previous_state):
            request.session['current_state'] = UserState.SELECT_FILTERS.value
            request.session['next_state'] = UserState.SELECT_FILTERS.value
            raise Http404(
                "Invalid state transition..." + "\nCurrent state: " + session_current_state.to_string() + "\nPrevious state: " + session_previous_state.to_string() + "\n")
        else:
            response = HttpResponseRedirect(reverse('modulo:modulo-recommender'))

    else:
        session_current_state = UserState(request.session.get('next_state', 0))
        session_previous_state = UserState(request.session.get('current_state', 0))

        state = session_current_state
        prev_state = session_previous_state

        if not validate_session_state(state, prev_state):
            request.session['current_state'] = UserState.SELECT_FILTERS.value
            request.session['next_state'] = UserState.SELECT_FILTERS.value
            raise Http404(
                "Invalid state transition in get method..." + "\nCurrent state: " + state.to_string() + "\nPrevious state: " + prev_state.to_string() + "\n")

        if state == UserState.SELECT_FILTERS:
            response = recommender_select_filters(request, state)
        elif state == UserState.DISPLAY_MODULES:
            response = recommender_display_modules(request, state)
        elif state == UserState.UPDATE_FILTERS:
            response = recommender_update_filters(request, state)
        elif state == UserState.SEE_FEEDBACK:
            response = recommender_see_feedback(request, state)
        elif state == UserState.THANKS:
            response = recommender_thanks(request, state)

    return response


def recommender_select_filters(request, state):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        if 'moduleForm' in request.POST:
            form = ModuleForm(request.POST)
        elif 'advancedForm' in request.POST:
            form = AdvancedRecommenderForm(request.POST)
        else:
            form = None

        # check whether it's valid:
        if form.is_valid():
            global id_counter
            rec = process_form(form, Recommender(id=id_counter))
            request.session['recommendation'] = json.dumps(rec, cls=HandleRecommender)
            request.session['reg_log'] = ""
            request.session['modules'] = None
            request.session['module_display_indices'] = None
            request.session['module_remaining_indices'] = None
            request.session['detailed_views'] = None
            request.session['module_details'] = None
            request.session['feedback'] = None
            request.session['advancedForm'] = isinstance(form, AdvancedRecommenderForm)
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.DISPLAY_MODULES.value
            # request.session.set_expiry(3600)  # expires after 1h = 3600s
            request.session.set_expiry(300)  # expires after 5min = 300s
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))
        else:
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.SELECT_FILTERS.value
            template_args = {'state': state.value, 'selectFilters': UserState.SELECT_FILTERS.value}
            if isinstance(form, AdvancedRecommenderForm):
                template_args.update({'moduleForm': ModuleForm(), 'advancedForm': form, 'advanced': True})
            elif isinstance(form, ModuleForm):
                template_args.update({'moduleForm': form, 'advancedForm': AdvancedRecommenderForm(), 'advanced': False})
            return render(request, 'modulo/recommender_selectFilters.html', template_args)

    # if a GET we'll create two blank forms (one simple form and one advanced form)
    elif request.method == 'GET':
        module_form = ModuleForm()
        advanced_form = AdvancedRecommenderForm()
        request.session['current_state'] = state.value
        request.session['next_state'] = UserState.SELECT_FILTERS.value
        template_args = {'moduleForm': module_form, 'advancedForm': advanced_form, 'state': state.value,
                         'selectFilters': UserState.SELECT_FILTERS.value}
        return render(request, 'modulo/recommender_selectFilters.html', template_args)

    else:
        raise Http404("Unknown method for request %s" % request)


def recommender_display_modules(request, state):
    rec = Recommender.get_recommendation_from_json(request.session['recommendation'])

    if request.method == 'POST':
        assert (request.session['modules'] is not None and
                request.session['module_display_indices'] is not None and
                request.session['detailed_views'] is not None and
                request.session['module_details'] is not None and
                request.session['rec_log'] is not None)
        modules = Module.get_modules_from_json(request.session['modules'])
        display_indices = request.session['module_display_indices']
        detailed_views = request.session['detailed_views']
        module_details = request.session['module_details']
        modules_dict = request.session['feedback']
        recommendation_log = request.session['rec_log']

        if 'submitFeedback' in request.POST:
            submit_feedback(rec, modules_dict)
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.THANKS.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

        valid, data, module_button_pressed = \
            process_display_modules_post_data(request.POST, [modules[i] for i in display_indices])
        if not valid:
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.DISPLAY_MODULES.value
            '''
            error_msg = 'You must either select the module \"%s\", mark it as interesting or ' \
                        'mark it as a not-for-me module before submitting feedback for it!' % module_button_pressed
            '''
            error_msg = 'You must either mark the module \"%s\" as interesting or ' \
                        'as a not-for-me module before submitting feedback for it!' % module_button_pressed
            template_args = {'error_message': error_msg, 'modules': [modules[i] for i in display_indices],
                             'details': detailed_views, 'module_details': module_details,
                             'state': state.value, 'recommendation_log': recommendation_log,
                             'displayModules': UserState.DISPLAY_MODULES.value,
                             'updateFilters': UserState.UPDATE_FILTERS.value,
                             'seeFeedback': UserState.SEE_FEEDBACK.value}
            if modules_dict['selected_module'] is not None:
                template_args.update({'selected_module': modules_dict['selected_module']})
            return render(request, 'modulo/recommender_displayModules.html', template_args)

        if 'feedback' in data.keys():
            remaining_indices = request.session['module_remaining_indices']
            if data['feedback']['feedback_type'] == 'selected_module':
                if modules_dict['selected_module'] is not None and \
                                modules_dict['selected_module'] not in modules_dict['interesting_modules']:
                    modules_dict['interesting_modules'].append(modules_dict['selected_module'])
                modules_dict['selected_module'] = data['feedback']['module_title']
            else:
                modules_dict[data['feedback']['feedback_type']].append(data['feedback']['module_title'])
            if data['feedback']['module_title'] in detailed_views:
                detailed_views.remove(data['feedback']['module_title'])
                module_details.pop(data['feedback']['module_title'])
                request.session['detailed_views'] = detailed_views
                request.session['module_details'] = module_details

            # starts at 1; is the index from [1 to #displayedModules]
            del display_indices[data['feedback']['module_display_nr'] - 1]
            if remaining_indices:
                display_indices.append(remaining_indices[0])
                del remaining_indices[0]

            request.session['module_display_indices'] = display_indices
            request.session['module_remaining_indices'] = remaining_indices
            request.session['feedback'] = modules_dict
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.DISPLAY_MODULES.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

        if 'details' in data.keys():
            # get which module was clicked detail and mark it as seen and remove it from the list of not_seen_modules
            if data['details']['type'] == 'see':
                detailed_views.append(data['details']['module_title'])
                module_details[data['details']['module_title']] = \
                    Module.objects.get(title=data['details']['module_title']).module_details()
                if data['details']['module_title'] not in modules_dict['seen_modules']:
                    modules_dict['not_seen_modules'].remove(data['details']['module_title'])
                    modules_dict['seen_modules'].append(data['details']['module_title'])
            elif data['details']['type'] == 'hide':
                detailed_views.remove(data['details']['module_title'])
                module_details.pop(data['details']['module_title'])

            # print(module_details)
            request.session['detailed_views'] = detailed_views
            request.session['module_details'] = module_details
            request.session['feedback'] = modules_dict
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.DISPLAY_MODULES.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

    elif request.method == 'GET':
        if request.session['modules'] is None:
            assert (request.session['modules'] is None)
            assert (request.session['module_display_indices'] is None)
            assert (request.session['module_remaining_indices'] is None)
            assert (request.session['detailed_views'] is None)
            assert (request.session['module_details'] is None)
            assert (request.session['feedback'] is None)
            modules, recommendation_log = rec.recommend()
            display_indices = list(range(min(5, len(modules))))
            remaining_indices = [] if len(modules) == len(display_indices) else list(range(len(modules)))[5:]
            detailed_views = []
            module_details = {}
            modules_dict = {'selected_module': None, 'interesting_modules': [], 'not_for_me_modules': [],
                            'seen_modules': [], 'not_seen_modules': [m.title for m in modules]}

            request.session['recommendation'] = json.dumps(rec, cls=HandleRecommender)
            request.session['rec_log'] = recommendation_log
            request.session['modules'] = json.dumps(modules, cls=HandleModule)
            request.session['module_display_indices'] = display_indices
            request.session['module_remaining_indices'] = remaining_indices
            request.session['detailed_views'] = detailed_views
            request.session['module_details'] = module_details
            request.session['feedback'] = modules_dict
        else:
            recommendation_log = request.session['rec_log']
            modules = Module.get_modules_from_json(request.session['modules'])
            display_indices = request.session['module_display_indices']
            remaining_indices = request.session['module_remaining_indices']
            detailed_views = request.session['detailed_views']
            module_details = request.session['module_details']
            modules_dict = request.session['feedback']

        # print(module_details)
        request.session['current_state'] = state.value
        request.session['next_state'] = UserState.DISPLAY_MODULES.value
        template_args = {'modules': [modules[i] for i in display_indices], 'details': detailed_views,
                         'module_details': module_details, 'recommendation_log': recommendation_log,
                         'state': state.value, 'displayModules': UserState.DISPLAY_MODULES.value,
                         'updateFilters': UserState.UPDATE_FILTERS.value, 'seeFeedback': UserState.SEE_FEEDBACK.value}
        template_args.update({'feedback_provided': modules_dict['selected_module'] is not None or
                                                   modules_dict['interesting_modules'] != [] or
                                                   modules_dict['not_for_me_modules'] != []})
        if modules_dict['selected_module'] is not None:
            template_args.update({'selected_module': modules_dict['selected_module']})
        if len(modules) == 0:
            error_msg = "There are no modules matching your current filters. " \
                        "Try updating them using the button below!"
            template_args.update({'error_message': error_msg})
        elif len(display_indices) == 0:
            error_msg = "Thank you for providing feedback to every module. " \
                        "You can now review the provided feedback (SEE FEEDBACK) or directly submit the feedback " \
                        "so that the system can learn to make better recommendations! " \
                        "You can also change your recommendation filters, but this will clear the provided feedback " \
                        "from your current recommendation."
            template_args.update({'error_message': error_msg})
        return render(request, 'modulo/recommender_displayModules.html', template_args)

    else:
        raise Http404("Unknown method for request %s" % request)


def recommender_update_filters(request, state):
    rec = Recommender.get_recommendation_from_json(request.session['recommendation'])

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        if 'moduleForm' in request.POST:
            form = ModuleForm(request.POST)
        elif 'advancedForm' in request.POST:
            form = AdvancedRecommenderForm(request.POST)
        else:
            form = None

        # check whether it's valid:
        if form.is_valid():
            old_interests = copy.deepcopy(rec.interests)
            old_filters = copy.deepcopy(rec.filters)
            new_rec = process_form(form, rec)
            if old_filters != new_rec.filters or set(old_interests) != set(new_rec.interests):
                request.session['recommendation'] = json.dumps(rec, cls=HandleRecommender)
                request.session['modules'] = None
                request.session['module_display_indices'] = None
                request.session['module_remaining_indices'] = None
                request.session['detailed_views'] = None
                request.session['module_details'] = None
                request.session['feedback'] = None
                request.session['advancedForm'] = isinstance(form, AdvancedRecommenderForm)

            # redirect to a new URL:
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.DISPLAY_MODULES.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))
        else:
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.UPDATE_FILTERS.value
            template_args = {'state': state.value, 'updateFilters': UserState.UPDATE_FILTERS.value}
            if isinstance(form, AdvancedRecommenderForm):
                template_args.update(
                    {'moduleForm': ModuleForm(initial=ModuleForm.getInitialValuesFromRecommendation(rec)),
                     'advancedForm': form, 'advanced': True})
            elif isinstance(form, ModuleForm):
                template_args.update({'moduleForm': form, 'advancedForm': AdvancedRecommenderForm(
                    initial=AdvancedRecommenderForm.getInitialValuesFromRecommendation(rec)), 'advanced': False})
            return render(request, 'modulo/recommender_updateFilters.html', template_args)

    # if a GET we'll create two forms
    # with the initial values of the filters from the previous recommendation
    elif request.method == 'GET':
        module_form = ModuleForm(initial=ModuleForm.getInitialValuesFromRecommendation(rec))
        advanced_form = AdvancedRecommenderForm(initial=AdvancedRecommenderForm.getInitialValuesFromRecommendation(rec))
        request.session['current_state'] = state.value
        request.session['next_state'] = UserState.UPDATE_FILTERS.value
        template_args = {'moduleForm': module_form, 'advancedForm': advanced_form,
                         'advanced': request.session['advancedForm'], 'state': state.value,
                         'updateFilters': UserState.UPDATE_FILTERS.value}
        return render(request, 'modulo/recommender_updateFilters.html', template_args)

    else:
        raise Http404("Unknown method for request %s" % request)


def recommender_see_feedback(request, state):
    rec = Recommender.get_recommendation_from_json(request.session['recommendation'])

    assert (request.session['feedback'] is not None)
    modules_dict = request.session['feedback']

    if not (modules_dict['selected_module'] or
                modules_dict['interesting_modules'] or
                modules_dict['not_for_me_modules']):
        request.session['current_state'] = state.value
        # request.session['next_state'] = UserState.DISPLAY_MODULES.value
        template_args = {'error_message': "You haven't selected any feedback to see.",
                         'next_action': [UserState.DISPLAY_MODULES.value], 'state': state.value}
        return render(request, 'modulo/recommender_error.html', template_args)

    if request.method == 'POST':
        valid, data, module_button_pressed = process_see_feedback_post_data(request.POST, modules_dict)
        if not valid:
            detailed_views = request.session['detailed_views']
            module_details = request.session['module_details']
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.SEE_FEEDBACK.value
            '''
            error_msg = 'Select a choice for module \"%s\" if you want to update its feedback!' % module_button_pressed
            '''
            error_msg = 'Before updating feedback on module \"%s\" please check another feedback option!' % module_button_pressed
            template_args = {'error_message': error_msg,
                             'details': detailed_views, 'module_details': module_details,
                             'seeFeedback': UserState.SEE_FEEDBACK.value,
                             'displayModules': UserState.DISPLAY_MODULES.value, 'state': state.value,
                             'selected_module': modules_dict['selected_module'],
                             'interesting_modules': modules_dict['interesting_modules'],
                             'not_for_me_modules': modules_dict['not_for_me_modules'],
                             'seen_modules': modules_dict['seen_modules'],
                             'not_seen_modules': modules_dict['not_seen_modules']}
            return render(request, 'modulo/recommender_seeFeedback.html', template_args)

        if 'submitFeedback' in data.keys():
            submit_feedback(rec, modules_dict)
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.THANKS.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

        if 'feedback' in data.keys():
            # update the modules_dict
            if data['feedback']['current_feedback'] == 'interesting' and \
                            data['feedback']['new_feedback'] == 'selected':
                modules_dict['interesting_modules'].remove(data['feedback']['module_title'])
                modules_dict['interesting_modules'].append(modules_dict['selected_module']) \
                    if modules_dict['selected_module'] is not None else None
                modules_dict['selected_module'] = data['feedback']['module_title']
            elif data['feedback']['current_feedback'] == 'interesting' and \
                            data['feedback']['new_feedback'] == 'not_for_me':
                modules_dict['interesting_modules'].remove(data['feedback']['module_title'])
                modules_dict['not_for_me_modules'].append(data['feedback']['module_title'])
            elif data['feedback']['current_feedback'] == 'not_for_me' and \
                            data['feedback']['new_feedback'] == 'selected':
                modules_dict['not_mor_me_modules'].remove(data['feedback']['module_title'])
                modules_dict['interesting_modules'].append(modules_dict['selected_module']) \
                    if modules_dict['selected_module'] is not None else None
                modules_dict['selected_module'] = data['feedback']['module_title']
            elif data['feedback']['current_feedback'] == 'not_for_me' and \
                            data['feedback']['new_feedback'] == 'interesting':
                modules_dict['not_for_me_modules'].remove(data['feedback']['module_title'])
                modules_dict['interesting_modules'].append(data['feedback']['module_title'])
            elif data['feedback']['current_feedback'] == 'selected' and \
                            data['feedback']['new_feedback'] == 'interesting':
                modules_dict['selected_module'] = None
                modules_dict['interesting_modules'].append(data['feedback']['module_title'])
            else:
                raise Exception("Invalid feedback transition!")

            request.session['feedback'] = modules_dict
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.SEE_FEEDBACK.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

        if 'details' in data.keys():
            detailed_views = request.session['detailed_views']
            module_details = request.session['module_details']

            # print(module_details)
            # show/hide details
            if data['details']['type'] == 'see':
                detailed_views.append(data['details']['module_title'])
                module_details[data['details']['module_title']] = \
                    Module.objects.get(title=data['details']['module_title']).module_details()
                if data['details']['module_title'] not in modules_dict['seen_modules']:
                    modules_dict['not_seen_modules'].remove(data['details']['module_title'])
                    modules_dict['seen_modules'].append(data['details']['module_title'])
            elif data['details']['type'] == 'hide':
                detailed_views.remove(data['details']['module_title'])
                module_details.pop(data['details']['module_title'])
            # print(module_details)

            request.session['detailed_views'] = detailed_views
            request.session['module_details'] = module_details
            request.session['feedback'] = modules_dict
            request.session['current_state'] = state.value
            request.session['next_state'] = UserState.SEE_FEEDBACK.value
            return HttpResponseRedirect(reverse('modulo:modulo-recommender'))

    elif request.method == 'GET':
        detailed_views = request.session['detailed_views']
        module_details = request.session['module_details']
        # print(module_details)
        request.session['current_state'] = state.value
        request.session['next_state'] = UserState.SEE_FEEDBACK.value
        template_args = {'details': detailed_views, 'module_details': module_details,
                         'seeFeedback': UserState.SEE_FEEDBACK.value,
                         'displayModules': UserState.DISPLAY_MODULES.value, 'state': state.value,
                         'selected_module': modules_dict['selected_module'],
                         'interesting_modules': modules_dict['interesting_modules'],
                         'not_for_me_modules': modules_dict['not_for_me_modules'],
                         'seen_modules': modules_dict['seen_modules'],
                         'not_seen_modules': modules_dict['not_seen_modules']}
        return render(request, 'modulo/recommender_seeFeedback.html', template_args)

    else:
        raise Http404("Unknown method for request %s" % request)


def recommender_thanks(request, state):
    # print("This session contains:")
    # print_session_content(request.session)
    request.session.flush()
    request.session['in_system'] = None
    template_args = {'state': state.value, 'selectFilters': UserState.SELECT_FILTERS.value}
    return render(request, 'modulo/recommender_thanks.html', template_args)


def initialize():
    global allowed_transitions, id_counter
    allowed_transitions = [
        # initial transition
        (None, UserState.SELECT_FILTERS),
        (UserState.SELECT_FILTERS, UserState.SELECT_FILTERS),
        (UserState.THANKS, UserState.SELECT_FILTERS),

        (UserState.SELECT_FILTERS, UserState.DISPLAY_MODULES),
        (UserState.DISPLAY_MODULES, UserState.DISPLAY_MODULES),
        (UserState.UPDATE_FILTERS, UserState.DISPLAY_MODULES),
        (UserState.SEE_FEEDBACK, UserState.DISPLAY_MODULES),

        (UserState.UPDATE_FILTERS, UserState.UPDATE_FILTERS),
        (UserState.DISPLAY_MODULES, UserState.UPDATE_FILTERS),

        (UserState.DISPLAY_MODULES, UserState.SEE_FEEDBACK),
        (UserState.SEE_FEEDBACK, UserState.SEE_FEEDBACK),

        (UserState.SEE_FEEDBACK, UserState.THANKS),
        (UserState.DISPLAY_MODULES, UserState.THANKS)
    ]
    id_counter = 0
    print("views_recommender initialized")
