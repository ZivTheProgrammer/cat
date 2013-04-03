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

def index(request):
    return render(request, "index.html")
    
# Display the main search page.
def course_search(request):
    form = CourseNumberForm()
    return render(request, "course_search.html", {'form': form})

# Get search results and pass them back to the search page.
def search_results(request):
    output = None
    query = parse(request.POST['text'])
    db = CatDB()
    output = db.get_course(**query)
    list = [result for result in output]
    print list
    return render(request, "search_results.html", {'output': list})
    
# Helper function to interpret the OMNIBAR(tm).
def parse(text):
    tokens = text.lower().split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': []}
    previous = {}
    for token in tokens:
        print token
        # Match subject codes
        if re.match('^[a-z]{3}$', token):
            output['subject'].append(token)
        # Match distribution requirement codes
        elif re.match('^[a-z]{2}$', token):
            output['distribution'].append(token)
        # Match course numbers
        elif re.match('^[0-9]{3}$', token):
            output['course_number'].append(token)
        # Match professor names
        elif re.match('^[a-z]+$', token):
            output['professor_name'].append(token)
    return output