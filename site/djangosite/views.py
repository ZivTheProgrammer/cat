from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
import CASClient

def home(request):
    return render_to_response("hello_world.html")
    
def login(request):
    C = CASClient.CASClient()
    netid = C.Authenticate()
    return HttpResponse(netid)