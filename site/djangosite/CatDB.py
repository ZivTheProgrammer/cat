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

        For example:
        get_course(course_number='201', subject=['MAT', 'COS', 'ELE'])
        would return whichever of MAT201, COS201 and ELE201 that exist,
        from every semester
    """
    # TODO: Add keyword search in descriptions, etc.
    def get_course(self, course=None, subject=None, course_number=None,
            min_course_number='000', max_course_number='999', professor_id=None,
            professor_name=None, term=None, min_term='0000', max_term='9999',
            distribution=None, description=None):
        #TODO: make sure all of these are strings
        if course:
            course = course.split(', ');
            if isinstance(course,list):
                for c in course:
                    c = str(c)
            else:
                return self.courseCol.find(course)
        else:
            course = {}

        if subject:
            subject = subject.split(', ');
            if isinstance(subject,list):
                for c in subject:
                    c =str(c)
            else:
                course['subject'] = { '$in':subject if isinstance(subject, list) else [subject]}

        if course_number:
            course_number = course_number.split(', ');
            if isinstance(course_number,list):
                for c in course_number:
                    c =str(c)
            else:
                course['course_number'] = {'$in':course_number if isinstance(course_number, list) else [course_number]}
        else:
            course['course_number'] = {'$gt':min_course_number, '$lt':max_course_number}

        if term:
            term = term.split(', ');
            if isinstance(term, list):
                for c in term:
                    c = str(c)
            else:
                course['term'] = term
        else:
            course['term'] = {'$gt':min_term, '$lt':max_term}
        profIDs = []

        if professor_id:
            professor_id = professor_id.split(', ')
            if isinstance(professor_id, list):
                for c in professor_id:
                    c = str(c)
            else:
                profIDs = professor_id if isinstance(professor_id, list) else [professor_id]

        if professor_name:
            professor_name = professor_name.split(', ');
            if not isinstance(professor_name, list):
                professor_name = [professor_name]
            for n in professor_name:
                allProfs = self.get_professor(name=n)
                for p in allProfs:
                    profIDs.append(p['id'])

        if profIDs:
            profIDs = profIDs.split(', ')
            if isinstance(profIDs, list):
                for c in profIDs:
                    c = str(c)
            else:
                course['instructors'] = {'$in': profIDs}

        if distribution:
            distribution = distribution.split(', ')
            if isinstance(distribution, list):
                for c in distribution:
                    c = str(c)
            else:
                course['distribution'] = {'$in': distribution if isinstance(distribution, list) else [distribution] }

        if description: #keyword search
            keywords = description.split()
            descRegex = '.*'
            for kw in keywords:
                descRegex = descRegex + kw + '|'
            descRegex = descRegex + '.*'
            course['description'] = re.compile(descRegex, re.IGNORECASE)
        
        if not course:
            return None
        else:
            return self.courseCol.find(course)

