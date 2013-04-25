import sys
import string
from time import sleep
from urllib import urlopen
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from scraper import scraper

if len(sys.argv) != 2 or sys.argv[1] not in ['build', 'update', 'add']:
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
courseCol = db.courses # All course instances
uniqueCourseCol = db.unique
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
    db.drop_collection('unique')

elif action == 'update':
    print 'updating'

elif action == 'add':
    print 'looking for new semesters to add'
    # For now, this just adds any classes not in the db.
    # It doesn't check for things that have changed


# Get the list of available terms
try:
    fTerm = urlopen(feed + '?term=list')
except:
    print "***********Couldn't load list of courses************"
    exit()
terms = ET.parse(fTerm)

for term in terms.iter(ns + 'term'):
    termCode = term.find(ns + 'code').text
    # If we're just updating with a new semester, don't look at old ones
    if action == 'add' and courseCol.find_one({'term':termCode}):
        continue
    print "term code: " + termCode
    # Get the data from each term, starting with list of subjects:
    try:
        fSub = urlopen(feed + '?term=' + termCode + "&subject=list")
    except:
        try:
            fSub = urlopen(feed + '?term=' + termCode + "&subject=list")
        except:
            print "***********Couldn't load term %s subject list************" % (term)
            continue
    subjects = ET.parse(fSub)
    # Get data for each subject
    for sub in subjects.iter(ns + 'subject'):
        subCode = sub.find(ns + 'code').text
        if subCode != "MAT" and subCode != "GLS":
            continue
        # Get all the courses for each subject
        sleep(.5)
        try:
            fCourse = urlopen(feed + "?term=" + termCode + "&subject=" + subCode)
        except:
            try:
                fCourse = urlopen(feed + "?term=" + termCode + "&subject=" + subCode)
            except:
                print "***********Couldn't load term %s and subject %s************" % (termCode, subCode)
                continue
            
        courses = ET.parse(fCourse)
        parent_map = dict((c, p) for p in courses.getiterator() for c in p)
        for course in courses.iter(ns + 'course'):
            entry = {}
            entry['term'] = termCode
            # Find the subject code used for the primary listing (not necessarily
            # the subject we searched by
            # TODO: make sure we get the right subject- there may be multiple on the page
            #entry['subject'] = courses.find('.//' + ns + 'subjects/' + ns
            #        + 'subject/' + ns + 'code').text
            entry['subject'] = parent_map[parent_map[course]].find(ns + 'code').text
            catNum = course.findall(ns + 'catalog_number')
            if len(catNum) > 1:
                print "ERROR: course has more than one number"
            entry['course_number'] = catNum[0].text
            # Check whether we already added this class (e.g. if it was crosslisted)
            # Presumably the term, dept and number uniquely identify it
            #print entry
            if courseCol.find_one(entry):
                continue #TODO: put this back
                #break
            print entry['subject'], entry['course_number']
            
            entry['course_id'] = course.find(ns + 'course_id').text
            entry['title'] = course.find(ns + 'title').text
            entry['description'] = course.find(ns + 'detail').find(ns + 'description').text
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
                    crossEntry['unique_course'] = entry['subject'] + entry['course_number']
                    courseCol.insert(crossEntry)
            if not entry['crosslistings']:
                del entry['crosslistings']
            # Now get data from the registrar site
            try:
                regData = scraper.scrape_id_term(entry['course_id'], entry['term'])
            except:
                print "***********Couldn't load registrar data for term %s, subject %s, number %s************" % (termCode, subCode, entry['course_number'])
                continue

            #print regData
            """
            if regData.get('prereqs', None):
                entry['prereqs'] = regData['prereqs']
            if regData.get('area', None):
                entry['distribution'] = regData['area']
            if regData.get('readings', None):
                entry['readings'] = regData['readings']
            if regData.get('grading', None):
                entry['grading'] = regData['grading']
            if regData.get('classes', None):
                entry['classes'] = regData['classes']
            if regData.get('pdf', None):
                entry['pdf'] = regData['pdf']
            if regData.get('assignments', None):
                entry['assignments'] = regData['assignments']
            """

            for key in regData.keys():
                if key in ['prereqs', 'distribution', 'readings', 'grading','classes',
                        'pdf', 'assignments', 'other_reqs', 'other_info']:
                    entry[key] = regData[key]

            # TODO: check for courses that have changed number, etc.
            entry['unique_course'] = entry['subject'] + entry['course_number']
            newId = courseCol.insert(entry)
            # Find in / add to the list of unique courses
            #print entry
            #print "New ID: ", newId
            uniqueCourseCol.update({'course':entry['unique_course']}, {'$push' : {'years': {'id': newId, 'term':entry['term'], 'instructors':entry['instructors']}}}, upsert=True)
            #print uniqueCourseCol.find_one({'course' : entry['unique_course']})
#            break
        
    break
#for p in profCol.find():
#    print p
#for c in courseCol.find():
#    print c
print "Done! Uncomment the things before this print statement to see what's in the database."
print "Comment the break statements to get more than one semester and more than one course per subject"

