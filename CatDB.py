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

    
    # Returns a list of professors with matching id and name
    # (name can be partial, id cannot)
    def get_professor(self, name=None, id_number=None):
        prof = {}
        if not name and not id_number:
            return None
        if id_number:
            prof['id'] = id_number
        if name: # regex to search for parts of names
            print 'searching for name: ' + name
            nameRegex = '.*' + string.join(name.split(), '.*') + '.*'
            prof['name'] = re.compile(nameRegex, re.IGNORECASE)
        return self.profCol.find(prof)

    # Returns a course that matches all the given information
    # course can be a dict with all this info; if it's provided, everything
    # else is ignored, and it is passed to the search directly
    # If course number/term is specified, min/max values are ignored
    # If professor id is given, professor name is ignored
    def get_course(self, course=None, subject=None, course_number=None,
            min_course_number='000', max_course_number='999', professor_id=None,
            professor_name=None, term=None, min_term='0000', max_term='9999'):
        #TODO: make sure all of these are strings
        if course:
            return self.courseCol.find(course)
        else:
            course = {}
        if subject:
            course['subject'] = subject
        if course_number:
            course['course_number'] = course_number
        else:
            course['course_number'] = {'$gt':min_course_number, '$lt':max_course_number}
        if term:
            course['term'] = term
        else:
            course['term'] = {'$gt':min_term, '$lt':max_term}
        if professor_id:
            course['instructors'] = {'$in': [professor_id]}
        elif professor_name:
            allProfs = self.get_professor(name=professor_name)
            profIDs = []
            for p in allProfs:
                profIDs.append(p['id'])
            course['instructors'] = {'$in': profIDs}
        
        print 'searching for', course
        if not course:
            return None
        else:
            return self.courseCol.find(course)

