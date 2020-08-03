from django.db import models
from home.templatetags.format_helpers import m_to_mi


# Event model
class DailyWalk(models.Model):
    """
    Stores a single daily walk. This is unique for any given date and registered
    account. It is always linked to the specific device identifier :model: `home.Device`
    """

    date = models.DateField(help_text="The specific for which the steps are recorded for")
    steps = models.IntegerField(help_text="Number of steps recorded")
    distance = models.FloatField(help_text="Total distance covered")
    device = models.ForeignKey("Device", on_delete=models.CASCADE, help_text="Device the data is coming from")
    account = models.ForeignKey("Account", on_delete=models.CASCADE, help_text="Account the data is linked to")
    created = models.DateTimeField(auto_now_add=True, help_text="Record creation timestamp")
    updated = models.DateTimeField(auto_now=True, help_text="Record updation timestamp")

    @property
    def distance_in_miles(self):
        return m_to_mi(self.distance)

    # Auto populate the account field from the device field
    def save(self, *args, **kwargs):
        self.account = self.device.account
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account.email} | {self.date}"

    class Meta:
        ordering = ("-date",)
        constraints = [
            models.UniqueConstraint(fields=["account", "date"], name="account_date"),
        ]
