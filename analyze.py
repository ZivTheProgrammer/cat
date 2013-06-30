from pymongo import MongoClient
import pymongo
from datetime import datetime
import sys

connection = MongoClient()
db = connection.cat_database
studentCol = db.students
analytics = db.analytics

students = studentCol.find()

print "Analytics started June 30, 2013."
print "Running with command line arguments 'csv filename' will save some data in a file with that name"
print "(in case you want to do fancy real stuff with it)"
print
print "Number of users that have visited (ever): ", students.count()

now = datetime.now()
times = []

for s in students:
    if 'lastVisit' in s:
        diff = now - s['lastVisit']
        times.append(diff.total_seconds())

print
print "Seconds from last visit for each user:"
for t in sorted(times):
    print int(round(t))

data = {}
for a in analytics.find(sort=[('time', pymongo.ASCENDING)]):
    day = a['time'].date()
    entry = data.get(day, {}).get(a['type'], 0) + 1;
    if day not in data:
        data[day] = {}
    data[day][a['type']] = entry
    
csv = 'date,newUsers,addClass,removeClass\n'
print
print "%s\t\t%s\t%s\t%s" % ('date', 'new', 'add', 'remove');
for (day, counts) in data.items():
    print "%s\t%d\t%d\t%d" % (day.strftime('%x'), counts.get('newUser',0), counts.get('addClass',0), counts.get('removeClass',0))
    csv = csv + "%s,%d,%d,%d\n" % (day.strftime('%x'), counts.get('newUser',0), counts.get('addClass',0), counts.get('removeClass',0))

print

if len(sys.argv) > 2:
    if 'csv' in sys.argv:
        filename = sys.argv[sys.argv.index('csv')+1]
        f = open(filename, 'w')
        f.write(csv)
        f.close()
        print "Data written to the file", filename

