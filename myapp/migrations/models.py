from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    profile_pic = models.ImageField(upload_to='uploads/profile_pics', blank=True, null=True)


class RelationsTo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_liked = models.BooleanField()


class RelationsWith(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    users = models.ManyToManyField(RelationsTo)


class Message(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField()
    text = models.CharField(max_length=244)


class Couples(models.Model):
    users = models.ManyToManyField(User)
    messages = models.ManyToManyField(Message)

