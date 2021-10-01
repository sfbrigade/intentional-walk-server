from django.db import models


class Race(models.Model):
    """
    Simple table of racial identity options
    """

    label = models.CharField(unique=True, max_length=75)

    def __str__(self):
        return self.label
