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


action = sys.argv[1]

if action == 'build':
    print "building the database from scratch"
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
        print subCode
        # Get all the courses for each subject
        sleep(.5)
        fCourse = urlopen(feed + "?term=" + termCode + "&subject=" + subCode)
        courses = ET.parse(fCourse)
        for course in courses.iter(ns + 'course'):
            catNum = course.findall(ns + 'catalog_number')
            if len(catNum) > 1:
                print "ERROR: course has more than one number"
            print catNum[0].text
            title = course.find(ns + 'title').text
            print title
            description = course.find(ns + 'detail').find(ns + 'description').text
            print description
            profs = []
            instructors = course.iter(ns + 'instructor')
            for i in instructors:
                profs.append((i.find(ns + 'emplid').text, i.find(ns + 'first_name').text,
                    i.find(ns + 'last_name').text))
            print profs
            break
        break
    break

