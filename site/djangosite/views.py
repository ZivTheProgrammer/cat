from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from forms import *
import CASClient
import re
from CatDB import CatDB

DISTRIBUTION_AREAS = ['EM', 'EC', 'HA', 'LA', 'QR', 'SA', 'STN', 'STL']

def home(request):
    return render(request, "hello_world.html")

# Handle user login. Non-functional at the moment.    
def login(request):
    C = CASClient.CASClient()
    netid = C.Authenticate()
    return HttpResponse(netid)

def index(request):
    db = CatDB()
    student = db.get_student("bbaggins")
    list = student['courseList']
    courses = db.get_course(course_id= list)
    for result in courses:
        result = annotate(db, result)
    return render(request, "index.html", {'distrib': DISTRIBUTION_AREAS, 'courses': courses})

# Get search results and pass them back to the search page.
def search_results(request):
    # Used to keep track of result versus cart courses
    classified = {}
    # Load courses in search results
    query = parse(request.POST['text'])
    db = CatDB()
    output = db.get_course(**query)
    for result in output:
        result = annotate(db, result)
        result['source'] = 'results'
        classified[result['course_id']] = result
    # Load courses in cart
    student = db.get_student("bbaggins")
    list = student['courseList']
    courses = db.get_course(course_id= list)
    for result in courses:
        result = annotate(db, result)
        if result['course_id'] in classified:
            classified[result['course_id']]['source'] = 'both'
        else:
            result['source'] = 'cart'
            classified[result['course_id']] = result
    return render(request, "search_results.html", {'results': classified})
    
# Get a new semester and pass it back to the search page.
def get_semester(request):
    db = CatDB()
    result = db.get_course({"course_id": request.GET['course_id']})[0]
    result['term'] = request.GET['semester'] # For testing!
    result = annotate(db, result)
    return render(request, "get_semester.html", {'result': result})

# Add a course to the user's course cart.
def add_course_cart(request):
    db = CatDB()
    print request.POST
    db.add_course("bbaggins", request.POST['course_id'])
    return render(request, "cart_course.html", {'course_id': request.POST['course_id']})
    
# Remove a course from the user's course cart.  
def remove_course_cart(request):
    db = CatDB()
    db.remove_course("bbaggins", request.POST['course_id'])
    return HttpResponse("Success") #Shouldn't need to return anything
    
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
        elif term_no % 10 == 1:
            semester['term_name'] = "Summer {:d}".format(1899 + term_no / 10)
    return semester

# Helper function to interpret the OMNIBAR(tm).
def parse(text):
    tokens = text.upper().split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': [], 'pdf': []}
    previous = {}
    for token in tokens:
        print token #For testing... remember to remove this eventually!
        # Match distribution requirement codes
        if token in DISTRIBUTION_AREAS:
            output['distribution'].append(token)
        # Match subject codes
        elif re.match('^[A-Z]{3}$', token):
            output['subject'].append(token)
        # Match course numbers
        elif re.match('^[0-9]{3}$', token):
            output['course_number'].append(token)
        elif re.match('^>[0-9]{3}$', token):
            output['min_course_number'] = token[1:]
        elif re.match('^<[0-9]{3}$', token):
            output['max_course_number'] = token[1:]
        # Match professor names
        elif re.match('^[A-Z]+$', token):
            output['professor_name'].append(token)
        # Match PDF criteria
        elif re.match('^NO-AUDIT$', token):
            output['pdf'].append('na')
        elif re.match('^NO-PDF$', token):
            output['pdf'].append('npdf')
        elif re.match('^PDF-ONLY$', token):
            output['pdf'].append('pdfonly')
    return output