import sys
import string
from time import sleep
from urllib import urlopen
import xml.etree.ElementTree as ET
from pymongo import MongoClient

if len(sys.argv) < 2:
    print "usage: scrapeClasses [build | update | add]"
    print "\tbuild: creates the database from scratch"
    print "\tupdate: checks for and new data or data that has changed, adding it to"
    print "\t\tthe database, without changing anything that hasn't changed"
    print "\t\t(even if that info is no longer posted)"
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
    sure = raw_input("Are you sure you want to delete the old database? ")
    if not sure.lower() in ['y', 'yes', 'yeah', 'yep']:
        sys.exit()
    print "building the database from scratch"
    # Delete the old database- be careful!
    db.drop_collection('courses')
    db.drop_collection('instructors')

elif action == 'update':
    print 'updating'

elif action == 'add':
    print 'looking for new semesters to add'
    # For now, this just adds any classes not in the db.
    # It doesn't check for things that have changed

# Get the list of available terms
fTerm = urlopen(feed + '?term=list')
terms = ET.parse(fTerm)

for term in terms.iter(ns + 'term'):
    termCode = term.find(ns + 'code').text
    # If we're just updating with a new semester, don't look at old ones
    if action == 'add' and courseCol.find_one({'term':termCode}):
        continue
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
                # If we haven't seen this prof before, add them to the db
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
                entry['crosslistings'].append(crossEntry)
                # if this listing isn't in the db, add it
                if not courseCol.find_one(crossEntry):
                    crossEntry = crossEntry.copy() # don't want to change the one in entry
                    crossEntry['primary_subject'] = entry['subject']
                    crossEntry['primary_course_number'] = entry['course_number']
                    courseCol.insert(crossEntry)

            courseCol.insert(entry)
            break
        
    break
#for p in profCol.find():
#    print p
#for c in courseCol.find():
#    print c
print "Done! Uncomment the things before this print statement to see what's in the database."
print "Comment the break statements to get more than one semester and more than one course per subject"

