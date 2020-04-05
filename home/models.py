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
        return f"{self.name} | {self.email}"

    class Meta:
        ordering = ("-created",)


# Event model
class DailyWalk(models.Model):
    # Identifier
    event_id = models.CharField(max_length=250)
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
    event_id = models.CharField(max_length=250)
    # Walk meta
    start = models.DateTimeField()
    end = models.DateTimeField()
    steps = models.IntegerField()
    pause_time = models.FloatField()
    distance = models.FloatField()
    appuser = models.manufacturer = models.ForeignKey("AppUser", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.appuser} | {self.start} - {self.end}"

    class Meta:
        ordering = ("-start",)
