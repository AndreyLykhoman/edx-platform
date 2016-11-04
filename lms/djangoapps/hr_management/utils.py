from hr_management.models import CourseAccessRequest

from instructor.offline_gradecalc import student_grades
from instructor.utils import DummyRequest
from student.models import CourseEnrollment
from courseware.courses import get_course_by_id
from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User

from datetime import datetime
import logging
import csv
import io

log = logging.getLogger(__name__)

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
    header = ['#full_name','email','organization','course_name','enrollment_date','completion_date','score']
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
            
            certificate = GeneratedCertificate.objects.filter(user=student).filter(course_id=course.id)
            if certificate:
                cert = certificate[0]
                completion_date = cert.created_date
            else:
                completion_date = ''
            score = grade['percent']
            row = [
                full_name,
                email,
                organization,
                course_name,
                enrollment_date,
                completion_date,
                score
            ]
            encoded_row = [unicode(s).encode('utf-8') for s in row]
            writer.writerow(encoded_row)

    raw_grade_data = fp.getvalue()
    fp.close()

    return raw_grade_data

from django.conf import settings
import boto
from boto.s3.key import Key
from datetime import datetime
def upload_report_string_to_s3(content, filename_prefix=''):
    """
    Takes the CSV grade string from generate_csv_grade_string and uploads to S3.
    Requires the Grade Bucket (used for instructor dashboard grade downloads) to be configured
    """
    grade_config = settings.GRADES_DOWNLOAD
    if grade_config['STORAGE_TYPE'] != 'S3':
        log.error('Cannot upload string to S3 if STORAGE_TYPE is \'{}\''.format(grade_config['STORAGE_TYPE']))
        return

    BUCKET_NAME = grade_config['BUCKET']
    filename = '/reports/{}LearningPlatformReportFor{}.csv'.format(filename_prefix, datetime.today().strftime('%B'))
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.lookup(BUCKET_NAME)
    
    key = Key(bucket)
    key.key = filename
    key.set_contents_from_string(content)

    url = key.generate_url(expires_in=0)
    conn.close()
    
    log.info('{} successfully uploaded to S3 bucket: {}'.format(filename, BUCKET_NAME))
    return url
