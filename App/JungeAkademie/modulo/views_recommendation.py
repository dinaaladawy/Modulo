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
import copy, enum, json, re

#list containing dictionary {recommendation, recommended_modules, display_indices, detailed_indices, feedback}
activeRequestList = None
allowed_transitions = None
id_counter = None

class UserState(enum.Enum):
    SELECT_FILTERS = 0
    DISPLAY_MODULES = 1
    UPDATE_FILTERS = 2
    SEE_FEEDBACK = 3
    THANKS = 4

def getRequestFromActiveRequests(request_id):
    global activeRequestList
    r = r'"id": '+str(request_id)+r'[,}]' #pattern to find in recommendation json_object
    for req in activeRequestList[:]:
        if re.search(r, req['recommendation']):
            return req
    return None
    
def validateState(current_state, previous_state, request_id):
    global allowed_transitions
    if not (previous_state, current_state) in allowed_transitions:
        return False
    if request_id is None and current_state in [UserState.DISPLAY_MODULES, UserState.UPDATE_FILTERS, UserState.SEE_FEEDBACK]:
        return False
    return True

def processForm(form, rec):
    # process the data in form.cleaned_data as required
    rec.updateFilters(timeInterval=form.processTime(), credits=form.processCredits(), exam_types=form.processExam(), locations=form.processLocation(), interests=form.processInterests())
    return rec

def processDisplayModulesPostData(post_data, displayed_modules):
    valid = False
    data = {}
    keys = list(post_data.keys())
    moduleButtonPressed = displayed_modules[int(keys[['submit' in key for key in keys].index(True)].split('submit')[1]) - 1] if any(['submit' in key for key in keys]) else None
    mods = ['module' in key for key in keys]
    dets = ['details' in key for key in keys]
    if any(mods) and mods.count(True) == 1:
        valid = True
        d = {}
        module_key = keys[mods.index(True)]
        module_index = int(module_key.split('module')[1])
        d['module_display_Nr'] = module_index #starting at 1 not at 0
        module = displayed_modules[module_index - 1]
        d['module_title'] = module.title
        if post_data[module_key] == 'selected':
            d['feedbackType'] = 'selectedModule'
        elif post_data[module_key] == 'interesting':
            d['feedbackType'] = 'interestingModules'
        elif post_data[module_key] == 'not-for-me':
            d['feedbackType'] = 'notForMeModules'
        else:
            raise Exception('Unknown feedback received...')
        data['feedback'] = d
    if any(dets):
        valid = True
        d = {}
        details_key = keys[dets.index(True)]
        details_index = int(details_key.split('details')[1])
        d['module_display_Nr'] = details_index #starting at 1 not at 0
        module = displayed_modules[details_index - 1]
        d['module_title'] = module.title
        d['type'] = 'see' if post_data[details_key]=='More details' else 'hide'
        data['details'] = d
    return valid, data, moduleButtonPressed

def processSeeFeedbackPostData(post_data, module_dict):
    valid = False
    data = {}
    keys = list(post_data.keys())
    moduleButtonPressed = keys[['submit' in key for key in keys].index(True)].split('submit')[1] if any(['submit' in key for key in keys]) else None
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
        d['type'] = 'see' if post_data[details_key]=='More details' else 'hide'
        data['details'] = d
    return valid, data, moduleButtonPressed

def recommender_state_machine(request, state='0', prev_state=None, request_id=None):
    state = UserState(int(state))
    if prev_state is not None:
        prev_state = UserState(int(prev_state))
    if request_id is not None:
        request_id = int(request_id)
        
    if not validateState(state, prev_state, request_id):
        raise Http404("Invalid state transition..."+"\nCurrent state: "+str(state)+"\nPrevious state: "+str(prev_state)+"\nrequest_id: "+str(request_id))
    
    if state == UserState.SELECT_FILTERS:
        return recommender_selectFilters(request, state)
    elif state == UserState.DISPLAY_MODULES:
        return recommender_displayModules(request, state, prev_state, request_id)
    elif state == UserState.UPDATE_FILTERS:
        return recommender_updateFilters(request, state, request_id)
    elif state == UserState.SEE_FEEDBACK:
        return recommender_seeFeedback(request, state, request_id)
    elif state == UserState.THANKS:
        return recommender_thanks(request, state)
    pass

