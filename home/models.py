import time
from django.db import models


# User model
class AppUser(models.Model):
    # Device/Account identifier - Unique token to be sent while making API calls
    # Also the primary key
    account_id = models.CharField(max_length=250, primary_key=True)
    # User information
    name = models.CharField(max_length=250)
    email = models.EmailField()
    zip = models.CharField(max_length=25)
    age = models.IntegerField()
    # Meta information
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} | {self.email} | {self.account_id} "

    class Meta:
        ordering = ("-created",)


# Event model
class DailyWalk(models.Model):
    # Walk meta
    date = models.DateField()
    steps = models.IntegerField()
    distance = models.FloatField()
    appuser = models.manufacturer = models.ForeignKey("AppUser", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.appuser} | {self.date}"

    class Meta:
        ordering = ("-date",)
        constraints = [
            models.UniqueConstraint(fields= ['appuser', 'date'], name='appuser_date'),
        ]


# Event model
class IntentionalWalk(models.Model):
    # event id will be a v4 random uuid generated on the client
    event_id = models.CharField(max_length=250, unique=True)
    # Walk meta
    start = models.DateTimeField()
    end = models.DateTimeField()
    steps = models.IntegerField()
    pause_time = models.FloatField()
    distance = models.FloatField()
    appuser = models.manufacturer = models.ForeignKey("AppUser", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    @property
    def walk_time(self):
        return (self.end - self.start).total_seconds() - self.pause_time

    @property
    def walk_time_repr(self):
        return time.strftime("%Hh %Mm %Ss", time.gmtime(int((self.end - self.start).total_seconds() - self.pause_time)))

    @property
    def pause_time_repr(self):
        return time.strftime("%Hh %Mm %Ss", time.gmtime(int(self.pause_time)))

    @property
    def speed(self):
        return (self.distance/((self.end - self.start).total_seconds() - self.pause_time))*3600

    def __str__(self):
        return f"{self.appuser} | {self.start} - {self.end}"

    class Meta:
        ordering = ("-start",)
