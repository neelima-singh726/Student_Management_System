from base64 import urlsafe_b64decode, urlsafe_b64encode
import json
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render, HttpResponse
from django.shortcuts import redirect
from datetime import datetime
from home.models import student_detail
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, get_user_model, authenticate
import smtplib
from email.mime.text import MIMEText
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from twilio.base.exceptions import TwilioRestException
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from student.settings import EMAIL, PSWD, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TWILIO_SID

from django.contrib.messages import get_messages

#*************Not required this is automaticallly done by django*******************
# def clear_messages(request):
#     storage = get_messages(request)
#     storage.used = True

def index(request):
    return render(request,'index.html')

@login_required
def about(request):
    dob_formatted = request.user.student_detail.dob.strftime('%Y-%m-%d')
    context = {
        'student':  request.user.student_detail,
        'dob_formatted': dob_formatted
    }
    return render(request, 'about.html', context)
   

def update_student_details(request):
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        print(dob)
        student = student_detail.objects.get(email=email)
        student.first_name = first_name
        student.last_name = last_name
        student.phone = phone
        student.dob = dob
        student.save()
        print(student.dob)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        print(request.POST.get('dob'))
        print(dob)
        # Check if the email is already used as a username
        if student_detail.objects.filter(username=email).exists():
            messages.success(request, 'Email already in use. Please choose a different email.')
            return render(request, 'index.html')
            # print("Before clearing messages:", request.COOKIES.get('messages'))
            # clear_messages(request)
            # print("After clearing messages:", request.COOKIES.get('messages'))
        
        else:
            user = student_detail.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                dob=dob
            )
            if user:
                messages.success(request, 'Student Details Added Successfully')
                return redirect('register')
    return render(request, 'register.html')


def loginuser(request):
    if request.method=='POST':
        username=request.POST['username']
        password =request.POST['password']
        # print(username,password)
        user = authenticate(username=username,password = password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('send_broadcast')  
            else:
                return redirect('about')
        else:
             messages.success(request, 'Invalid User')
             return redirect('/')
        
        
def forgot_password(request):
    return render(request, 'forgot_password.html')


#############################################################




from django.http import JsonResponse
import smtplib

import json
import smtplib
from django.http import JsonResponse



def send_emails(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")




def send_email(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_b64encode(force_bytes(user.pk))
                reset_link = f"http://127.0.0.1:8000/reset/{uidb64.decode()}/{token}/"      
                subject = "Reset Password"
                body = f"Click the following link to reset your password: {reset_link}"
                sender = EMAIL
                recipients = [email]
                password = PSWD
                
                send_emails(subject, body, sender, recipients, password)
                
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


def reset_password(request, uidb64, token):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_password = data.get('new_password')
        
        try:
            uid = urlsafe_b64decode(uidb64).decode('utf-8')
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid token'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})


@login_required
def broadcast_email(request):
    if request.user.is_superuser:
        user_emails = student_detail.objects.values_list('email', flat=True)
        print(user_emails)
        if request.method == 'POST':
            data = json.loads(request.body)
            subject = data.get('subject')
            body = data.get('body')
            if body:
                try:
                    recipients = list(user_emails)
                    print(recipients)               
                    send_emails(subject, body, EMAIL, recipients, PSWD)
                    return JsonResponse({'success': True})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

@login_required
def send_broadcast(request):
    return render(request, 'email.html')


#######################phone no verification ############################

from django.http import JsonResponse
from twilio.rest import Client
import random
from django.core.cache import cache


def send_verification_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse the JSON data from the request body
        phone_number = data.get('phone')
        client = Client(TWILIO_SID,TWILIO_AUTH_TOKEN)
        verification_code = str(random.randint(1000, 9999))  # Generate a random 4-digit code
        print(phone_number)
        # Store the OTP in cache temporarily
        cache_key = f"otp_{phone_number}"
        cache.set(cache_key, verification_code, timeout=300)  # Set a timeout (in seconds)
        
        try:
            message = client.messages.create(
            body=f"Your verification code: {verification_code}",
            from_= TWILIO_PHONE_NUMBER,
            to=  phone_number
         )
        except TwilioRestException as e:
            print("Twilio Error Code:", e.code)
            print("Twilio Error Message:", e.msg)
            print("Twilio Error Details:", e.details)
            # print("Twilio Error More Info:", e.more_info)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse the JSON data from the request body
        phone_number = data.get('phone')
        entered_otp = data.get('otp')
        
        # Retrieve the stored OTP from cache
        stored_otp = cache.get(f"otp_{phone_number}")
        if stored_otp is None:
            return JsonResponse({'success': False, 'message': 'OTP not found or expired'})

        # Compare entered OTP with stored OTP
        if entered_otp == stored_otp:
            # Verification successful, remove stored OTP from cache
            cache.delete(f"otp_{phone_number}")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid OTP'})

    return JsonResponse({'success': False})



