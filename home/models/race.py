from django.db import models

from home.models import Account
from home.models.account import RaceLabels


class Race(models.Model):
    """
    Simple table of racial identity options
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    code = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.account} | {self.code}"
