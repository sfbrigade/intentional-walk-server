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
    start_baseline = models.DateField(blank=True, null=True, help_text="Start of baseline period (prior to contest start)")
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
        # Gets the "active" contest for a given date (generally "today")
        #
        # A contest is not considered active during the baseline period.
        # Therefore, the `for_date` must fall after the promo date.
        #
        # strict: `for_date` must fall strictly within the contest dates,
        #         starting on promo date, ending on end date (inclusive)
        #
        # If strict is False, then find most recent contest (prior to for_date)
        #
        if isinstance(for_date, str):
            for_date = datetime.date.fromisoformat(for_date)
        today = datetime.date.today() if for_date is None else for_date
        contest = Contest.objects.filter(start_promo__lte=today, end__gte=today).order_by("start_promo").first()
        if contest is None and not strict:
            # get the last contest
            contest = Contest.objects.filter(end__lt=today).order_by("-end").first()
        return contest

    @staticmethod
    def for_baseline(for_date: datetime.date):
        return Contest.objects.filter(start_baseline__lte=for_date, start__gt=for_date).order_by("-start").first()

    def save(self, *args, **kwargs):
        # ensure promotion begins before or at same time as contest start
        if self.start < self.start_promo:
            raise ValidationError("Promotion must start before or at same time as Start")
        # ensure baseline begins before contest start
        if self.start_baseline and self.start_baseline >= self.start:
            raise ValidationError("Baseline period must begin before contest start")
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
