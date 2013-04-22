from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from forms import *
import CASClient
import re
from CatDB import CatDB
from collections import OrderedDict

DISTRIBUTION_AREAS = ['EM', 'EC', 'HA', 'LA', 'QR', 'SA', 'STN', 'STL']
SUBJECT_AREAS = ["AAS", "AFS", "AMS", "ANT", "AOS", "APC", "ARA", "ARC", "ART", "AST", "ATL", "BCS", "CBE", "CEE", "CHI", "CHM", "CHV", "CLA", "CLG", "COM", "COS", "CWR", "CZE", "DAN", "EAP", "EAS", "ECO", "ECS", "EEB", "EGR", "ELE", "ENE", "ENG", "ENV", "EPS", "FIN", "FRE", "FRS", "GEO", "GER", "GHP", "GLS", "GSS", "HEB", "HIN", "HIS", "HLS", "HOS", "HUM", "ISC", "ITA", "JDS", "JPN", "JRN", "KOR", "LAO", "LAS", "LAT", "LIN", "MAE", "MAT", "MED", "MOD", "MOG", "MOL", "MSE", "MUS", "NES", "NEU", "ORF", "PAW", "PER", "PHI", "PHY", "PLS", "POL", "POP", "POR", "PSY", "QCB", "REL", "RUS", "SAS", "SLA", "SOC", "SPA", "STC", "SWA", "THR", "TPP", "TRA", "TUR", "URB", "URD", "VIS", "WRI", "WWS"]
DECAY_FACTOR = 0.5

def home(request):
    return HttpResponseRedirect("/index/")

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
    classified = OrderedDict()
    # Load courses in search results
    db = CatDB()
    query = parse(db, request.POST['text'])
    output = db.get_course(**query)
    for result in output:
        result = annotate(db, result)
        result['source'] = 'results'
        classified[result['course_id']] = result
    # Load courses in cart
    student = db.get_student("bbaggins")
    list = student.get('courseList', [])
    courses = db.get_course(course_id = list)
    for result in courses:
        result = annotate(db, result)
        if result['course_id'] in classified:
            if classified[result['course_id']]['source'] == 'results':
                classified[result['course_id']]['source'] = 'both'
        else:
            result['source'] = 'cart'
            classified[result['course_id']] = result
    return render(request, "search_results.html", {'results': classified})
    
# Get a new semester and pass it back to the search page.
def get_semester(request):
    db = CatDB()
    course = db.get_course({"course_id": request.POST['course_id']})[0]
    result = db.get_course({"subject": course['subject'], 
        "course_number": course['course_number'], 
        "term": request.POST['semester']})[0]
    result = annotate(db, result)
    return render(request, "get_semester.html", {'result': result})

# Get a course's reviews and pass them back.
def get_reviews(request):
    db = CatDB()
    course = db.get_course({"course_id": request.POST['course_id']})[0]
    result = db.get_reviews(course['unique_course'])
    print result
    return render(request, "get_reviews.html", {'result': result})
    
# Add a course to the user's course cart.
def add_course_cart(request):
    db = CatDB()
    db.add_course("bbaggins", request.POST['course_id'])
    return render(request, "cart_course.html", {'course_id': request.POST['course_id'], 'course_name': request.POST['course_code']})
    
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
        # Add more nice semester names
        all_named_terms = OrderedDict()
        for term in semester['all_terms']:
            all_named_terms[term] = term_name(int(term))
        semester['all_named_terms'] = all_named_terms
    # Add aggregated review data
    reviews = db.get_reviews(semester['unique_course'])
    current_weight = 1.0
    total_weight = 0.0
    weighted_rating = 0.0
    for review in reviews:
        print review['review_Nums']
        if 'overall_mean' in review['review_Nums']:
            total_weight += current_weight
            weighted_rating += float(review['review_Nums']['overall_mean']) * current_weight
            current_weight = current_weight * DECAY_FACTOR
    if total_weight > 0.0:
        semester['overall_rating'] = weighted_rating / total_weight
    return semester

def term_name(term_no):
    if term_no % 10 == 4:
        return "Spring {:d}".format(1900 + term_no / 10)
    elif term_no % 10 == 2:
        return"Fall {:d}".format(1899 + term_no / 10)
    elif term_no % 10 == 1:
        return "Summer {:d}".format(1899 + term_no / 10)

# Helper function to interpret the OMNIBAR(tm).
def parse(db, text):
    tokens = text.upper().split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': [], 'pdf': [], 'keywords': []}
    previous = ''
    for token in tokens:
        # Match distribution requirement codes
        if token in DISTRIBUTION_AREAS:
            output['distribution'].append(token)
        elif token == 'ST':
            output['distribution'].extend(['STN', 'STL'])
        # Match subject codes
        elif token in SUBJECT_AREAS:
            output['subject'].append(token)
        # Match course numbers
        elif re.match('^>[0-9]{3}$', token) or re.match('^>[0-9]{3}$', previous+token):
            output['min_course_number'] = token[-3:] 
        elif re.match('^<[0-9]{3}$', token) or re.match('^<[0-9]{3}$', previous+token):
            output['max_course_number'] = token[-3:]
        elif re.match('^>=[0-9]{3}$', token) or re.match('^>=[0-9]{3}$', previous+token):
            output['min_course_number'] = str(int(token[-3:])-1)
        elif re.match('^<=[0-9]{3}$', token) or re.match('^<=[0-9]{3}$', previous+token):
            output['max_course_number'] = str(int(token[-3:])+1)
        elif re.match('^[0-9]{3}[A-Za-z]?$', token):
            output['course_number'].append(token)
        
        # Match PDF criteria
        elif re.match('^(NO-AUDIT|NA|NOAUDIT)$', token):
            output['pdf'].append('na')
        elif re.match('^(NO-PDF|NOPDF|NPDF)$', token):
            output['pdf'].append('npdf')
        elif re.match('^(PDF-ONLY|PDFONLY)$', token):
            output['pdf'].append('pdfonly')
        elif re.match('^(PDF|PDFABLE|PDF-ABLE)$', token) and re.match('^(NO|NOT)$', previous):
            output['pdf'].append('npdf')
        elif re.match('^(AUDIT|A|AUDITABLE|AUDIT-ABLE)$', token) and re.match('^(NO|NOT)$', previous):
            output['pdf'].append('na')

        elif re.match('^(NO|NOT)$', token):
            pass
        # Match professor names
        elif re.match('^[A-Z]+$', token):
            if db.get_professor(token).count() > 0:
                output['professor_name'].append(token)
            else:
                output['keywords'].append(token)
        previous = token
    return output
    
