from pymongo import MongoClient
import re
import string
import pprint

""" A class that provides functions to get information from our database
    of courses. To use, create a CatDB object:
        db = CatDB()
    then call the various functions on it:
        db.getProfessorInfo(name='Kernighan')
"""

CURRENT_SEMESTER = '1142'

class CatDB:

    words2ignore = ['the', 'be', 'to', 'of', u'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'there'];

    def __init__(self):
        self.connection = MongoClient()
        self.db = self.connection.cat_database
        self.courseCol = self.db.courses
        self.profCol = self.db.instructors
        self.studentCol = self.db.students
        self.uniqueCourseCol = self.db.unique

    def get_student(self, netID):
        course_list = self.studentCol.find_one({'netID': netID});
        if not course_list:
            course_list = {}
        return course_list
        
    def add_course(self, netID, courseList):
        if (self.studentCol.find_one({'netID': netID}) is None):
            entry = {};
            entry['netID'] = netID;
            if isinstance(courseList, list):
                entry['courseList'] = courseList;
            else:
                entry['courseList'] = [courseList];
            self.studentCol.insert(entry);
        else:
            entry = self.studentCol.find_one({'netID': netID});
            if isinstance(courseList, list):
                for course in courseList:
                    if course not in entry['courseList']:
                        entry['courseList'].append(course);
            else:
                print entry['courseList']
                entry['courseList'].append(courseList);
            # put updated things back
            self.studentCol.update({'netID': netID},
                                   {
                    '$set': {'courseList': entry['courseList']},
                    })

    def remove_course(self, netID, courseList):
        # check for if course is not there then you can't remove it
        if (self.studentCol.find_one({'netID': netID}) is None):
            sys.stderr.write('you tried to remove a course when the student has no courses!');
        else:
            entry = self.studentCol.find_one({'netID': netID});
            if isinstance(courseList, list):
                for course in courseList:
                    if course in entry['courseList']:
                        entry['courseList'].remove(course);
            else:
                entry['courseList'].remove(courseList);
            # put updated things back
            self.studentCol.update({'netID': netID},
                                   {
                    '$set': {'courseList': entry['courseList']},
                    })

    # Returns a list of professors with matching id and name
    # (name can be partial, id cannot)
    def get_professor(self, name=None, id_number=None):
        prof = {}
        if not name and not id_number:
            return None
        if id_number:
            prof['id'] = id_number
        if name: # regex to search for parts of names
            nameRegex = '.*(^|\s)' + string.join(name.split(), '.*') + '.*'
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
            print totalscore
        # sort by score
        #for c in sorted(scores, key = scores.get, reverse = True):
            # Don't do this! The entries have been modified between getting them from the db
            # and this ranking
            #courses_ranked.append(self.courseCol.find_one({'course_id': c}));
        #print '------------------------'
        #print list_courses
        print '****************'
        #print sorted(list_courses, key=lambda course: course['score'], reverse = True);
        
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
#        print self.courseCol
#        print self.db

        #TODO: make sure all of these are strings
        if course:
            return self.courseCol.find(course)
        else:
            course = {}
            
        if time:
            if not isinstance(time, list):
                time = [time]
            course['term'] = CURRENT_SEMESTER
            course['classes'] =  { 
                '$elemMatch': {
                    'section': re.compile('[LCS].*', re.I),
                    'starttime': {'$in': time},
                    }
                }
            
        if day:
            if not isinstance(day, list):
                day = [day]
            regex = '.*('
            for d in day:
                if (d == "t") or (d == "T"):
                    regex = regex +  "(t[^h])|"
                else:
                    regex = regex + d + "|"
            regex = regex + "ZYX).*"
            course['term'] = CURRENT_SEMESTER
            course['classes'] =  { 
                '$elemMatch': {
                    #'section': {'$in': ['L01', 'C01', 'C02', 'C03', 'S01']}, # FIX
                    'section': re.compile('[LCS].*', re.I),
                    'days': re.compile(regex, re.IGNORECASE)  #{'$in': day}
                    }
                }
            
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
                    descRegex = descRegex + kw + '|'

            descRegex = descRegex + 'zyvxzzxzx).*'
            course['description'] = re.compile(descRegex, re.IGNORECASE)
            course['title'] = course['description']
            if '$or' not in course:
                course['$or'] = []
            course['$or'].extend([{'description':course.pop('description')}, {'title':course.pop('title')}])
            print "regex: ", descRegex

        if pdf:
            course['pdf'] = {'$in':pdf if isinstance(pdf, list) else [pdf]}
        if course_id:
            course['course_id'] = {'$in': course_id if isinstance(course_id, list) else [course_id]}
        if unique_course:
            course['unique_course'] = {'$in': unique_course if isinstance(unique_course, list) else [unique_course]}
            
        print "search query: ",  course
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
            #return results_list
            return self.rank(results_list, keywords);
        # Get the most recent semester of each course
        unique_courses = set()
        for c in results_list:
            i = c.get('unique_course', None)
            if i:
                unique_courses.add(i)
        #print unique_courses
        courseIDs = []
        uniqueCourses = []
        for c in self.uniqueCourseCol.find({'course':{'$in' : list(unique_courses)}}):
            #print c
            uniqueCourses.append(c)
            years = c.get('years', [])
            bestYear = {}
            for y in years:
                if bestYear.get('term', 0) < y.get('term', 1):
                    bestYear = y
            i = bestYear.get('id', None)
            if i:
                courseIDs.append(i)
        #print 'ids:', courseIDs
        # Add a list of terms to each course
        results = self.courseCol.find({'_id': {'$in':courseIDs}})
        results_list = []
        for c in results:
            i = c['unique_course'];
            for d in uniqueCourses:
                #print i, d['course']
                if d['course'] == i:
                    c['all_terms'] = sorted([x['term'] for x in d['years']], reverse=True)
            #print c
            results_list.append(c)
        # Do we want to return the whole thing, rather than the cursor?
        #if len(results_list) < 100: # Luke's hack to prevent returning every course in the DB. Need to improve.
        results_list = self.rank(results_list, keywords);
        #print "returning lists of courses...", results_list
        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(results_list)        
        #print results_list
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
        offerings = self.courseCol.find({'_id' : {'$in' : term_ids}})
        reviews = []
        for i in offerings:
            semester = {}
            semester['term'] = i.get('term', []);
            semester['instructors'] = i.get('instructors', []);
#            semester['reviews'] = i.get('reviews', []);
            semester['review_text'] = i.get('review_text', []);
            semester['review_Nums'] = i.get('review_Nums', []);
            reviews.append(semester)

        return reviews
