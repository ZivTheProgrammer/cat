from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
import sys, os, urllib, re
from CatDB import *
from collections import OrderedDict
import HTMLParser

DISTRIBUTION_AREAS = ['EM', 'EC', 'HA', 'LA', 'QR', 'SA', 'STN', 'STL']
SUBJECT_AREAS = ["AAS", "AFS", "AMS", "ANT", "AOS", "APC", "ARA", "ARC", "ART", "AST", "ATL", "BCS", "CBE", "CEE", "CHI", "CHM", "CHV", "CLA", "CLG", "COM", "COS", "CWR", "CZE", "DAN", "EAP", "EAS", "ECO", "ECS", "EEB", "EGR", "ELE", "ENE", "ENG", "ENV", "EPS", "FIN", "FRE", "FRS", "GEO", "GER", "GHP", "GLS", "GSS", "HEB", "HIN", "HIS", "HLS", "HOS", "HUM", "ISC", "ITA", "JDS", "JPN", "JRN", "KOR", "LAO", "LAS", "LAT", "LIN", "MAE", "MAT", "MED", "MOD", "MOG", "MOL", "MSE", "MUS", "NES", "NEU", "ORF", "PAW", "PER", "PHI", "PHY", "PLS", "POL", "POP", "POR", "PSY", "QCB", "REL", "RUS", "SAS", "SLA", "SOC", "SPA", "STC", "SWA", "THR", "TPP", "TRA", "TUR", "URB", "URD", "VIS", "WRI", "WWS"]
SPECIAL = {'AFRICAN', 'COMPUTATIONAL', 'APPLIED', 'CHEMICAL', 'CIVIL', 'BIOLOGICAL', 'CLASSICAL', 'COMPARATIVE', 'COMPUTER', 'CREATIVE', 'EUROPEAN', 'EVOLUTIONARY', 'ELECTRICAL', 'ENERGY', 'ENVIRONMENTAL', 'FRESHMAN', 'GLOBAL', 'GENDER', 'SEXUALITY', 'INTEGRATED', 'LATIN', 'MECHANICAL', 'AEROSPACE', 'MODERN', 'MOLECULAR', 'NEAR', 'FINANCIAL', 'OPERATIONS', 'ANCIENT', 'QUANTITATIVE', 'COMPUTATIONAL', 'SOUTH', 'TEACHER','INTERCULTURAL', 'WOODROW', 'VISUAL', 'SCIENCE', 'TECHNOLOGY'}
DEPT_MAP = {"AFRICAN AMERICAN": "AAS", "AMERICAN": "AMS", "ANTHROPOLOGY": "ANT", "ATMOSPHERIC": "AOS", "OCEANIC SCIENCE": "AOS", "APPLIED MATH": "APC", "COMPUTATIONAL MATH": "APC", "ARABIC": "ARA", "ARCHITECTURE": "ARC", "ARCHAEOLOGY": "ART", "ASTROPHYSICS": "AST", "ATELIER": "ATL", "BOSNIAN": "BCS", "CROATIAN": "BCS", "SERBIAN": "BCS", "CHEMICAL ENGINEERING": "CBE", "BIOLOGICAL ENGINEERING": "CBE", "CIVIL ENGINEERING": "CEE", "ENVIRONMENTAL ENGINEERING": "CEE", "CHINESE": "CHI", "CHEMISTRY": "CHM", "HUMAN VALUES": "CHV", "CLASSICS": "CLA", "CLASSICAL GREEK": "CLG", "COMPARATIVE LITERATURE": "COM", "COMPUTER SCIENCE": "COS", "CREATIVE WRITING": "CWR", "CZECH": "CZE", "DANCE": "DAN", "EAST ASIAN": "EAS", "ECONOMICS": "ECO", "EUROPEAN CULTURAL": "ECS", "ECOLOGY": "EEB", "EVOLUTIONARY BIOLOGY": "EEB", "ENGINEERING": "EGR", "ELECTRICAL ENGINEERING": "ELE", "ENERGY STUDIES": "ENE", "ENGLISH": "ENG", "ENVIRONMENTAL STUDIES":"ENV", "CONTEMPORARY EUROPEAN": "EPS", "EUROPEAN POLITICS": "EPS", "FINANCE": "FIN", "FRENCH": "FRE", "FRESHMAN SEMINAR": "FRS", "GEOSCIENCES": "GEO", "GERMAN": "GER", "GLOBAL HEALTH": "GHP", "GLOBAL SEMINAR": "GLS", "GENDER AND SEXUALITY": "GSS", "HEBREW": "HEB", "HINDI": "HIN", "HISTORY": "HIS", "HELLENIC STUDIES": "HLS", "HELLENIC": "HLS", "HUMANISTIC": "HUM", "INTEGRATED SCIENCE": "ISC", "ITALIAN": "ITA", "JUDAIC": "JDS", "JAPANESE": "JPN", "JOURNALISM": "JRN", "KOREAN": "KOR", "LATINO": "LAO", "LATIN AMERICAN": "LAS", "LATIN": "LAT", "LINGUISTICS": "LIN", "MECHANICAL ENGINEERING": "MAE", "AEROSPACE ENGINEERING": "MAE", "MATHEMATICS": "MAT", "MATH": "MAT", "MEDIEVAL": "MED", "MODERN GREEK": "MOG", "MOLECULAR BIOLOGY": "MOL", "MATERIALS": "MSE", "MUSIC": "MUS", "NEAR EASTERN": "NES", "NEUROSCIENCE": "NEU", "OPERATIONS RESEARCH": "ORF", "FINANCIAL ENGINEERING": "ORF", "ANCIENT WORLD": "PAW", "PERSIAN": "PAW", "PHILOSOPHY": "PHI", "PHYSICS": "PHY", "POLISH": "PLS", "POLITICS": "POL", "PSYCHOLOGY": "PSY", "QUANTITATIVE BIOLOGY": "QCB", "COMPUTATIONAL BIOLOGY": "QCB", "RELIGION": "REL", "RUSSIAN": "RUS", "SOUTH ASIAN": "SAS", "SLAVIC": "SLA", "SOCIOLOGY": "SOC", "SPANISH": "SPA", "SWAHILI": "SWA", "THEATER": "THR", "TEACHER PREPARATION": "TPP", "TRANSLATION": "TRA", "INTERCULTURAL COMMUNICATION": "TRA", "TURKISH": "TUR", "URBAN": "URB", "URDU": "URD", "VISUAL ARTS": "VIS", "WRITING": "WRI", "WOORDROW WILSON": "WWS", "SCIENCE COUNCIL": "STC", "TECHNOLOGY COUNCIL": "STC"}


