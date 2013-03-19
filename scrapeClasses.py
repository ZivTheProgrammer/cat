import sys
import string
from time import sleep
from urllib import urlopen
import xml.etree.ElementTree as ET
from pymongo import MongoClient

if len(sys.argv) < 2:
    print "usage: scrapeClasses [build | update | add]"
    print "\tbuild: creates the database from scratch"
    print "\tupdate: checks for any data that has changed, and updates the database,"
    print "\t\tbut without adding any new semesters"
    print "\tadd: looks for any new semesters of data, and adds them to the database"
    sys.exit()

feed = 'http://etcweb.princeton.edu/webfeeds/courseofferings/'
ns = '{http://as.oit.princeton.edu/xml/courseofferings-1_3}'

connection = MongoClient()
db = connection.cat_database
courseCol = db.courses
profCol = db.instructors

action = sys.argv[1]

if action == 'build':
    print "building the database from scratch"
    # Delete the old database- be careful!
    db.drop_collection('courses')
    db.drop_collection('instructors')

elif action == 'update':
    print "updating"

# Get the list of available terms
fTerm = urlopen(feed + '?term=list')
terms = ET.parse(fTerm)


for term in terms.iter(ns + 'term'):
    termCode = term.find(ns + 'code').text
    print "term code: " + termCode
    # Get the data from each term, starting with list of subjects:
    fSub = urlopen(feed + '?term=' + termCode + "&subject=list")
    subjects = ET.parse(fSub)
    # Get data for each subject
    for sub in subjects.iter(ns + 'subject'):
        subCode = sub.find(ns + 'code').text
        # Get all the courses for each subject
        sleep(.5)
        fCourse = urlopen(feed + "?term=" + termCode + "&subject=" + subCode)
        courses = ET.parse(fCourse)
        for course in courses.iter(ns + 'course'):
            entry = {}
            entry['term'] = termCode
            # Find the subject code used for the primary listing (not necessarily
            # the subject we searched by
            entry['subject'] = courses.find('.//' + ns + 'subjects/' + ns
                    + 'subject/' + ns + 'code').text
            entry['subject']
            catNum = course.findall(ns + 'catalog_number')
            if len(catNum) > 1:
                print "ERROR: course has more than one number"
            entry['course_number'] = catNum[0].text
            # Check whether we already added this class (e.g. if it was crosslisted)
            # Presumably the term, dept and number uniquely identify it
            print entry
            if courseCol.find_one(entry):
                # continue TODO: put this back
                break
            
            entry['course_id'] = course.find(ns + 'course_id').text
            title = course.find(ns + 'title').text
            description = course.find(ns + 'detail').find(ns + 'description').text
            profs = []
            instructors = course.iter(ns + 'instructor')
            for i in instructors:
                profId = i.find(ns + 'emplid').text
                profs.append(profId)
                if not profCol.find_one({'id':profId}):
                    prof = {}
                    prof['id'] = profId
                    prof['first_name'] = i.find(ns + 'first_name').text
                    prof['last_name'] = i.find(ns + 'last_name').text
                    prof['name'] = prof['first_name'] + ' ' + prof['last_name']
                    profCol.insert(prof)
            entry['instructors'] = profs
            crosslistings = course.iter(ns + 'crosslisting')
            if crosslistings:
                entry['crosslistings'] = []
            for c in crosslistings:
                crossEntry = {}
                crossEntry['term'] = termCode
                crossEntry['subject'] = c.find(ns + 'subject').text
                crossEntry['course_number'] = c.find(ns + 'catalog_number').text
                # if this listing isn't in the db, add it
                entry['crosslistings'].append(crossEntry)
                if not courseCol.find_one(crossEntry):
                    crossEntry = crossEntry.copy() # don't want to change the one in entry
                    crossEntry['primary_subject'] = entry['subject']
                    crossEntry['primary_course_number'] = entry['course_number']
                    courseCol.insert(crossEntry)

            courseCol.insert(entry)
            break
        
    break
for p in profCol.find():
    print p
for c in courseCol.find():
    print c

