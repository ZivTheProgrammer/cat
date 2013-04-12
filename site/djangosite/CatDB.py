from pymongo import MongoClient
import re
import string

""" A class that provides functions to get information from our database
    of courses. To use, create a CatDB object:
        db = CatDB()
    then call the various functions on it:
        db.getProfessorInfo(name='Kernighan')
"""

class CatDB:

    def __init__(self):
        self.connection = MongoClient()
        self.db = self.connection.cat_database
        self.courseCol = self.db.courses
        self.profCol = self.db.instructors
	self.studentCol = self.db.students
        self.uniqueCourseCol = self.db.unique

    def get_student(self, netID):
        return self.studentCol.find_one({'netID': netID});

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
            nameRegex = '.*' + string.join(name.split(), '.*') + '.*'
            prof['name'] = re.compile(nameRegex, re.IGNORECASE)
        return self.profCol.find(prof)

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
    # TODO: Add keyword search in descriptions, etc.
    def get_course(self, course=None, subject=None, course_number=None,
            min_course_number='000', max_course_number='999', professor_id=None,
            professor_name=None, term=None, min_term='0000', max_term='9999',
            distribution=None, pdf=None, unique=True):
        #TODO: make sure all of these are strings
        if course:
            return self.courseCol.find(course)
        else:
            course = {}
        if subject:
            # TODO: Make all capital letters
            course['subject'] = { '$in':subject if isinstance(subject, list) else [subject]}
        if course_number:
            course['course_number'] = {'$in':course_number if isinstance(course_number, list) else [course_number]}
        else:
            course['course_number'] = {'$gt':min_course_number, '$lt':max_course_number}
        if term:
            course['term'] = term
        else:
            course['term'] = {'$gt':min_term, '$lt':max_term}
        profIDs = []
        if professor_id:
            profIDs = professor_id if isinstance(professor_id, list) else [professor_id]
        if professor_name:
            if not isinstance(professor_name, list):
                professor_name = [professor_name]
            for n in professor_name:
                allProfs = self.get_professor(name=n)
                for p in allProfs:
                    profIDs.append(p['id'])
        if profIDs:
            course['instructors'] = {'$in': profIDs}
        if distribution:
            course['distribution'] = {'$in': distribution if isinstance(distribution, list) else [distribution] }
        if pdf:
            course['pdf'] = {'$in':pdf if isinstance(pdf, list) else [pdf]}

        if not course:
            return None
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
            return results_list
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
                    c['all_terms'] = [x['term'] for x in d['years']]
            results_list.append(c)
        # Do we want to return the whole thing, rather than the cursor?

        return results_list
        


    # Returns the reviews for all past semesters of a given course.
    # Gives a list of dictionaries, each of which contains the info for
    # one semester, with the review, term number and professor
    def get_reviews(self, unique_id):
        # Get the list of all the semesters the course was offered
        course = self.uniqueCourseCol.find_one({'course': unique_id});
        if course:
            terms = course.get('years', [])
        else:
            terms = []
        term_ids = [t['_id'] for t in terms]
        offerings = self.courseCol.find({'_id' : {'$in' : term_ids}})
        reviews = []
        for i in offerings:
            semester = {}
            semester['term'] = i['term']
            semester['instructors'] = i['instructors'];
            semester['reviews'] = i.get('reviews', []);
            reviews.append(semester)

        return reviews
