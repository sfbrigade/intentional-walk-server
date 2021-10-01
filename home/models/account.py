from django.db import models

SAN_FRANCISCO_ZIP_CODES = set([
    '94102', '94103', '94104', '94105', '94107', '94108', '94109', '94110',
    '94111', '94112', '94114', '94115', '94116', '94117', '94118', '94121',
    '94122', '94123', '94124', '94127', '94129', '94130', '94131', '94132',
    '94133', '94134', '94158',
])

# Note: Maybe inherit from Django's User model?
class Account(models.Model):
    """
    Stores a single user account as identified by email. This is created when the
    app is installed and the user signs up for the first time and is has multiple
    devices - :model: `home.Device` associated with it
    """

    email = models.EmailField(unique=True, help_text="Email which uniquely identifies an account")
    name = models.CharField(max_length=250, help_text="User's name")
    zip = models.CharField(max_length=25, help_text="User's zipcode")
    age = models.IntegerField(help_text="User's age")
    is_sf_resident = models.BooleanField(null=True, help_text="Whether the user is a SF resident or not, based on zip")
    is_latino = models.BooleanField(null=True, blank=True, help_text="Latino or Hispanic origin")
    race = models.ManyToManyField("Race", blank=True, help_text="Self-identified race(s) of user")
    gender = models.CharField(max_length=25, blank=True, help_text="Self-identified gender identity of user")

    is_tester = models.BooleanField(default=False, help_text="User is an app tester")
    contests = models.ManyToManyField("Contest", blank=True, help_text="All the contests the account has enrolled in")
    created = models.DateTimeField(auto_now_add=True, help_text="Accounts creation timestamp")
    updated = models.DateTimeField(auto_now=True, help_text="Accounts updation timestamp")

    def __str__(self):
        return f"{self.name} | {self.email}"

    class Meta:
        ordering = ("-created",)