def home(request):
    return HttpResponseRedirect("/index/")

def about(request):
    if 'netid' in request.session:
        netid = request.session['netid']
    else:
        netid = ""
    return render(request, "about.html", {'netid': netid})
    
# Handle user login. Based on Kernighan's Python CAS code. 
def login(request):
    cas_url = "https://fed.princeton.edu/cas/"
    service_url = 'http://' + urllib.quote(request.META['HTTP_HOST'] + request.META['PATH_INFO'])
    service_url = re.sub(r'ticket=[^&]*&?', '', service_url)
    service_url = re.sub(r'\?&?$|&$', '', service_url)
    if "ticket" in request.GET:
        val_url = cas_url + "validate?service=" + service_url + '&ticket=' + urllib.quote(request.GET['ticket'])
        r = urllib.urlopen(val_url).readlines() # returns 2 lines
        if len(r) == 2 and re.match("yes", r[0]) != None:
            request.session['netid'] = r[1].strip()
            return HttpResponseRedirect("/index/")
        else:
            return HttpResponse("Failed!")
    else:
        login_url = cas_url + 'login?service=' + service_url
        return HttpResponseRedirect(login_url)

# Handle user logout. Logs user out of both CAT and CAS.
def logout(request):
    del request.session['netid']
    return HttpResponseRedirect("https://fed.princeton.edu/cas/logout")
        
# Base view for the site. Get courses currently in cart.
def index(request):
    if not request.session.has_key('netid'):
        return HttpResponseRedirect("/login/")
    classified = {}
    db = CatDB()
    student = db.get_student(request.session['netid'])
    courses = student.get('courseList', [])
    courses = db.get_course(course_id = courses)
    for result in courses:
        result['source'] = 'cart'
        classified[result['course_id']] = result
    return render(request, "index.html", {'distrib': DISTRIBUTION_AREAS, 'courses': courses, 
        'results': classified, 'netid': request.session['netid'], 'first_load': True, 'current_semester': CURRENT_SEMESTER})

