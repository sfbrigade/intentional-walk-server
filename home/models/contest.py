import datetime
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Contest(models.Model):
    """
    Each entry defines a contest with a start and end date. Many to many links
    with :model: `home.Account`
    """

    contest_id = models.CharField(default=uuid.uuid4, max_length=250, primary_key=True, help_text="Contest identifier",)
    start_promo = models.DateField(help_text="Start date of promotion")
    start = models.DateField(help_text="Contest start date")
    end = models.DateField(help_text="Contest end date")
    created = models.DateTimeField(auto_now_add=True, help_text="Contest creation timestamp")
    updated = models.DateTimeField(auto_now=True, help_text="Contest updation timestamp")

    def __str__(self):
        return f"{self.start} | {self.end}"

    class Meta:
        ordering = ("-start",)

    @staticmethod
    def active(for_date=None, strict=False):
        today = datetime.date.today() if for_date is None else for_date
        contest = Contest.objects.filter(start_promo__lte=today, end__gte=today).order_by("start_promo").first()
        if contest is None and not strict:
            # get the last contest
            contest = Contest.objects.filter(end__lt=today).order_by("-end").first()
        return contest

    def save(self, *args, **kwargs):
        # ensure promotion begins before or at same time as contest start
        if self.start < self.start_promo:
            raise ValidationError("Promotion must start before or at same time as Start")
        # ensure end is greater than start
        if self.end <= self.start:
            raise ValidationError("End of contest must be after Start")
        # ensure that this does not overlap an existing contest period
        query = Contest.objects.filter(
            Q(start_promo__lte=self.start, end__gt=self.start)
            | Q(start_promo__lt=self.end, end__gte=self.end)
            | Q(start_promo__gte=self.start, end__lte=self.end)
        )
        if self.pk:
            query = query.exclude(pk=self.pk)
        if query.exists():
            raise ValidationError("Contest must not overlap another")
        super().save(*args, **kwargs)