def recommender_selectFilters(request, state):
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
            global activeRequestList, id_counter
            rec = processForm(form, Recommender(id=id_counter))
            request_info = {'recommendation': json.dumps(rec, cls=HandleRecommender), 
                            'modules': None, 
                            'module_display_indices': None, 
                            'module_remaining_indices': None, 
                            'detailed_views': None, 
                            'feedback': None,
                            'advancedForm': isinstance(form, AdvancedRecommenderForm)}
            activeRequestList.append(request_info)
            id_counter += 1
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.DISPLAY_MODULES.value, state.value, rec.id]))
        else:
            template_args = {'state': state.value, 'selectFilters': UserState.SELECT_FILTERS.value}
            if isinstance(form, AdvancedRecommenderForm):
                template_args.update({'moduleForm': ModuleForm(), 'advancedForm': form, 'advanced': True})
            elif isinstance(form, ModuleForm):
                template_args.update({'moduleForm': form, 'advancedForm': AdvancedRecommenderForm(), 'advanced': False})
            return render(request, 'modulo/recommender_selectFilters.html', template_args)

    # if a GET we'll create two blank forms (one simple form and one advanced form)
    elif request.method == 'GET':
        moduleForm = ModuleForm()
        advancedForm = AdvancedRecommenderForm()
        template_args = {'moduleForm': moduleForm, 'advancedForm': advancedForm, 'state': state.value, 'selectFilters': UserState.SELECT_FILTERS.value}
        return render(request, 'modulo/recommender_selectFilters.html', template_args)
    
    else:
        raise Http404("Unknown method for request %s" % request)

