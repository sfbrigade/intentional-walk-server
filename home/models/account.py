from django.db import models


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
    contests = models.ManyToManyField("Contest", blank=True, help_text="All the contests the account has enrolled in")
    created = models.DateTimeField(auto_now_add=True, help_text="Accounts creation timestamp")
    updated = models.DateTimeField(auto_now=True, help_text="Accounts updation timestamp")

    def __str__(self):
        return f"{self.name} | {self.email}"

    class Meta:
        ordering = ("-created",)
