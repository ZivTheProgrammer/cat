from pymongo import MongoClient
import argparse
from bs4 import BeautifulSoup
from bs4 import Tag
from collections import OrderedDict
import itertools
import json
import os
import re
import StringIO
#import nltk
import operator

# By Candy Button, Fall 2012 Independent Work with Brian Kernighan

# Using the Natural Language Toolkit:
# Bird, Steven, Edward Loper and Ewan Klein (2009). Natural Language Processing with Python. O'Reilly Media Inc.


def v(text):
    if Parser.VERBOSE:
        print text;

def readfile(filename):
    contents = None;
    with open(filename, 'r') as f:
        contents = f.read()
    return contents

def soupfile(filename):
    html = readfile(filename)
    return BeautifulSoup(html)

def isdatafile(filename):
    # TODO make this actually work!
    return filename == "CBE245_140773"
    return False

def isadvicefile(filename):
    # TODO
    return re.match(".*_a\Z", filename)

def coursenum_from_filename(filename):
    match = re.search("^.*_", filename)
    coursenum = match.group(0)[0:-1]
    return coursenum

class Parser:

    SAVE_FILE = "state_of_parser.json"
    VERBOSE = False

    QUESTIONS = {
            re.compile("overall quality of the lectures", re.I) : "lectures",
            re.compile("overall quality of the [written|writing] assignments", re.I): "assignments",
            re.compile("overall quality of the readings", re.I): "readings",
            re.compile("overall quality of the precepts", re.I): "precepts",
            re.compile("overall quality of the classes", re.I): "classes",
            re.compile("overall quality of the [course|writing seminar]", re.I): "overall"
            }
    all_questions = set()

    def __init__(self):
        self.data = {}
        self.worddict={}

    def nextfilename(self):
        pass

    def load(self):
        try:
            f = open(Parser.SAVE_FILE, 'r')
            if f == None:
                return False
            self.data = json.load(f);
            f.close()
            v("******** LOADED DATA *******\n")
            return True
        except IOError:
            print "Failed loading data; file %s not readable" % Parser.SAVE_FILE
            print "searching for... ", course
            return False

    def save(self):
        f = open(Parser.SAVE_FILE, 'w')
        json.dump(self.data, f)
        f.close()

    # This function requires the natural language toolkit - you must download it and 
    # uncomment the import statement (import nltk) at the top of this file
    def parse_words(self, sentences):
        words = nltk.word_tokenize(sentences)
        tags = nltk.pos_tag(words)
        
        for tag in tags:
            if tag[1] == 'JJ':
                word = tag[0];
                if self.worddict.get(word) == None:
                    self.worddict[word] = 1;
                else:
                    self.worddict[word] += 1;

    def parse_advice(self, text, coursenum = None, term=None):
        if not coursenum:
            coursenum = coursenum_from_filename(text);
        courseNumber = coursenum[4:]
        courseDept = coursenum[:3]

        #soup = soupfile(filename)
        soup = BeautifulSoup(text)
        tag = soup.find(name="ul")
        if tag == None:
            print "Couldn't find advice list for ", coursenum
            return False
        reviews = []
        for item in tag.children:
            if isinstance(item, Tag) and item.name == "li":
                # Save the data in the Parser object
                # if self.data.get(filename) == None:
                #    self.data[filename] = []
                # self.data[filename].append(item.string.strip()) 

                # Or parse individual words from the string
                # self.parse_words(item.string.strip()); 

                # Print the string if in verbose mode
                #v(coursenum)
                #v(item.string.strip())

                # INSERT YOUR CODE HERE,
                # use item.string.strip() as a single student's advice
                reviews.append(item.string.strip())
        # Add reviews to the database
        courseCol.update({'term':term, 'course_number': courseNumber, 'subject': courseDept}, {'$set': {'review_text': reviews}})
        return True

    def parse_numbers(self, text, coursenum=None, term=None):
        #soup = soupfile(filename)
        #print 'Parsing numbers'
        soup = BeautifulSoup(text)
        if not coursenum:
            coursenum = coursenum_from_filename(text);
        table = soup.find(name="table")
        table = table.find_next("table")
        table = table.find_next("table")
        # TODO: fill out the rest of the BeautifulSoup parsing to get the data here
        # INSERT YOUR CODE HERE

        courseNumber = coursenum[4:]
        courseDept = coursenum[:3]

        ratings = {}
        row = table.find_next("tr").find_next("tr").find_next("tr")
