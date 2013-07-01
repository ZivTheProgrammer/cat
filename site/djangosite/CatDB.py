from datetime import datetime
from pymongo import MongoClient
import pymongo
import re
import string
import pprint
import HTMLParser
from collections import OrderedDict

""" A class that provides functions to get information from our database
    of courses. To use, create a CatDB object:
        db = CatDB()
    then call the various functions on it:
        db.getProfessorInfo(name='Kernighan')
"""

CURRENT_SEMESTER = '1142' # The most recent semester for which courses are posted. TODO: Make sure this isn't defined anywhere else.
RATING_CATEGORIES = ['overall', 'lectures', 'precepts', 'classes', 'readings', 'assignments']
DECAY_FACTOR = 0.33 # For averaging course ratings over multiple semesters
STARTING_WEIGHT = 0.05 # Also for averaging course ratings. Increase or decrease to change strength of Bayesian ranking system.
RATINGS_COLOR_SCALE = [0.0, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6] # Scale for determing rating colors

# A helper function to define nice term names. Moved here from views
def term_name(term_no):
    if term_no % 10 == 4:
        return "Spring {:d}".format(1900 + term_no / 10)
    elif term_no % 10 == 2:
        return "Fall {:d}".format(1899 + term_no / 10)
    elif term_no % 10 == 1:
        return "Summer {:d}".format(1899 + term_no / 10)

