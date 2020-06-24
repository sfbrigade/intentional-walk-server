import time
from django.db import models


class IntentionalWalk(models.Model):
    """
    Stores a single intentional/recorded walk from a user/account. It is always
    linked to the specific device identifier :model: `home.Device`
    """

    start = models.DateTimeField(help_text="Timestamp when the intentional walk started")
    end = models.DateTimeField(help_text="Timestamp when the intentional walk ended")
    steps = models.IntegerField(help_text="Number of steps recorded")
    pause_time = models.FloatField(help_text="Total time paused (in seconds)")
    distance = models.FloatField(help_text="Total distance covered")
    device = models.ForeignKey("Device", on_delete=models.CASCADE, help_text="Device the data is coming from")
    account = models.ForeignKey("Account", on_delete=models.CASCADE, help_text="Account the data is linked to")
    created = models.DateTimeField(auto_now_add=True, help_text="Record creation timestamp")

    @property
    def walk_time(self):
        return (self.end - self.start).total_seconds() - self.pause_time

    @property
    def walk_time_repr(self):
        return time.strftime(
            "%Hh %Mm %Ss", time.gmtime(int((self.end - self.start).total_seconds() - self.pause_time)),
        )

    @property
    def pause_time_repr(self):
        return time.strftime("%Hh %Mm %Ss", time.gmtime(int(self.pause_time)))

    @property
    def speed(self):
        return (self.distance / ((self.end - self.start).total_seconds() - self.pause_time)) * 3600

    # Auto populate the account field from the device field
    def save(self, *args, **kwargs):
        self.account = self.device.account
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account.email}  | {self.start} - {self.end}"

    class Meta:
        ordering = ("-start",)
