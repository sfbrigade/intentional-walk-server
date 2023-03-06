from django.db import models


# Event model
class Leaderboard(models.Model):
    """ """

    steps = models.IntegerField(help_text="Number of steps recorded")

    account = models.ForeignKey(
        "Account",
        on_delete=models.CASCADE,
        help_text="Account the data is linked to",
    )
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE,
        help_text="Device the data is coming from",
    )
    contest = models.ForeignKey(
        "Contest",
        on_delete=models.CASCADE,
        help_text="The contest the account is enrolled in",
    )

    # Auto populate the account field from the device field
    def save(self, *args, **kwargs):
        self.account = self.device.account
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.device.device_id} | {self.steps}"
