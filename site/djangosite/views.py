from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect

def home(request):
    return render_to_response("hello_world.html")