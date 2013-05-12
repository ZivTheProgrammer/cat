from django.shortcuts import render, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from forms import *
import CASClient
import sys, os, urllib, re
from CatDB import CatDB
from collections import OrderedDict
import HTMLParser

RATING_CATEGORIES = ['overall_mean', 'lectures_mean', 'precepts_mean', 'classes_mean', 'readings_mean']
DISTRIBUTION_AREAS = ['EM', 'EC', 'HA', 'LA', 'QR', 'SA', 'STN', 'STL']
SUBJECT_AREAS = ["AAS", "AFS", "AMS", "ANT", "AOS", "APC", "ARA", "ARC", "ART", "AST", "ATL", "BCS", "CBE", "CEE", "CHI", "CHM", "CHV", "CLA", "CLG", "COM", "COS", "CWR", "CZE", "DAN", "EAP", "EAS", "ECO", "ECS", "EEB", "EGR", "ELE", "ENE", "ENG", "ENV", "EPS", "FIN", "FRE", "FRS", "GEO", "GER", "GHP", "GLS", "GSS", "HEB", "HIN", "HIS", "HLS", "HOS", "HUM", "ISC", "ITA", "JDS", "JPN", "JRN", "KOR", "LAO", "LAS", "LAT", "LIN", "MAE", "MAT", "MED", "MOD", "MOG", "MOL", "MSE", "MUS", "NES", "NEU", "ORF", "PAW", "PER", "PHI", "PHY", "PLS", "POL", "POP", "POR", "PSY", "QCB", "REL", "RUS", "SAS", "SLA", "SOC", "SPA", "STC", "SWA", "THR", "TPP", "TRA", "TUR", "URB", "URD", "VIS", "WRI", "WWS"]
SPECIAL = {'AFRICAN', 'COMPUTATIONAL', 'APPLIED', 'CHEMICAL', 'CIVIL', 'BIOLOGICAL', 'CLASSICAL', 'COMPARATIVE', 'COMPUTER', 'CREATIVE', 'EUROPEAN', 'EVOLUTIONARY', 'ELECTRICAL', 'ENERGY', 'ENVIRONMENTAL', 'FRESHMAN', 'GLOBAL', 'GENDER', 'SEXUALITY', 'INTEGRATED', 'LATIN', 'MECHANICAL', 'AEROSPACE', 'MODERN', 'MOLECULAR', 'NEAR', 'FINANCIAL', 'OPERATIONS', 'ANCIENT', 'QUANTITATIVE', 'COMPUTATIONAL', 'SOUTH', 'TEACHER','INTERCULTURAL', 'WOODROW', 'VISUAL', 'SCIENCE', 'TECHNOLOGY'}
DEPT_MAP = {"AFRICAN AMERICAN": "AAS", "AMERICAN": "AMS", "ANTHROPOLOGY": "ANT", "ATMOSPHERIC": "AOS", "OCEANIC SCIENCE": "AOS", "APPLIED MATH": "APC", "COMPUTATIONAL MATH": "APC", "ARABIC": "ARA", "ARCHITECTURE": "ARC", "ARCHAEOLOGY": "ART", "ASTROPHYSICS": "AST", "ATELIER": "ATL", "BOSNIAN": "BCS", "CROATIAN": "BCS", "SERBIAN": "BCS", "CHEMICAL ENGINEERING": "CBE", "BIOLOGICAL ENGINEERING": "CBE", "CIVIL ENGINEERING": "CEE", "ENVIRONMENTAL ENGINEERING": "CEE", "CHINESE": "CHI", "CHEMISTRY": "CHM", "HUMAN VALUES": "CHV", "CLASSICS": "CLA", "CLASSICAL GREEK": "CLG", "COMPARATIVE LITERATURE": "COM", "COMPUTER SCIENCE": "COS", "CREATIVE WRITING": "CWR", "CZECH": "CZE", "DANCE": "DAN", "EAST ASIAN": "EAS", "ECONOMICS": "ECO", "EUROPEAN CULTURAL": "ECS", "ECOLOGY": "EEB", "EVOLUTIONARY BIOLOGY": "EEB", "ENGINEERING": "EGR", "ELECTRICAL ENGINEERING": "ELE", "ENERGY STUDIES": "ENE", "ENGLISH": "ENG", "ENVIRONMENTAL STUDIES":"ENV", "CONTEMPORARY EUROPEAN": "EPS", "EUROPEAN POLITICS": "EPS", "FINANCE": "FIN", "FRENCH": "FRE", "FRESHMAN SEMINAR": "FRS", "GEOSCIENCES": "GEO", "GERMAN": "GER", "GLOBAL HEALTH": "GHP", "GLOBAL SEMINAR": "GLS", "GENDER AND SEXUALITY": "GSS", "HEBREW": "HEB", "HINDI": "HIN", "HISTORY": "HIS", "HELLENIC RY EUROPEAN": "EPS", "EUROPEAN POLITICS": "EPS", "FINANCE": "FIN", "FRENCH": "FRE", "FRESHMAN SEMINAR": "FRS", "GEOSCIENCES": "GEO", "GERMAN": "GER", "GLOBAL HEALTH": "GHP", "GLOBAL SEMINAR": "GLS", "GENDER": "GSS", "SEXUALITY": "GSS", "HEBREW": "HEB", "HINDI": "HIN", "HISTORY": "HIS", "HELLENIC": "HLS", "HUMANISTIC": "HUM", "INTEGRATED SCIENCE": "ISC", "ITALIAN": "ITA", "JUDAIC": "JDS", "JAPANESE": "JPN", "JOURNALISM": "JRN", "KOREAN": "KOR", "LATINO": "LAO", "LATIN AMERICAN": "LAS", "LATIN": "LAT", "LINGUISTICS": "LIN", "MECHANICAL ENGINEERING": "MAE", "AEROSPACE ENGINEERING": "MAE", "MATHEMATICS": "MAT", "MATH": "MAT", "MEDIEVAL": "MED", "MODERN GREEK": "MOG", "MOLECULAR BIOLOGY": "MOL", "MATERIALS": "MSE", "MUSIC": "MUS", "NEAR EASTERN": "NES", "NEUROSCIENCE": "NEU", "OPERATIONS RESEARCH": "ORF", "FINANCIAL ENGINEERING": "ORF", "ANCIENT WORLD": "PAW", "PERSIAN": "PAW", "PHILOSOPHY": "PHI", "PHYSICS": "PHY", "POLISH": "PLS", "POLITICS": "POL", "PSYCHOLOGY": "PSY", "QUANTITATIVE BIOLOGY": "QCB", "COMPUTATIONAL BIOLOGY": "QCB", "RELIGION": "REL", "RUSSIAN": "RUS", "SOUTH ASIAN": "SAS", "SLAVIC": "SLA", "SOCIOLOGY": "SOC", "SPANISH": "SPA", "SWAHILI": "SWA", "THEATER": "THR", "TEACHER PREPARATION": "TPP", "TRANSLATION": "TRA", "INTERCULTURAL COMMUNICATION": "TRA", "TURKISH": "TUR", "URBAN": "URB", "URDU": "URD", "VISUAL ARTS": "VIS", "WRITING": "WRI", "WOORDROW WILSON": "WWS", "SCIENCE COUNCIL": "STC", "TECHNOLOGY COUNCIL": "STC"}
DECAY_FACTOR = 0.4 # For averaging course ratings over multiple semesters

