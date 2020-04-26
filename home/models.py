import time
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


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
        return f"{self.name} | {self.email} | {self.account_id}"

    class Meta:
        ordering = ("-created",)


# Contest model
class Contest(models.Model):
    contest_id = models.CharField(default=uuid.uuid4, max_length=250, primary_key=True)
    start = models.DateField()
    end = models.DateField()

    def __str__(self):
        return f"{self.start} | {self.end}"

    class Meta:
        ordering = ("-start",)

    def save(self, *args, **kwargs):
        # ensure end is greater than start
        if self.end <= self.start:
            raise ValidationError('End of contest must be after Start')
        # ensure that this does not overlap an existing contest period
        query = Contest.objects.filter(
            Q(start__lte=self.start, end__gt=self.start) |
            Q(start__lt=self.end, end__gte=self.end) |
            Q(start__gte=self.start, end__lte=self.end))
        if self.pk:
            query = query.exclude(pk=self.pk)
        if query.exists():
            raise ValidationError('Contest must not overlap another')
        super().save(*args, **kwargs)


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
