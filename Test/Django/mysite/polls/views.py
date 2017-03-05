# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse

from .models import Question, Choice

def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template('polls/index.html')
    output = ', '.join([q.question_text for q in latest_question_list])
    context = { 'latest_question_list': latest_question_list }
    #response = HttpResponse("Hello, world. You're at the polls index.")
    #response = HttpResponse(output);
    #response = HttpResponse(template.render(context, request))
    response = render(request, 'polls/index.html', context);
    return response
	
def detail(request, question_id):
    '''
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    '''
    question = get_object_or_404(Question, pk=question_id)
    #response = HttpResponse("You're looking at question %s." % question_id)
    response = render(request, 'polls/detail.html', {'question': question})
    return response

def results(request, question_id):
    #response = HttpResponse("You're looking at the results of question %s." % question_id)
    question = get_object_or_404(Question, pk=question_id)
    response = render(request, 'polls/results.html', {'question': question})
    return response

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form with the error_message.
        return render(request, 'polls/detail.html', { 'question': question, 'error_message': "You didn't select a choice.", })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing with POST data. 
        # This prevents data from being posted twice if a user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))