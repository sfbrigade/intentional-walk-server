from django.db import models


class Destination(models.Model):
    """
    Points of Interest ("destinations")
    """

    name = models.CharField(max_length=40, unique=True, help_text="Destination name")
    place_id = models.CharField(max_length=256, blank=True, help_text="Place ID (Google Maps Platform)")
    category = models.CharField(max_length=20, help_text="Destination category/type")
    latitude = models.FloatField(max_length=40, unique=True, help_text="Geolocation latitude")
    longitude = models.FloatField(max_length=40, unique=True, help_text="Geolocation longitude")
    address = models.CharField(max_length=100, help_text="Street address")
    zip = models.CharField(max_length=10, help_text="Zip code")

    created = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")
    updated = models.DateTimeField(auto_now=True, help_text="Update timestamp")

    def __str__(self):
        return f"<Destination: {self.name}>"
