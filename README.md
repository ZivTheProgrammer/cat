cat
===

A project for COS 333 by Noah Apthorpe, Garrett Disco, Luke Paulsen, Jocelyn Tang, and Natalie Weires


Database stuff:
If you want to build the database on your machine, you need Python version 2.7
(at least), MongoDB, and pymongo. To build the db, have a mongo server running
('mongod' from the command line), then call 'python scrapeClasses.py build'.
For now, it just gets a small subset of all the courses.

Django:
To run the Django development server, open a command-line window, navigate to
cat/site, and type 'python manage.py runserver'. Then navigate to 'localhost:8000'
in your browser to view the site homepage.