def recommender_displayModules(request, state, prev_state, request_id):
    request_info = getRequestFromActiveRequests(request_id)
    if request_info is None:
        global activeRequestList, id_counter
        #print("id_counter: ", id_counter)
        #print("request list: ", activeRequestList)
        request_string = (request.META['SERVER_NAME']+":"+request.META['SERVER_PORT']+request.path)
        return render(request, 'modulo/recommender_error.html', {'error_msg': "No recommendation available with id %d at request %s" % (request_id, request_string)})
    else:
        rec = Recommender.get_recommendation_from_json(request_info['recommendation'])
    
    if request.method == 'POST':
        assert(request_info['modules'] is not None and request_info['module_display_indices'] is not None and request_info['detailed_views'] is not None)
        modules = Module.get_modules_from_json(request_info['modules'])
        display_indices = json.loads(request_info['module_display_indices'])
        detailed_views = json.loads(request_info['detailed_views'])
        modules_dict = json.loads(request_info['feedback'])
        
        valid, data, moduleButtonPressed = processDisplayModulesPostData(request.POST, [modules[i] for i in display_indices])
        if not valid:
            error_msg = 'You must either select the module "%s", mark it as interesting or mark it as a not-for-me module before submitting feedback for it!' % moduleButtonPressed
            template_args = {'error_message': error_msg, 'id': request_id, 'modules': [modules[i] for i in display_indices], 'details': detailed_views, 'state': state.value, 'displayModules': UserState.DISPLAY_MODULES.value, 'updateFilters': UserState.UPDATE_FILTERS.value, 'seeFeedback': UserState.SEE_FEEDBACK.value}
            if modules_dict['selectedModule'] is not None:
                template_args.update({'selected_module': modules_dict['selectedModule']})
            return render(request, 'modulo/recommender_displayModules.html', template_args)
            
        if 'feedback' in data.keys():
            remaining_indices = json.loads(request_info['module_remaining_indices'])
            if data['feedback']['feedbackType'] == 'selectedModule':
                if modules_dict['selectedModule'] is not None and modules_dict['selectedModule'] not in modules_dict['interestingModules']:
                    modules_dict['interestingModules'].append(modules_dict['selectedModule'])
                modules_dict['selectedModule'] = data['feedback']['module_title']
            else:
                modules_dict[data['feedback']['feedbackType']].append(data['feedback']['module_title'])
            if data['feedback']['module_title'] in detailed_views:
                   detailed_views.remove(data['feedback']['module_title'])
                   request_info['detailed_views'] = json.dumps(detailed_views)
            
            del display_indices[data['feedback']['module_display_Nr'] - 1] # starts at 1; is the index from [1 to #displayedModules]
            if remaining_indices:
                display_indices.append(remaining_indices[0])
                del remaining_indices[0]
            
            request_info['module_display_indices'] = json.dumps(display_indices)
            request_info['module_remaining_indices'] = json.dumps(remaining_indices)
            request_info['feedback'] = json.dumps(modules_dict)        
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.DISPLAY_MODULES.value, state.value, request_id]))
 
        if 'details' in data.keys():
            #get which module was clicked detail and mark it as seen and remove it from the list of notSeenModules
            if data['details']['type'] == 'see':
                detailed_views.append(data['details']['module_title'])
                if data['details']['module_title'] not in modules_dict['seenModules']:
                    modules_dict['notSeenModules'].remove(data['details']['module_title'])
                    modules_dict['seenModules'].append(data['details']['module_title'])
            elif data['details']['type'] == 'hide':
                detailed_views.remove(data['details']['module_title'])
            
            request_info['detailed_views'] = json.dumps(detailed_views)
            request_info['feedback'] = json.dumps(modules_dict)
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.DISPLAY_MODULES.value, state.value, request_id]))
    
    elif request.method == 'GET':
        if request_info['modules'] is None:
            assert(request_info['module_display_indices'] is None)
            assert(request_info['module_remaining_indices'] is None)
            assert(request_info['detailed_views'] is None)
            assert(request_info['feedback'] is None)
            modules = rec.recommend()
            display_indices = list(range(min(5, len(modules))))
            remaining_indices = [] if len(modules) == len(display_indices) else list(range(len(modules)))[5:]
            detailed_views = []
            modules_dict = {'selectedModule': None, 'interestingModules': [], 'notForMeModules': [], 'seenModules': [], 'notSeenModules': [m.title for m in modules]}
            
            request_info['recommendation'] = json.dumps(rec, cls=HandleRecommender) #update recommendation (categories are included in the filters...)
            request_info['modules'] = json.dumps(modules, cls=HandleModule)
            request_info['module_display_indices'] = json.dumps(display_indices)
            request_info['module_remaining_indices'] = json.dumps(remaining_indices)
            request_info['detailed_views'] = json.dumps(detailed_views)
            request_info['feedback'] = json.dumps(modules_dict)
        
        else:
            modules = Module.get_modules_from_json(request_info['modules'])
            display_indices = json.loads(request_info['module_display_indices'])
            remaining_indices = json.loads(request_info['module_remaining_indices'])
            detailed_views = json.loads(request_info['detailed_views'])
            modules_dict = json.loads(request_info['feedback'])
            
        template_args = {'id': request_id, 'modules': [modules[i] for i in display_indices], 'details': detailed_views, 'state': state.value, 'displayModules': UserState.DISPLAY_MODULES.value, 'updateFilters': UserState.UPDATE_FILTERS.value, 'seeFeedback': UserState.SEE_FEEDBACK.value}
        if modules_dict['selectedModule'] is not None:
            template_args.update({'selected_module': modules_dict['selectedModule']})
        if len(modules) == 0:
            error_msg = "There are no modules which match your current filters. Try updating them using the button below!"
            template_args.update({'error_message': error_msg})
        elif len(display_indices) == 0:
            error_msg = "Thank you for providing feedback to every module. You can now review the provided feedback (SEE FEEDBACK) and from there submit it so that the system can learn to make better recommendations!"
            template_args.update({'error_message': error_msg})
        return render(request, 'modulo/recommender_displayModules.html', template_args)
    
    else:
        raise Http404("Unknown method for request %s" % request)