class CatDB:

    words2ignore = ['the', 'be', 'to', 'of', u'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do',
            'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say',
            'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'there'];

    def __init__(self):
        self.connection = MongoClient()
        self.db = self.connection.cat_database
        self.courseCol = self.db.courses
        self.profCol = self.db.instructors
        self.studentCol = self.db.students
        self.uniqueCourseCol = self.db.unique
        self.analytics = self.db.analytics
            # entries with types 'newUser', 'addClass', 'removeClass'

    def get_student(self, netID):
        course_list = self.studentCol.find_one({'netID': netID});
        # Record that the student has visited
        self.studentCol.update({'netID':netID}, {'$set': {'lastVisit' : datetime.now()}}, upsert=True)
        if not course_list:
            self.analytics.insert({'type':'newUser', 'time':datetime.now()})
            course_list = {}
        return course_list
        
    def add_course(self, netID, courseList):
        self.analytics.insert({'type':'addClass', 'time':datetime.now()})
        if (self.studentCol.find_one({'netID': netID}) is None):
            entry = {};
            entry['netID'] = netID;
            if isinstance(courseList, list):
                entry['courseList'] = courseList;
            else:
                entry['courseList'] = [courseList];
            entry['lastVisit'] = datetime.now()
            self.studentCol.insert(entry);
        else:
            entry = self.studentCol.find_one({'netID': netID});
            if 'courseList' not in entry:
                entry['courseList'] = []
            if isinstance(courseList, list):
                for course in courseList:
                    if course not in entry['courseList']:
                        entry['courseList'].append(course);
            else:
                entry['courseList'].append(courseList);
            # put updated things back
            self.studentCol.update({'netID': netID},
                                   {'$set': {'courseList': entry['courseList'],
                                    'lastVisit' : datetime.now()},
                                    },upsert=True)
        print 'Added a course to get list: ', entry.get('courseList', [])

    def remove_course(self, netID, courseList):
        self.analytics.insert({'type':'removeClass', 'time':datetime.now()})
        print 'removing', courseList
        # check for if course is not there then you can't remove it
        if (self.studentCol.find_one({'netID': netID}) is None):
            sys.stderr.write('you tried to remove a course when the student has no courses!');
        else:
            entry = self.studentCol.find_one({'netID': netID})
            if isinstance(courseList, list):
                for course in courseList:
                    if course in entry['courseList']:
                        entry['courseList'].remove(course)
            else:
                if courseList in entry['courseList']:
                    entry['courseList'].remove(courseList)
            # put updated things back
            self.studentCol.update({'netID': netID},
                                   {'$set': {'courseList': entry['courseList'],
                                             'lastVisit' : datetime.now()}
                                    },upsert=True)
        print 'Removed a course to get list: ', entry.get('courseList', [])

    # Returns a list of professors with matching id and name
    # (name can be partial, id cannot)
    def get_professor(self, name=None, id_number=None):
        prof = {}
        if not name and not id_number:
            return None
        if id_number:
            prof['id'] = id_number
        if name: # regex to search for parts of names
            nameRegex = '.*(^|\s)' + string.join(name.split(), '(\s)(.+\s)?') + '($|\s).*'
            prof['name'] = re.compile(nameRegex, re.IGNORECASE)
        return self.profCol.find(prof)

    def rank(self, list_courses, keywords):
        # check how many keywords the course description contains
        scores = {}
        courses_ranked = []
        if keywords == None:
            return list_courses;
        for course in list_courses:
            courseDesc = course.get('description', '').upper() if course.get('description', None) else ''
            title = course.get('title', '').upper() if course.get('title', None) else ''
            totalcount = 0
            matchDesc = 0
            matchTitle = 0
            totalscore = 0
            if keywords is None:
                return list_courses
            for q in keywords:
                if (re.search(q.upper(), title)):
                    matchTitle = matchTitle + 1
                if (re.search(q.upper(), courseDesc)):
                    matchDesc = matchDesc + 1
                    totalcount = totalcount + courseDesc.count(q)
            # sleazy            
            totalscore = matchTitle*1000 + matchDesc*100 + totalcount
            course['score'] = totalscore; # dictionary of scores of courses        
        list_courses = sorted(list_courses, key=lambda course: (course['subject'], course['course_number']))
        return sorted(list_courses, key=lambda course: course['score'], reverse = True);

    """ Returns all courses that match all the given information
        course can be a dict with all this info; if it's provided, everything
        else is ignored, and it is passed to the search directly
        If course number/term is specified, min/max values are ignored
        If professor id and name are given, finds classes that match either
        Anything that takes a single value can also take a list. The function
        returns courses that match any of them
        pdf can be 'na', 'pdfonly', 'npdf' (not pdf-able)

        If unique=True, returns the most recent semester of any matching course.
        Otherwise, returns every semester that matches.
        In the resulting list of dictionaries, 'all_terms' will be specified only
        if unique=True

        For example:
        get_course(course_number='201', subject=['MAT', 'COS', 'ELE'])
        would return whichever of MAT201, COS201 and ELE201 that exist,
        from every semester
    """
    def get_course(self, course=None, subject=None, course_number=None,
            min_course_number=None, max_course_number=None, professor_id=None,
            professor_name=None, term=None, min_term=None, max_term=None,
            distribution=None, pdf=None, course_id=None, unique_course=None,
            keywords=None, unique=True, time=None, day=None):

        #TODO: make sure all of these are strings
        if course:
            return self.courseCol.find(course)
        else:
            course = {}
            
        if time:
            if not isinstance(time, list):
                time = [time]
            times = [re.compile('^'+t, re.I) for t in time]

            course['term'] = CURRENT_SEMESTER
            course['classes'] =  {
                '$elemMatch': {
                    'section': re.compile('[LCS].*', re.I),
                    'starttime': {'$in': times},
                    }
                }
            
        if day:
            if not isinstance(day, list):
                day = [day]
            regex = '^('
            for d in day:
                if (d == "t") or (d == "T"):
                    regex = regex +  "(T)|"
                else:
                    regex = regex + d + "|"
            regex = regex + "Z)*$"
            course['term'] = CURRENT_SEMESTER
            match = { 
                '$elemMatch': {
                    'section': re.compile('[LCS].*', re.I),
                    'days': re.compile(regex, re.IGNORECASE)  #{'$in': day}
                    }
                }
            if 'classes' not in course:
                course['classes'] = match
            else:
                course['classes']['$elemMatch']['days'] = match['$elemMatch']['days']
            
        if subject:
            # TODO: Make all capital letters
            course['subject'] = { '$in':subject if isinstance(subject, list) else [subject]}

        if course_number:
            course['course_number'] = {'$in':course_number if isinstance(course_number, list) else [course_number]}
        elif min_course_number or max_course_number:
            if not max_course_number: max_course_number = '9999'
            if not min_course_number: min_course_number = '0000'
            course['course_number'] = {'$gt':min_course_number, '$lt':max_course_number}

        if term:
            course['term'] = term
        elif min_term or max_term:
            if not max_term: max_term = '9999'
            if not min_term: min_term = '0000'
            course['term'] = {'$gt':min_term, '$lt':max_term}
        profIDs = []

        if professor_id:
            """professor_id = professor_id.split(', ')
            if isinstance(professor_id, list):
                for c in professor_id:
                    c = str(c)"""
            #else:
            profIDs = professor_id if isinstance(professor_id, list) else [professor_id]

        if professor_name:
            if not isinstance(professor_name, list):
                professor_name = [professor_name]
            for n in professor_name:
                allProfs = self.get_professor(name=n)
                for p in allProfs:
                    profIDs.append(p['id'])

        if distribution:
                course['distribution'] = {'$in': distribution if isinstance(distribution, list) else [distribution] }

        if profIDs:
            if isinstance(profIDs, list):
                profIDs = [str(c) for c in profIDs]
            else:
                profIDs = [profIDs]
            course['$or'] = [{'instructors':{'$in': profIDs}}]

        if keywords: #keyword search
            descRegex = '.*('
            for kw in keywords:
                if (kw.lower() not in self.words2ignore):
                    descRegex = descRegex + '(^|\s)' + kw + '|'

            descRegex = descRegex + 'zyvxzx).*'
            course['description'] = re.compile(descRegex, re.IGNORECASE)
            course['title'] = course['description']
            if '$or' not in course:
                course['$or'] = []
            course['$or'].extend([{'description':course.pop('description')}, {'title':course.pop('title')}])
        if pdf:
            course['pdf'] = {'$in':pdf if isinstance(pdf, list) else [pdf]}
            #course['term'] = CURRENT_SEMESTER
        if course_id:
            course['course_id'] = {'$in': course_id if isinstance(course_id, list) else [course_id]}
        if unique_course:
            course['unique_course'] = {'$in': unique_course if isinstance(unique_course, list) else [unique_course]}
        if not course:
            return []
        results = self.courseCol.find(course)

        # Replace crosslistings with primary listings
        results_list = []
        crosslistings = []
        for c in results:
            if 'primary_subject' in c:
                crosslistings.append({'subject': c['primary_subject'], 'course_number': c['primary_course_number'], 'term': c['term']})
            else:
                results_list.append(c)

        if crosslistings:
            new_results = self.courseCol.find({'$or': crosslistings});
            for c in new_results:
                results_list.append(c)

        if not unique:
            return self.rank(results_list, keywords)
        # Get the most recent semester of each course
        unique_courses = set()
        for c in results_list:
            i = c.get('unique_course', None)
            if i:
                unique_courses.add(i)
        courseIDs = []
        uniqueCourses = []
        for c in self.uniqueCourseCol.find({'course':{'$in' : list(unique_courses)}}):
            uniqueCourses.append(c)
            years = c.get('years', [])
            bestYear = {}
            for y in years:
                if bestYear.get('term', 0) < y.get('term', 1):
                    bestYear = y
            i = bestYear.get('id', None)
            if i:
                courseIDs.append(i)
        # Add a list of terms to each course
        results = self.courseCol.find({'_id': {'$in':courseIDs}})
        results_list = []
        for c in results:
            i = c['unique_course'];
            for d in uniqueCourses:
                if d['course'] == i:
                    c['all_terms'] = sorted([x['term'] for x in d['years']], reverse=True)
            results_list.append(c)
        # Do we want to return the whole thing, rather than the cursor?
        results_list = self.rank(results_list, keywords)
        return results_list

        
    # Returns the reviews for all past semesters of a given course.
    # Gives a list of dictionaries, each of which contains the info for
    # one semester, with the review, term number and professor
    # unique_id is the value of the unique_course field for a course
    def get_reviews(self, unique_id):
        # Get the list of all the semesters the course was offered
        course = self.uniqueCourseCol.find_one({'course': unique_id});
        if course:
            terms = course.get('years', [])
        else:
            terms = []
        term_ids = [t['id'] for t in terms]
        offerings = self.courseCol.find({'_id' : {'$in' : term_ids}}, sort=[('term', pymongo.DESCENDING)])
        reviews = []
        for i in offerings:
            semester = {}
            semester['term'] = i.get('term', []);
            semester['instructors'] = i.get('instructors', []);
            semester['review_text'] = i.get('review_text', []);
            semester['review_Nums'] = i.get('review_Nums', []);
            reviews.append(semester)

        return reviews

    # Function to return all courses in the database.
    # For testing purposes-- probably should not be used.
    def all_courses(self):
        results = self.courseCol.find()
        unique = []
        for result in results:
            if not 'primary_subject' in result:
                unique.append(result)
        return unique
        
    def annotate(self):
        # Get all courses
        results = self.courseCol.find()
        # Filter out crosslistings
        unique = []
        for result in results:
            if not 'primary_subject' in result:
                unique.append(result)
        # Set stuff up to deal with HTML tags
        parser = HTMLParser.HTMLParser()
        regex = re.compile(r'<.*?>')
        # Annotate
        for semester in unique:
            # Unescape and de-tag HMTL
            if 'description' in semester and semester['description']:
                semester['description'] = parser.unescape(semester['description'])
            if 'readings' in semester:
                for reading in semester['readings']:
                    for key in reading:
                        reading[key] = parser.unescape(reading[key])
            # Write professor names
            if 'instructors' in semester:
                semester['profs'] = []
                for instructor in semester['instructors']:
                    semester['profs'].append(self.get_professor(id_number=instructor)[0])
            # Add nice semester names
            if 'term' in semester:
                term_no = int(semester['term'])
                semester['term_name'] = term_name(term_no)
            # Make the list of all terms
            unique_course = self.uniqueCourseCol.find_one({'course': semester['unique_course']})
            if unique_course:
                semester['all_terms'] = sorted([x['term'] for x in unique_course['years']], reverse=True)
            # Add more nice semester names
            # Does nothing at the moment b/c all_terms is written by get_course. TODO: fix.
            if 'all_terms' in semester:
                # Add more nice semester names
                all_named_terms = OrderedDict()
                for term in semester['all_terms']:
                    all_named_terms[term] = term_name(int(term))
                semester['all_named_terms'] = all_named_terms
            # Add aggregated review data
            reviews = self.get_reviews(semester['unique_course'])
            current_weight = STARTING_WEIGHT
            total_weight = dict((category, 1.0) for category in RATING_CATEGORIES)
            weighted_rating = dict((category, 3.8) for category in RATING_CATEGORIES)
            seen_one = dict((category, False) for category in RATING_CATEGORIES) # To make sure we are getting some ratings
            for review in reviews:
                # Skip reviews for terms later than the one being viewed
                if int(review['term']) > int(semester['term']):
                    continue
                # Skip terms that don't have any reviews
                if not review['review_Nums']:
                    continue
                # Update weights
                current_weight = current_weight * DECAY_FACTOR
                # Add up ratings by category
                for category in RATING_CATEGORIES:
                    if category in review['review_Nums']:
                        seen_one[category] = True
                        for i, count in enumerate(review['review_Nums'][category]):
                            weighted_rating[category] += current_weight * float(count) * (5 - i)
                            total_weight[category] += current_weight * float(count)
            for category in RATING_CATEGORIES:
                if seen_one[category]:
                    final_average = weighted_rating[category] / total_weight[category]
                    semester[category + "_mean"] = "{0:.2f}".format(final_average)
                    for i, cutoff in enumerate(RATINGS_COLOR_SCALE):
                        if final_average > cutoff:
                            semester[category + '_color'] = 'rating_color_%s' % i
                    """if final_average > 4.6:
                        semester[category + '_color'] = 'rating_color_1'
                    elif final_average > 4.4:
                        semester[category + '_color'] = 'rating_color_2'
                    elif final_average > 4.2:
                        semester[category + '_color'] = 'rating_color_3'
                    elif final_average > 4.0:
                        semester[category + '_color'] = 'rating_color_4'
                    elif final_average > 3.8:
                        semester[category + '_color'] = 'rating_color_5'
                    elif final_average > 3.6:
                        semester[category + '_color'] = 'rating_color_6'
                    elif final_average > 3.4:
                        semester[category + '_color'] = 'rating_color_7'
                    elif final_average > 3.2:
                        semester[category + '_color'] = 'rating_color_8'
                    elif final_average > 0.0:
                        semester[category + '_color'] = 'rating_color_9'"""
            self.courseCol.save(semester)
