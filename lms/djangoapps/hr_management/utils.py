from collections import namedtuple

from hr_management.models import CourseAccessRequest

from instructor.offline_gradecalc import student_grades
from instructor.utils import DummyRequest
from student.models import CourseEnrollment
from courseware.courses import get_course_by_id
from django.contrib.auth.models import User

from datetime import datetime
import csv
import io


HrefLabel = namedtuple('HrefLabel', ['href', 'label'])

# Microsite value object. Primary use in templates
# the url members are intended for the HrefLabel above
MicrositeVO = namedtuple('MicrositeVO', ['home_url', 'management_url', 'microsite'])

def requested_access_for_course(course, user):
    """
    Return True if user is registered for course, else False
    """
    if user is None:
        return False
    if user.is_authenticated():
        return CourseAccessRequest.has_requested_access(user, course.id)
    else:
        return False

def generate_csv_grade_string(organization=None):
    """
    Create a CSV string that will be included in weekly report email
    """
    header = ['#full_name','email','organization','course_name','enrollment_date','progress','completion_date','score']
    encoded_header = [unicode(s).encode('utf-8') for s in header ]
    fp = io.BytesIO()
    writer = csv.writer(fp, quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(encoded_header)

    if not organization:
        student_list = User.objects.all()
    else:
        student_list = User.objects.filter(organizations__short_name=organization)

    request = DummyRequest()

    output_data = []
    for student in student_list:
        try:
            full_name = student.profile.name
        except: 
            continue
        try: 
            organization = student.organizations.all()[0]
        except: 
            organization = 'none'

        email = student.email
        for enrollment in student.courseenrollment_set.all(): 
            try:
                course = get_course_by_id(enrollment.course_id)
            except: 
                continue
            grade = student_grades(student, request, course)
            enrollment_date = enrollment.created
            course_name = course.display_name
            progress = ''
            completion_date = ''
            score = grade['percent']
            row = [
                full_name,
                email,
                organization,
                course_name,
                enrollment_date,
                progress,
                completion_date,
                score
            ]
            encoded_row = [unicode(s).encode('utf-8') for s in row]
            writer.writerow(encoded_row)

    raw_grade_data = fp.getvalue()
    fp.close()

    return raw_grade_data

def generate_microsite_vo(microsite, port=None):
    """
    Create a namedtuple of data to show in the UI

    We build our urls here to keep the view and template simpler

    Massage microsites to get the urls we want
    Use protocol relative URL

    Perhaps another option is creating custom template filters
    https://docs.djangoproject.com/en/1.8/howto/custom-template-tags/
    """
    port_str = ':{}'.format(port) if port else ''
    return MicrositeVO(
        home_url=HrefLabel(
            href='//{}{}'.format(microsite.site.domain, port_str),
            label=microsite.site),
        management_url=HrefLabel(
            href='//{}{}/hr-management/'.format(microsite.site.domain, port_str),
            label='manage'),
        microsite=microsite
    )
