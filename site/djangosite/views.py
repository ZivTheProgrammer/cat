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
    for result in list:
        result = annotate(db, result)
    return render(request, "search_results.html", {'output': list})
    
# Get a new semester and pass it back to the search page.
def get_semester(request):
    db = CatDB()
    result = db.get_course({"course_id": request.GET['course_id']})[0]
    result['term'] = u'1132' # For testing!
    result = annotate(db, result)
    return render(request, "get_semester.html", {'result': result})

# Helper function to add information to a semester of a course.
def annotate(db, semester):
    # Add instructor information
    if 'instructors' in semester:
        semester['profs'] = []
        for instructor in semester['instructors']:
            semester['profs'].append(db.get_professor(id_number=instructor)[0])
    # Add nice semester name
    if 'term' in semester:
        term_no = int(semester['term'])
        if term_no % 10 == 4:
            semester['term_name'] = "Spring {:d}".format(1900 + term_no / 10)
        elif term_no % 10 == 2:
            semester['term_name'] = "Fall {:d}".format(1899 + term_no / 10)
    return semester

# Helper function to interpret the OMNIBAR(tm).
def parse(text):
    tokens = text.lower().split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': []}
    previous = {}
    for token in tokens:
        print token
        # Match subject codes
        if re.match('^[a-z]{3}$', token):
            output['subject'].append(token.upper())
        # Match distribution requirement codes
        elif re.match('^[a-z]{2}$', token):
            output['distribution'].append(token.upper())
        # Match course numbers
        elif re.match('^[0-9]{3}$', token):
            output['course_number'].append(token)
        # Match professor names
        elif re.match('^[a-z]+$', token):
            output['professor_name'].append(token)
        # Match PDF criteria
        elif re.match('^no-audit$', token):
            output['pdf'] = 'na'
        elif re.match('^no-pdf$', token):
            output['pdf'] = 'npdf'
        elif re.match('^pdf-only$', token):
            output['pdf'] = 'pdfonly'
    return output