def recommender_updateFilters(request, state, request_id):
    request_info = getRequestFromActiveRequests(request_id)
    if request_info is None:
        global activeRequestList, id_counter
        #print(id_counter)
        #print(activeRequestList)
        request_string = (request.META['SERVER_NAME']+":"+request.META['SERVER_PORT']+request.path)
        return render(request, 'modulo/recommender_error.html', {'error_msg': "No recommendation available with id %d at request %s" % (request_id, request_string)})
    else:
        rec = Recommender.get_recommendation_from_json(request_info['recommendation'])
    
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
            oldInterests = copy.deepcopy(rec.interests)
            oldFilters = copy.deepcopy(rec.filters)
            newRec = processForm(form, rec)
            if oldFilters != newRec.filters or set(oldInterests) != set(newRec.interests):
                request_info['recommendation'] = json.dumps(newRec, cls=HandleRecommender)
                request_info['modules'] = None
                request_info['module_display_indices'] = None
                request_info['module_remaining_indices'] = None
                request_info['detailed_views'] = None
                request_info['feedback'] = None
                request_info['advancedForm'] = isinstance(form, AdvancedRecommenderForm)
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.DISPLAY_MODULES.value, state.value, request_id]))
        
        else:
            template_args = {'id': request_id, 'state': state.value, 'updateFilters': UserState.UPDATE_FILTERS.value}
            if isinstance(form, AdvancedRecommenderForm):
                template_args.update({'moduleForm': ModuleForm(initial=ModuleForm.getInitialValuesFromRecommendation(rec)), 'advancedForm': form, 'advanced': True})
            elif isinstance(form, ModuleForm):
                template_args.update({'moduleForm': form, 'advancedForm': AdvancedRecommenderForm(initial=AdvancedRecommenderForm.getInitialValuesFromRecommendation(rec)), 'advanced': False})
            return render(request, 'modulo/recommender_updateFilters.html', template_args)

    # if a GET we'll create two forms
    # with the initial values of the filters from the previous recommendation
    elif request.method == 'GET':
        moduleForm = ModuleForm(initial=ModuleForm.getInitialValuesFromRecommendation(rec))
        advancedForm = AdvancedRecommenderForm(initial=AdvancedRecommenderForm.getInitialValuesFromRecommendation(rec))
        template_args = {'moduleForm': moduleForm, 'advancedForm': advancedForm, 'advanced': request_info['advancedForm'], 'id': request_id, 'state': state.value, 'updateFilters': UserState.UPDATE_FILTERS.value}
        return render(request, 'modulo/recommender_updateFilters.html', template_args)
    
    else:
        raise Http404("Unknown method for request %s" % request)

