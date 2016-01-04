import logging

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt                                          
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_by_id
from instructor.enrollment import (
    enroll_email,
    get_email_params,
)
from instructor.utils import DummyRequest

#hijack account creation at time of POST
from student.views import create_account_with_params
from student.forms import AccountCreationForm

#for password/username creation
import random
import string

logger = logging.getLogger(__name__)

@csrf_exempt 
def endpoint(request):
    if request.method != 'POST':
        logger.warning('Non-POST request coming to url: /infusionsoft')
        raise Http404

    post_secret = request.POST.get('SecretKey','')
    server_secret = settings.APPSEMBLER_FEATURES.get('INFUSIONSOFT_SECRET_KEY','')
    if post_secret != server_secret:
        msg = "POST request from Infusionsoft failed with secret key: {}".format(post_secret)
        logger.error(msg)
        return HttpResponse(status=403)

    course_id_str = request.POST.get('CourseId','')
    if not course_id_str:
        logger.error('Could not extract CourseId from POST request')
        return HttpResponse(status=400)

    user_email = request.POST.get('Email','')
    if not user_email:
        logger.error('Could not extract Email from POST request')
        return HttpResponse(status=400)

    #auto create student if none exists
    is_account_new = False
    try:
        validate_email(user_email)
        user = User.objects.get(email=user_email)
    except ValidationError:
        logger.error('User email did not validate correctly: {}'.format(email))
        return HttpResponse(status=400)
    except User.DoesNotExist:
        try:
            #from common/djangoapps/student/view.py:create_account
            full_name = request.POST.get('FirstName') + ' ' + request.POST.get('LastName')
            password = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))

            #filter out any spaces and punctuation
            username = ''.join(ch for ch in full_name if ch.isalnum())
            #make sure username is unique
            while User.objects.filter(username=username):
                username = username + str(random.randint(1,9))

            # post_vars = {
            #     'username': username,
            #     'email': user_email,
            #     'password': password,
            #     'name': full_name,
            #     'level_of_education': '',
            #     'gender': '',
            #     'mailing_address': '',
            #     'city': '',
            #     'country': '',
            #     'goals': ''
            # }

            # form = AccountCreationForm(
            #     data=params,
            #     extra_fields=extra_fields,
            #     extended_profile_fields=extended_profile_fields,
            #     enforce_username_neq_password=True,
            #     enforce_password_policy=enforce_password_policy,
            #     tos_required=tos_required,
            # )

            # (user, profile, registration) = _do_create_account(form)
            
            post_vars = {
                'username': username,
                'name': full_name,
                'terms_of_service': 'true',
                'csrfmiddlewaretoken': 'fake',
                'password': password,
                'email': user_email,
            }
            request = DummyRequest()

            create_account_with_params(request, post_vars)
            
            is_account_new = True
        except: 
            logger.error('User {} not correctly created through /infusionsoft'.format(user_email))
    
            subject = 'Error during account creation process on courses.bodymindinstitute.com'
            message = '''
                Account creation failed for the user with email: {}
            '''.format(user_email)
            send_mail(subject, message, 'support@appsembler.com', ['academy@metalogix.com','support@appsembler.com'], fail_silently=False)
    
            return HttpResponse(status=400)

    ##based on students_update_enrollment() in  djangoapps/instructor/views/api.py
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_str)
    action = 'enroll'
    auto_enroll = True
    #send default email only if account wasn't just created
    email_students = not is_account_new

    email_params = {} 
    if email_students:
        course = get_course_by_id(course_id)
        email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

    # First try to get a user object based on email address
    user = None 
    email = None 
    # language = None 
    try: 
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        email = user_email
    else:
        email = user.email
        # language = get_user_email_language(user)

    try: 
        # Use django.core.validators.validate_email to check email address
        # validity (obviously, cannot check if email actually /exists/,
        # simply that it is plausibly valid)
        validate_email(email)  # Raises ValidationError if invalid

        if action == 'enroll':
            before, after = enroll_email(
                course_id, email, auto_enroll, email_students, email_params 
            )

        if is_account_new:
            course = get_course_by_id(course_id)
            subject = 'Welcome to the BodyMind Institute'
            message = '''
Hello {first_name},

We are delighted to have you on board with us as a student here at the BodyMind Institute.

You have been registered in the following course: 

{course_name}

Here is your login information:

 Login: http://courses.bodymindinstitute.com
 Email: {email}
 Password: {password}

If you need any assistance, we would love to hear from you at info@bodymindinstitute.com or by phone toll free at 1-888-787-8886 M-F 9-5pm MST.

Again, welcome!

Your BodyMind Team
 www.bodymindinstitute.com
 info@bodymindinstitute.com
 North America: 1-888-787-8886 M-F 9-5pm MST

Join us in the conversation on Facebook where we regularly host free events, special offers and valuable resources all to enhance your learning with BodyMind Institute.
www.facebook.com/bodymindinstitute
            '''.format(
                    first_name=request.POST.get('FirstName'), 
                    course_name=course.display_name,
                    email=user_email, 
                    password=password
                )
            send_mail(subject, message, 'info@bodymindinstitute.com', [user_email], fail_silently=False)

    except ValidationError:
        # Flag this email as an error if invalid, but continue checking
        # the remaining in the list
        logger.error('User email did not validate correctly: {}'.format(email))
        return HttpResponse(status=400)

    except Exception as exc:  # pylint: disable=broad-except
        # catch and log any exceptions
        # so that one error doesn't cause a 500.
        logger.exception("Error while #{}ing student")
        logger.exception(exc)
        return HttpResponse(status=400)
        

    return HttpResponse(status=200)

