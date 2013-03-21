from django import forms

class CourseNumberForm(forms.Form):
    subject = forms.CharField()
    course_number = forms.CharField()
    