def home(request):
    return HttpResponseRedirect("/index/")

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
        result = annotate(db, result)
        result['source'] = 'cart'
        classified[result['course_id']] = result
    return render(request, "index.html", {'distrib': DISTRIBUTION_AREAS, 'courses': courses, 
        'results': classified, 'netid': request.session['netid'], 'first_load': True})

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
        result = annotate(db, result)
        result['source'] = 'results'
        classified[result['course_id']] = result
    # Load courses in cart
    student = db.get_student(request.session['netid'])
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
@require_POST
def get_semester(request):
    db = CatDB()
    course = db.get_course({"course_id": request.POST['course_id']})[0]
    result = db.get_course({"subject": course['subject'], 
        "course_number": course['course_number'], 
        "term": request.POST['semester']})[0]
    result = annotate(db, result)
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
    return render(request, "get_reviews.html", {'results': result})
    
# Add a course to the user's course cart.
@require_POST
def add_course_cart(request):
    db = CatDB()
    db.add_course(request.session['netid'], request.POST['course_id'])
    return render(request, "cart_course.html", {'course_id': request.POST['course_id'], 'course_name': request.POST['course_code']})
    
# Remove a course from the user's course cart.  
@require_POST
def remove_course_cart(request):
    db = CatDB()
    db.remove_course(request.session['netid'], request.POST['course_id'])
    return HttpResponse("Success") #Shouldn't need to return anything

