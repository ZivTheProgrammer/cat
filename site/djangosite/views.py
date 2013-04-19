from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from forms import *
import CASClient
import re
from CatDB import CatDB
from collections import OrderedDict

DISTRIBUTION_AREAS = ['EM', 'EC', 'HA', 'LA', 'QR', 'SA', 'STN', 'STL']

def home(request):
    return render(request, "hello_world.html")

# Handle user login. Non-functional at the moment.    
def login(request):
    C = CASClient.CASClient()
    netid = C.Authenticate()
    return HttpResponse(netid)

# Base view for the site
def index(request):
    classified = {}
    db = CatDB()
    student = db.get_student("bbaggins")
    courses = student.get('courseList', [])
    courses = db.get_course(course_id = courses)
    for result in courses:
        result = annotate(db, result)
        result['source'] = 'cart'
        classified[result['course_id']] = result
    return render(request, "index.html", {'distrib': DISTRIBUTION_AREAS, 'courses': courses, 'results': classified})

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
    list = student.get('courseList', [])
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
    course = db.get_course({"course_id": request.GET['course_id']})[0]
    result = db.get_course({"subject": course['subject'], 
        "course_number": course['course_number'], 
        "term": request.GET['semester']})[0]
    result = annotate(db, result)
    return render(request, "get_semester.html", {'result': result})

# Add a course to the user's course cart.
def add_course_cart(request):
    db = CatDB()
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
    # Add nice semester names
    if 'term' in semester:
        term_no = int(semester['term'])
        semester['term_name'] = term_name(term_no)
    if 'all_terms' in semester:
        all_named_terms = OrderedDict()
        for term in semester['all_terms']:
            all_named_terms[term] = term_name(int(term))
        print all_named_terms
        semester['all_named_terms'] = all_named_terms
    return semester

def term_name(term_no):
    if term_no % 10 == 4:
        return "Spring {:d}".format(1900 + term_no / 10)
    elif term_no % 10 == 2:
        return"Fall {:d}".format(1899 + term_no / 10)
    elif term_no % 10 == 1:
        return "Summer {:d}".format(1899 + term_no / 10)

# Helper function to interpret the OMNIBAR(tm).
def parse(text):
    tokens = text.upper().split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': [], 'pdf': [], 'keywords': []}
    previous = {}
    for token in tokens:
        # Match distribution requirement codes
        if token in DISTRIBUTION_AREAS:
            output['distribution'].append(token)
        elif token == 'ST':
            output['distribution'].extend(['STN', 'STL'])
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
            output['keywords'].append(token) # Be smarter about this!
        # Match PDF criteria
        elif re.match('^NO-AUDIT$', token):
            output['pdf'].append('na')
        elif re.match('^NO-PDF$', token):
            output['pdf'].append('npdf')
        elif re.match('^PDF-ONLY$', token):
            output['pdf'].append('pdfonly')
    return output