# Get search results and pass them back to the search page.
@require_POST
def search_results(request):
    # Used to keep track of result versus cart courses
    classified = OrderedDict()
    # Load courses in search results
    db = CatDB()
    query = parse(db, request.POST['text'])
    output = db.get_course(**query)
    for result in output:
        result['source'] = 'results'
        classified[result['course_id']] = result
    # Load courses in cart
    student = db.get_student(request.session['netid'])
    list = student.get('courseList', [])
    courses = db.get_course(course_id = list)
    for result in courses:
        if result['course_id'] in classified:
            if classified[result['course_id']]['source'] == 'results':
                classified[result['course_id']]['source'] = 'both'
        else:
            result['source'] = 'cart'
            classified[result['course_id']] = result
    return render(request, "search_results.html", {'results': classified, 'current_semester': CURRENT_SEMESTER})
    
# Get a new semester and pass it back to the search page.
@require_POST
def get_semester(request):
    db = CatDB()
    course = db.get_course({"course_id": request.POST['course_id']})[0]
    result = db.get_course({"subject": course['subject'], 
        "course_number": course['course_number'], 
        "term": request.POST['semester']})[0]
    return render(request, "get_semester.html", {'result': result})

# Get a course's reviews and pass them back.
@require_POST
def get_reviews(request):
    db = CatDB()
    course = db.get_course({"course_id": request.POST['course_id']})[0]
    result = db.get_reviews(course['unique_course'])
    # Do some annotating
    for review in result:
        review['term_name'] = term_name(int(review['term']))
        review['profs'] = []
        for instructor in review['instructors']:
            review['profs'].append(db.get_professor(id_number=instructor)[0])
        review['review_text'].sort(key = len, reverse = True)
    return render(request, "get_reviews.html", {'results': result, 'current_semester': CURRENT_SEMESTER})
    
# Add a course to the user's course cart.
@require_POST
def add_course_cart(request):
    db = CatDB()
    db.add_course(request.session['netid'], request.POST['course_id'])
    return render(request, "cart_course.html", {'course_id': request.POST['course_id'], 
        'course_subject': request.POST['course_code'][0:3], 'course_number': request.POST['course_code'][3:6]})
    
# Remove a course from the user's course cart.  
@require_POST
def remove_course_cart(request):
    db = CatDB()
    db.remove_course(request.session['netid'], request.POST['course_id'])
    return HttpResponse("Success") # Shouldn't need to return anything

# A temporary view to update annotations. To replace with a more complete admin page.
def admin(request):
    if not request.session.has_key('netid'):
        return HttpResponseRedirect("/login/")
    if not request.session['netid'] in ['apthorpe', 'gdisco', 'lpaulsen', 'nweires', 'jmtang']:
        return HttpResponseRedirect("/index/")
    db = CatDB()
    db.annotate()
    return HttpResponse('Welcome to the temporary admin page! The database has been successfully annotated. Nothing more to see here at the moment.')

