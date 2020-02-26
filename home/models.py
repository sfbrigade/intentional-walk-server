from django.db import models


# User model
class AppUser(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    zip = models.CharField(max_length=25)
    age = models.IntegerField()
    # Device/Account identifier - Unique token to be sent while making API calls
    device_id = models.CharField(max_length=250)
    # Meta information
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} | {self.email}"

    class Meta:
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(fields=['email', 'device_id'], name='Unique user + device')
        ]

# Event model
class DailyWalk(models.Model):
    date = models.DateField()
    steps = models.IntegerField()
    user = models.manufacturer = models.ForeignKey('AppUser',
                                                   on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} | {self.date}"

    class Meta:
        ordering = ('-date',)

# Event model
class IntentionalWalk(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    steps = models.IntegerField()
    user = models.manufacturer = models.ForeignKey('AppUser',
                                                   on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} | {self.start} - {self.end}"

    class Meta:
        ordering = ('-start',)