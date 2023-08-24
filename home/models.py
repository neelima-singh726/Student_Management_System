from django.db import models
import os
from twilio.rest import Client
from django.contrib.auth.models import User

# Create your models here.
class student_detail(User):
    student_id = models.AutoField(primary_key=True)
    # first_name = models.CharField(max_length=200)
    # last_name = models.CharField(max_length=200)
    # email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=200)
    # password = models.CharField(max_length=200)
    dob = models.DateField()


    def __str__(self):
        return self.email
    
  