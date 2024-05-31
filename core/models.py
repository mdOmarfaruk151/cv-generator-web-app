# core/models.py
from django.db import models
from django.contrib.auth.models import User

class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    experience = models.TextField()
    education = models.TextField()
    projects = models.TextField()
    skills = models.TextField()
    awards = models.TextField()
    languages = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class user_update(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.user.username)