def recommender_seeFeedback(request, state, request_id):
    request_info = getRequestFromActiveRequests(request_id)
    if request_info is None:
        request_string = (request.META['SERVER_NAME']+":"+request.META['SERVER_PORT']+request.path)
        return render(request, 'modulo/recommender_error.html', {'error_msg': "No recommendation available with id %d at request %s" % (request_id, request_string)})
    else:
        rec = Recommender.get_recommendation_from_json(request_info['recommendation'])
    
    assert(request_info['feedback'] is not None)
    modules_dict = json.loads(request_info['feedback'])
    
    if not (modules_dict['selectedModule'] or modules_dict['interestingModules'] or modules_dict['notForMeModules']):
        return render(request, 'modulo/recommender_error.html', {'error_msg': "You haven't selected any feedback to see.", 'next_action': [UserState.DISPLAY_MODULES.value], 'state': state.value, 'id': request_id})
    
    if request.method == 'POST':
        valid, data, moduleButtonPressed = processSeeFeedbackPostData(request.POST, modules_dict)
        if not valid:
            detailed_views = json.loads(request_info['detailed_views'])
            error_msg = 'Select a choice for module %s if you want to update its feedback!' % moduleButtonPressed
            return render(request, 'modulo/recommender_seeFeedback.html', {'error_message': error_msg, 'details': detailed_views, 'seeFeedback': UserState.SEE_FEEDBACK.value, 'displayModules': UserState.DISPLAY_MODULES.value, 'state': state.value, 'id': request_id, 'selected_module': modules_dict['selectedModule'], 'interesting_modules': modules_dict['interestingModules'], 'not_for_me_modules': modules_dict['notForMeModules'], 'seen_modules': modules_dict['seenModules'], 'not_seen_modules': modules_dict['notSeenModules']})
        
        if 'submitFeedback' in data.keys():
            #incorporate feedback into the system
            f = Feedback(recommendation=rec);
            f.updateFeedback(**modules_dict)
            f.setFeedback()
            activeRequestList.remove(request_info)
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.THANKS.value, state.value]))
        
        if 'feedback' in data.keys():
            #update the modules_dict
            if data['feedback']['current_feedback'] == 'interesting' and data['feedback']['new_feedback'] == 'selected':
                modules_dict['interestingModules'].remove(data['feedback']['module_title'])
                modules_dict['interestingModules'].append(modules_dict['selectedModule']) if modules_dict['selectedModule'] is not None else None
                modules_dict['selectedModule'] = data['feedback']['module_title']
                
            elif data['feedback']['current_feedback'] == 'interesting' and data['feedback']['new_feedback'] == 'not_for_me':
                modules_dict['interestingModules'].remove(data['feedback']['module_title'])
                modules_dict['notForMeModules'].append(data['feedback']['module_title'])
            elif data['feedback']['current_feedback'] == 'not_for_me' and data['feedback']['new_feedback'] == 'selected':
                modules_dict['notForMeModules'].remove(data['feedback']['module_title'])
                modules_dict['interestingModules'].append(modules_dict['selectedModule']) if modules_dict['selectedModule'] is not None else None
                modules_dict['selectedModule'] = data['feedback']['module_title']
            elif data['feedback']['current_feedback'] == 'not_for_me' and data['feedback']['new_feedback'] == 'interesting':
                modules_dict['notForMeModules'].remove(data['feedback']['module_title'])
                modules_dict['interestingModules'].append(data['feedback']['module_title'])
            elif data['feedback']['current_feedback'] == 'selected' and data['feedback']['new_feedback'] == 'interesting':
                modules_dict['selectedModule'] = None
                modules_dict['interestingModules'].append(data['feedback']['module_title'])
            else:
                raise Exception("Invalid feedback transition!")
                
            request_info['feedback'] = json.dumps(modules_dict)
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.SEE_FEEDBACK.value, state.value, request_id]))
        
        if 'details' in data.keys():
            detailed_views = json.loads(request_info['detailed_views'])
            #show/hide details
            if data['details']['type'] == 'see':
                detailed_views.append(data['details']['module_title'])
                if data['details']['module_title'] not in modules_dict['seenModules']:
                    modules_dict['notSeenModules'].remove(data['details']['module_title'])
                    modules_dict['seenModules'].append(data['details']['module_title'])
            elif data['details']['type'] == 'hide':
                detailed_views.remove(data['details']['module_title'])
            
            request_info['detailed_views'] = json.dumps(detailed_views)
            request_info['feedback'] = json.dumps(modules_dict)
            return HttpResponseRedirect(reverse('modulo:modulo-recommender', args=[UserState.SEE_FEEDBACK.value, state.value, request_id]))

    elif request.method == 'GET':
        detailed_views = json.loads(request_info['detailed_views'])
        return render(request, 'modulo/recommender_seeFeedback.html', {'details': detailed_views, 'seeFeedback': UserState.SEE_FEEDBACK.value, 'displayModules': UserState.DISPLAY_MODULES.value, 'state': state.value, 'id': request_id, 'selected_module': modules_dict['selectedModule'], 'interesting_modules': modules_dict['interestingModules'], 'not_for_me_modules': modules_dict['notForMeModules'], 'seen_modules': modules_dict['seenModules'], 'not_seen_modules': modules_dict['notSeenModules']})
    
    else:
        raise Http404("Unknown method for request %s" % request)
    
def recommender_thanks(request, state):
    return render(request, 'modulo/recommender_thanks.html', {'state': state.value, 'selectFilters': UserState.SELECT_FILTERS.value})

def initialize():
    global activeRequestList, allowed_transitions, id_counter
    activeRequestList = []
    id_counter = 0
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
        
        (UserState.SEE_FEEDBACK, UserState.THANKS)
    ]
    print("views_recommender initialized")