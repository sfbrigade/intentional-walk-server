import logging

from django.db import models
from home.models.leaderboard import Leaderboard
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum


from home.templatetags.format_helpers import m_to_mi

logger = logging.getLogger(__name__)


# Event model
class DailyWalk(models.Model):
    """
    Stores a single daily walk. This is unique for any given date and registered
    account. It is always linked to the specific device identifier
    :model: `home.Device`
    """

    date = models.DateField(
        help_text="The specific date for which the steps are recorded"
    )
    steps = models.IntegerField(help_text="Number of steps recorded")
    distance = models.FloatField(help_text="Total distance covered")
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE,
        help_text="Device the data is coming from",
    )
    account = models.ForeignKey(
        "Account",
        on_delete=models.CASCADE,
        help_text="Account the data is linked to",
    )
    created = models.DateTimeField(
        auto_now_add=True, help_text="Record creation timestamp"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="Record updation timestamp"
    )

    @property
    def distance_in_miles(self):
        return m_to_mi(self.distance)

    # Auto populate the account field from the device field
    def save(self, *args, **kwargs):
        self.account = self.device.account
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account.email} | {self.date}"

    def update_leaderboard(**kwargs):
        device = kwargs.get("device")
        contest = kwargs.get("contest")
        total_steps = (
            DailyWalk.objects.filter(account=device.account)
            .filter(date__range=(contest.start, contest.end))
            .aggregate(Sum("steps"))
        )
        if total_steps["steps__sum"] is None:
            total_steps["steps__sum"] = 0
        try:
            # Update
            leaderboard = Leaderboard.objects.get(
                account=device.account, contest=contest
            )
            leaderboard.steps = total_steps["steps__sum"]
            leaderboard.device = device
            leaderboard.save()
        except ObjectDoesNotExist:
            leaderboard = Leaderboard.objects.create(
                steps=total_steps["steps__sum"],
                device=device,
                contest=contest,
            )

    class Meta:
        ordering = ("-date",)
        constraints = [
            models.UniqueConstraint(
                fields=["account", "date"], name="account_date"
            ),
        ]
