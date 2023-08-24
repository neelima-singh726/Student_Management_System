from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path("", views.index, name='home'),
    path("register", views.register, name='register'),
    path("login", views.loginuser, name='login'),
    path("about", views.about, name = 'about'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-email/', views.send_email, name='send_email'),
    path('update-student-details/', views.update_student_details, name='update_student_details'),
    path('broadcast', views.broadcast_email, name='broadcast'),
    path('send_broadcast', views.send_broadcast, name='send_broadcast'),
    path("reset/<uidb64>/<token>/", views.reset_password, name = 'reset'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('send-otp/', views.send_verification_code, name='send-otp'),


]