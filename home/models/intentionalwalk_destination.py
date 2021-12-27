from django.db import models

from home.models.intentionalwalk import IntentionalWalk
from home.models.destination import Destination

# blog/models.py
class IntentionalWalkDestination(models.Model):
    intentional_walk = models.ForeignKey(IntentionalWalk, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    closest = models.FloatField(blank=True, help_text="Closest distance from destination (m)")
    farthest = models.FloatField(blank=True, help_text="Farthest distance from destination (m)")

    class Meta:
        unique_together = ('contributor', 'blog')
