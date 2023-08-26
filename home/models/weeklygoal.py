from django.db import models

from home.utils.dates import get_start_of_current_week


class WeeklyGoal(models.Model):
    """
    Stores a weekly goal.
    An entry is created for the first weekly goal
    set by a user and when a user updates their weekly goal
    """

    start_of_week = models.DateField(
        default=get_start_of_current_week,
        help_text="The start of the week for the goal",
    )
    steps = models.IntegerField(help_text="Step goal for the week")
    days = models.IntegerField(
        help_text="Number of days per week to reach goal"
    )
    account = models.ForeignKey(
        "Account",
        on_delete=models.CASCADE,
        help_text="Account the data is linked to",
    )

    def __str__(self):
        return f"{self.account.email} | {self.start_of_week}"

    class Meta:
        ordering = ("-start_of_week",)
