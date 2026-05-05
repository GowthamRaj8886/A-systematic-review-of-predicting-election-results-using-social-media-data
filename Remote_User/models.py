from django.db import models

# Create your models here.
from django.db.models import CASCADE


class ClientRegister_Model(models.Model):
    username = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=10)
    phoneno = models.CharField(max_length=10)
    country = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    city = models.CharField(max_length=30)

class Election_model(models.Model):

    tweeter=models.CharField(max_length=300)
    total_tweet_Time=models.CharField(max_length=300)
    tweet=models.CharField(max_length=3000)

class Election_prediction_model(models.Model):

    tweeter=models.CharField(max_length=300)
    total_tweet_Time=models.CharField(max_length=300)
    tweet=models.CharField(max_length=3000)
    prediction=models.CharField(max_length=300)

class detection_ratio_model(models.Model):

    names=models.CharField(max_length=300)
    ratio=models.CharField(max_length=300)