#        print lectures_row
        #print row, len(row.contents)
        while row and len(row.contents) > 1:
            #print "In a new row"
            # Figure out which question this is...
            question_name = ''
            question = row.find_next("td").string
            #print question
            for q in self.QUESTIONS:
                #print 'looking at question', q
                if q.search(question):
                    #print 'question matches'
                    #This question matches
                    question_name = self.QUESTIONS[q]
                    break
            if not question_name:
                row = row.find_next_sibling("tr").find_next_sibling("tr")
                continue
            #print row
            #print 'row contains ', len(row.contents), 'objects'
            self.all_questions.add(question)

            cell = row.find_next("td").find_next("td").find_next("td").find_next("td")
            numbers = []
            for i in range(5):
                numbers.append(cell.string.replace('%', ''))
                cell = cell.find_next_sibling("td")
            cell = cell.find_next_sibling("td")
            mean = cell.string.strip()
            row = row.find_next_sibling("tr").find_next_sibling("tr")
            #print numbers, mean
            ratings[question_name] = numbers
            ratings[question_name + '_mean'] = mean
        #print ratings


        """overall_row = precepts_row.find_next("tr").find_next("tr")
#        print overall_row
        cell = overall_row.find_next("td").find_next("td").find_next("td").\
find_next("td")
        ratings["overall"] = []
        for i in range(5):
            ratings["overall"].append(cell.string)
            cell = cell.find_next_sibling("td")
        cell = cell.find_next_sibling("td")
        ratings["overall_mean"] = cell.string.strip()"""

#        for c in courseCol.find({'subject': courseDept}):
#            print c
#        entry['review_Nums'] = entry.['review_Nums'].append(ratings); # FIX
#        entry['text_reviews'] = entry.['text_reviews'].append(text_ratings);
        print "searching for: ", courseNumber, courseDept, term
        courseCol.update({'term': term, 'course_number': courseNumber, 'subject': courseDept}, {'$set': {'review_Nums': ratings}})
        #print ratings
        entry = courseCol.find_one({'term':term, 'subject': courseDept, 'course_number': courseNumber}); # FIX??
        
        if (entry is None):
            print 'Course whose reviews you were trying to update is not found!'
        else:
            print 'Added reviews to the database!!!'
            #print entry;
        #print self.all_questions

    def parse_dir(self):
        # "." means the current directory
        files = filter(os.path.isfile, os.listdir('.'))
        v("Advice files:")
        for file in itertools.ifilter(isadvicefile, files):
            v(file)
            
            html = readfile(filename)
            self.parse_advice(file)
        v("Data files:")
        for file in itertools.ifilter(isdatafile, files):
            v(file)
            
            html = readfile(filename)
            self.parse_numbers(html)
        v(self.data)

    def parse_files(self, numerical, text, coursenum, term):
        print "parsing files!"
        self.parse_advice(text, coursenum, term)
        self.parse_numbers(numerical, coursenum, term)

    def print_words(self):
        list = sorted(self.worddict.iteritems(), key=operator.itemgetter(1))
        for tuple in list:
            print "%s: %d" % tuple

connection = MongoClient()
db = connection.cat_database
courseCol = db.courses # All course instances
uniqueCourseCol = db.unique
#profCol = db.instructors

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="print out lots of junk for debugging", action="store_true")
    args = parser.parse_args()
    Parser.VERBOSE = args.verbose
    try:
    # Loading and saving don't do anything unless you store stuff in the parser's data field, 
    # and the parsing function ignores the loaded data, so there's no use in saving/loading here.
    # p.load();

        p.parse_dir();

    # Only if you've saved words in the parser's worddict...
    # p.print_words();
    # p.save();
    except Exception, e: 
        z = e
        print z
else:
    Parser.VERBOSE = True

p = Parser();