# Helper function to interpret the OMNIBAR.
# Note: standalone 'pdf' gets completely ignored unless immediately followed by 'only'
def parse(db, text):
    tokens = text.upper().replace(',', ' ').replace('.', ' ').split()
    output = {'subject': [], 'course_number': [], 'professor_name': [], 'distribution': [], 'pdf': [], 'keywords': [], 'day': [], 'time': []}
    previous = ''
    for token in tokens:
        two = previous + ' ' + token
        # Match specially detected keywords
        if re.match('^KW:.{3,}$', token):
            output['keywords'].append(token[3:])  
        # Match distribution requirement codes
        elif token in DISTRIBUTION_AREAS:
            output['distribution'].append(token)
        elif token == 'ST':
            output['distribution'].extend(['STN', 'STL'])
        # Match subject codes
        elif token in SUBJECT_AREAS:
            output['subject'].append(token)
        # Match departments
        elif two in DEPT_MAP:
            output['subject'].append(DEPT_MAP[two])
        elif token in DEPT_MAP:
            output['subject'].append(DEPT_MAP[token])
        elif token in SPECIAL:
            pass
        elif previous in SPECIAL:
            output['keywords'].append(previous)
            output['keywords'].append(token)
        # Match full course code
        elif re.match('^[A-Z]{3}[0-9]{3}[A-Za-z]?$', token):
            output['subject'].append(token[0:3])
            output['course_number'].append(token[3:])
        # Match course numbers
        elif re.match('^>[0-9]{3}$', token) or re.match('^>[0-9]{3}$', previous+token):
            output['min_course_number'] = token[-3:] 
        elif re.match('^<[0-9]{3}$', token) or re.match('^<[0-9]{3}$', previous+token):
            output['max_course_number'] = token[-3:]
        elif re.match('^>=[0-9]{3}$', token) or re.match('^>=[0-9]{3}$', previous+token):
            output['min_course_number'] = '%03d'%(int(token[-3:])-1)
        elif re.match('^<=[0-9]{3}$', token) or re.match('^<=[0-9]{3}$', previous+token):
            output['max_course_number'] = '%03d'%(int(token[-3:])+1)
        elif re.match('^[0-9]{3}[A-Za-z]?$', token):
            output['course_number'].append(token)
        elif re.match('^[0-9]{1,3}-[0-9]{1,3}$', token):
            output['min_course_number'] = '%03d'%(int(token.split('-')[0])-1)
            output['max_course_number'] = '%03d'%(int(token.split('-')[1])+1)
        # Match PDF criteria
        elif re.match('^(NO-AUDIT|NA|NOAUDIT)$', token):
            output['pdf'].append('na')
        elif re.match('^(NO-PDF|NOPDF|NPDF)$', token):
            output['pdf'].append('npdf')
        elif re.match('^(PDF-ONLY|PDFONLY)$', token):
            output['pdf'].append('pdfonly')
        # Only works if standalone 'pdf' gets ignored
        elif re.match('^ONLY$', token) and re.match('^PDF$', previous):
            output['pdf'].append('pdfonly')
        elif re.match('^(PDF|PDFABLE|PDF-ABLE)$', token) and re.match('^(NO|NOT)$', previous):
            output['pdf'].append('npdf')
        elif re.match('^(AUDIT|A|AUDITABLE|AUDIT-ABLE)$', token) and re.match('^(NO|NOT)$', previous):
            output['pdf'].append('na')
        elif re.match('^(NO|NOT|PDF)$', token):
            pass
        # Capture day-of-the-week abbreviations
        elif re.match('^(M)?(T)?(W)?(TH)?(F)?$', token):
            t_last = False
            for letter in token:
                if t_last:
                    if letter == "H":
                        output['day'].append('TH')
                        t_last = False
                    elif letter == "T":
                        output['day'].append('T')
                        t_last = True
                    else:
                        output['day'].append('T')
                        t_last = False
                else:
                    if letter == "T":
                        t_last = True
                    else:
                        output['day'].append(letter)
                        t_last = False
            if t_last:
                output['day'].append('T')
        elif re.match('^(M|MO|MON|MONDAY)$', token):
            output['day'].append('M')
        elif re.match('^(T|TU|TUE|TUES|TUESDAY)$', token):
            output['day'].append('T')
        elif re.match('^(W|WE|WED|WEDNESDAY)$', token):
            output['day'].append('W')
        elif re.match('^(TH|THU|THUR|THURS|THURSDAY)$', token):
            output['day'].append('TH')
        elif re.match('^(F|FR|FRI|FRIDAY)$', token):
            output['day'].append('F')
        # Match times    
        elif re.match('^[0-2]?[0-9]:[0-9][0-9]$', token):
            output['time'].append(token)
        elif re.match('^[0-2]?[0-9]:[0-9][0-9](AM|PM)$', token):
            output['time'].append(token[:-2])
        elif re.match('^[0-2]?[0-9]$', token):
            output['time'].append(token + ":00")
        elif re.match('^[0-2]?[0-9](AM|PM)$', token):
            output['time'].append(token[:-2] + ":00")
        # Match professor names / general keywords
        elif re.match('^[A-Z]+$', token):
            if db.get_professor(token).count() > 0:
                output['professor_name'].append(token)
            # if not a professor's name, then assume it's a keyword
            elif re.match('^[A-Z]{3,}$', token):
                output['keywords'].append(token)
        previous = token
    return output
