#!/usr/bin/env python
"""
Sanity test for the scraper module.
by Alex Ogier
"""

import scraper
import os
import re
from pprint import pprint

def run_tests():
  for name in os.listdir(os.getcwd()):
    if re.search('course_details.*\.html$', name):
      with open(name) as f:
        course = scraper.scrape_page(f.read())
        pprint(course)

if __name__ == "__main__":
  run_tests()