# Helper function to add information to a semester of a course.
def annotate(db, semester):
    # Unescape html characters
    parser = HTMLParser.HTMLParser()
    regex = re.compile(r'<.*?>')
    if 'description' in semester and semester['description']:
        semester['description'] = parser.unescape(semester['description'])
    if 'readings' in semester:
        for reading in semester['readings']:
            for key in reading:
                reading[key] = parser.unescape(reading[key])
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
    weighted_rating = dict((category, 0.0) for category in RATING_CATEGORIES)
    for review in reviews:
        # Skip reviews for terms later than the one being viewed
        if int(review['term']) > int(semester['term']):
            continue
        # Skip terms that don't have any reviews
        if not review['review_Nums']:
            continue
        # Update weights
        current_weight = current_weight * DECAY_FACTOR 
        total_weight += current_weight
        # Add up ratings by category
        for category in RATING_CATEGORIES:
            if category in review['review_Nums']:
                weighted_rating[category] += float(review['review_Nums'][category]) * current_weight
            else:
                weighted_rating[category] -= 42.0 # large negative magic number
    if total_weight > 0.0:
        for category in RATING_CATEGORIES:
            if weighted_rating[category] > 0.0:
                semester[category] = "{0:.2f}".format(weighted_rating[category] / total_weight)
        if weighted_rating['overall_mean'] / total_weight > 4.6:
            semester['rating_color'] = 'rating_color_1'
        elif weighted_rating['overall_mean'] / total_weight > 4.4:
            semester['rating_color'] = 'rating_color_2'
        elif weighted_rating['overall_mean'] / total_weight > 4.2:
            semester['rating_color'] = 'rating_color_3'
        elif weighted_rating['overall_mean'] / total_weight > 4.0:
            semester['rating_color'] = 'rating_color_4'
        elif weighted_rating['overall_mean'] / total_weight > 3.8:
            semester['rating_color'] = 'rating_color_5'
        elif weighted_rating['overall_mean'] / total_weight > 3.6:
            semester['rating_color'] = 'rating_color_6'
        elif weighted_rating['overall_mean'] / total_weight > 3.4:
            semester['rating_color'] = 'rating_color_7'
        elif weighted_rating['overall_mean'] / total_weight > 3.2:
            semester['rating_color'] = 'rating_color_8'
        elif weighted_rating['overall_mean'] / total_weight > 0.0:
            semester['rating_color'] = 'rating_color_9'
    return semester

def term_name(term_no):
    if term_no % 10 == 4:
        return "Spring {:d}".format(1900 + term_no / 10)
    elif term_no % 10 == 2:
        return "Fall {:d}".format(1899 + term_no / 10)
    elif term_no % 10 == 1:
        return "Summer {:d}".format(1899 + term_no / 10)

# Helper function to interpret the OMNIBAR(tm).
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
            print 'ahoy!'
            output['subject'].append(DEPT_MAP[token])
        elif token in SPECIAL:
            print 'here'
            pass
        elif previous in SPECIAL:
            output['keywords'].append(previous)
            output['keywords'].append(token)
        # Match full course code
        elif re.match('^[A-Z]{3}[0-9]{3}$', token):
            output['subject'].append(token[0:3])
            output['course_number'].append(token[3:6])
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
                    else:
                        output['day'].append('T')
                    t_last = False
                else:
                    if letter == "T":
                        t_last = True
                    else:
                        output['day'].append(letter)
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
        elif re.match('^[0-2]?[0-9]:[0-9][0-9][AP]M$', token):
            output['time'].append(token[:-2])
        elif re.match('^[0-2]?[0-9](AM|PM)?$', token):
            output['time'].append(token + ":00")
        elif re.match('^[0-2]?[0-9][AP]M$', token):
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
