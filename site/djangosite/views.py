from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from forms import *
import CASClient
import re
from CatDB import CatDB

def home(request):
    return render(request, "hello_world.html")

# Handle user login. Non-functional at the moment.    
def login(request):
    C = CASClient.CASClient()
    netid = C.Authenticate()
    return HttpResponse(netid)

# Display the main search page.
def course_search(request):
    form = CourseNumberForm()
    return render(request, "course_search.html", {'form': form})

# Get search results and pass them back to the search page.
def search_results(request):
    output = None
    form = CourseNumberForm(request.POST)
    if form.is_valid():
        text = form.cleaned_data['text']
        
        db = CatDB()
        output = db.get_course(subject = form.cleaned_data['subject'], 
            course_number = form.cleaned_data['course_number'])
    return render(request, "search_results.html", {'output': output})
    
# Helper function to interpret the OMNIBAR(tm).
def parse(text):
    tokens = text.split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': []}
    previous = {}
    for token in tokens:
        if token.match
        