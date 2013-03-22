#!/usr/bin/env python
"""
Python routines for scraping data from Princeton's registrar.
by Alex Ogier

If run as a python script, the module will dump information on all the courses available
on the registrar website as a JSON format.

Check out LIST_URL to adjust what courses are scraped.

Useful functions are scrape_page() and scrape_all().
"""

from datetime import datetime
import json
import re
import sqlite3
import sys
import urllib2
from BeautifulSoup import BeautifulSoup

#TERM_CODE = 1122  # seems to be fall 11-12
#TERM_CODE = 1124  # so 1124 would be spring 11-12
                  # 1134 is definitely spring 13 (course offerings link)`
TERM_CODE = 1134

URL_PREFIX = "http://registrar.princeton.edu/course-offerings/"
LIST_URL = URL_PREFIX + "search_results.xml?term={term}"
COURSE_URL = URL_PREFIX + "course_details.xml?courseid={courseid}&term={term}"

COURSE_URL_REGEX = re.compile(r'courseid=(?P<id>\d+)')
PROF_URL_REGEX = re.compile(r'dirinfo\.xml\?uid=(?P<id>\d+)')
LISTING_REGEX = re.compile(r'(?P<dept>[A-Z]{3})\s+(?P<num>\d{3}[a-zA-Z]?)')

def get_course_list(search_page):
    "Grep through the document for a list of course ids."
    soup = BeautifulSoup(search_page)
    links = soup('a', href=COURSE_URL_REGEX)
    courseids = [COURSE_URL_REGEX.search(a['href']).group('id') for a in links]
    return courseids

def clean(str):
    "Return a string with leading and trailing whitespace gone and all other whitespace condensed to a single space."
    return re.sub('\s+', ' ', str.strip())

def get_course_details(soup):
    "Returns a dict of {courseid, area, title, descrip, prereqs}."
    area = clean(soup('strong')[1].findAllNext(text=True)[1])  # balanced on a pinhead
    pdf = clean(soup('strong')[1].findAllNext(text=True)[2])
    pdf_options = []
    if re.search("no audit|na", pdf, re.I):
        pdf_options.append("na")
    if re.search("npdf|(no pass/d/fail)", pdf, re.I):
        pdf_options.append("npdf")
    if re.search("p/d/f only", pdf, re.I):
        pdf_options.append("pdfonly")
    print pdf_options
    if pdf and not pdf_options:
        print "**** another pdf option: ", pdf
        print "\tPlease tell Natalie, so she can fix it!"
        print "\t(Or just do it yourself, if you want.)"

    if re.match(r'^\((LA|SA|HA|EM|EC|QR|ST|STN|STL)\)$', area):
        area = area[1:-1]
    else:
        area = ''

    match = re.match(r'\(([A-Z]+)\)', clean(soup('strong')[1].findNext(text=True)))
    pretitle = soup.find(text="Prerequisites and Restrictions:")
    descrdiv = soup.find('div', id='descr')
    readings = soup.find(text="Sample reading list:")
    grading = soup.find(text=re.compile("\n?Requirements/Grading:\n?"))

    grades = []
    if grading:
        prev = ''
        for g in grading.parent.findAllNext(text=True):
            if g.strip() and g.strip() != "Requirements/Grading:":
                grades.append(g.strip())
                # TODO: parse each line here
            if not prev and not g.strip():
                break
            prev = g.strip()

    readings_list = []
    if readings:
        # TODO: fix symbols like apostrophes
        author = None
        prev = 'something'
        # This assumes everything is always formatted the same, and
        # every book has a title and an author
        for sib in readings.parent.findAllNext(text=True):
            if not prev and not sib.strip():
                break
            prev = sib.strip()
            if sib.strip() == ',' and author:
                continue
            elif author and not sib.strip():
                author = None
                continue
            elif not author and sib.strip():
                author = sib.strip()
                continue
            elif author and sib.strip() and author != "Sample reading list:":
                readings_list.append({'title':sib.strip(), 'author':author})
                author = None
    
    return {
            #'courseid': COURSE_URL_REGEX.search(soup.find('a', href=COURSE_URL_REGEX)['href']).group('id'),
            'area': area,#[1:-1],    # trim parens #  match.group(1) if match != None else ''
            'title': clean(soup('h2')[1].string),
            'descrip': clean(descrdiv.contents[0] if descrdiv else ''),
            'prereqs': clean(pretitle.parent.findNextSibling(text=True)) if pretitle != None else '',
            'grading': grades,
            'readings': readings_list,
            'pdf': pdf_options
            }

