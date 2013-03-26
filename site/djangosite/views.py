from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from forms import *
import CASClient
from CatDB import CatDB

def home(request):
    return render(request, "hello_world.html")
    
def login(request):
    C = CASClient.CASClient()
    netid = C.Authenticate()
    return HttpResponse(netid)
    
def course_search(request):
    form = CourseNumberForm()
    return render(request, "course_search.html", {'form': form})

def search_results(request):
    output = None
    form = CourseNumberForm(request.POST)
    if form.is_valid():
        db = CatDB()
        output = db.get_course(subject = form.cleaned_data['subject'], 
            course_number = form.cleaned_data['course_number'])
    return render(request, "search_results.html", {'output': output})