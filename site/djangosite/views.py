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
    output = None
    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            db = CatDB()
            output = db.get_course(subject = form.cleaned_data['subject'], 
                course_number = form.cleaned_data['course_number'])
    else:
        form = CourseNumberForm()
    return render(request, "course_search.html", {'form': form, 'output': output})
    
def jquery(request):
    return render(request, "jQueryDemo.html")