def get_course_listings(soup):
    "Return a list of {dept, number} dicts under which the course is listed."
    listings = soup('strong')[1].string
    return [{'dept': match.group('dept'), 'number': match.group('num')} for match in LISTING_REGEX.finditer(listings)]

def get_course_profs(soup):
    "Return a list of {uid, name} dicts for the professors teaching this course."
    prof_links = soup('a', href=PROF_URL_REGEX)
    return [{'uid': PROF_URL_REGEX.search(link['href']).group('id'), 'name': clean(link.string)} for link in prof_links]

def get_single_class(row):
    "Helper function to turn table rows into class tuples."
    cells = row('td')
    time = cells[2].string.split("-")
    bldg_link = cells[4].strong.a
    return {
          'classnum': cells[0].strong.string,
          'days': re.sub(r'\s+', '', cells[3].strong.string),
          'starttime': time[0].strip(),
          'endtime': time[1].strip(),
          'bldg': bldg_link.string.strip(),
          'roomnum': bldg_link.nextSibling.string.replace('&nbsp;', ' ').strip()
          }

def get_course_classes(soup):
    "Return a list of {classnum, days, starttime, endtime, bldg, roomnum} dicts for classes in this course."
    class_rows = soup('tr')[1:] # the first row is actually just column headings
    # This next bit tends to cause problems because the registrar includes precepts and canceled
    # classes. Having text in both 1st and 4th columns (class number and day of the week)
    # currently indicates a valid class.
    return [get_single_class(row) for row in class_rows if row('td')[0].strong and row('td')[3].strong.string]

def scrape_page(page):
    "Returns a dict containing as much course info as possible from the HTML contained in page."
    soup = BeautifulSoup(page).find('div', id='contentcontainer')
    course = get_course_details(soup)
    course['listings'] = get_course_listings(soup)
    course['profs'] = get_course_profs(soup)
    course['classes'] = get_course_classes(soup)
    return course

def scrape_id(id):
    page = urllib2.urlopen(COURSE_URL.format(term=TERM_CODE, courseid=id))
    return scrape_page(page)

def scrape_id_term(id, term):
    page = urllib2.urlopen(COURSE_URL.format(term=term, courseid=id))
    return scrape_page(page)


def scrape_all():
    """
    Return an iterator over all courses listed on the registrar's site.

    Which courses are retrieved are governed by the globals at the top of this module,
    most importantly LIST_URL and TERM_CODE.

    To be robust in case the registrar breaks a small subset of courses, we trap
    all exceptions and log them to stdout so that the rest of the program can continue.
    """
    search_page = urllib2.urlopen(LIST_URL.format(term=TERM_CODE))
    courseids = get_course_list(search_page)

    n = 0
    for id in courseids:
        try:
            if n > 99999:
                return
            n += 1
            yield scrape_id(id)
        except Exception:
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write('Error processing course id {0}\n'.format(id))

if __name__ == "__main__":
    print scrape_id_term('009380', 1134)
    #print scrape_page('http://registrar.princeton.edu/course-offerings/course_details.xml?courseid=009380&term=1134')
    sys.exit()
    first = True
    for course in scrape_all():
        if first:
            first = False
        print '['
    else:
        print ','
    json.dump(course, sys.stdout)
    print ']'


