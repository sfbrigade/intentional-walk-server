import json
from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _

SAN_FRANCISCO_ZIP_CODES = set(
    [
        "94102",
        "94103",
        "94104",
        "94105",
        "94107",
        "94108",
        "94109",
        "94110",
        "94111",
        "94112",
        "94114",
        "94115",
        "94116",
        "94117",
        "94118",
        "94121",
        "94122",
        "94123",
        "94124",
        "94127",
        "94129",
        "94130",
        "94131",
        "94132",
        "94133",
        "94134",
        "94158",
    ]
)


class GenderLabels(models.TextChoices):
    CF = "CF", _("Female")
    CM = "CM", _("Male")
    TF = "TF", _("Trans Female")
    TM = "TM", _("Trans Male")
    NB = "NB", _("Non-binary")
    OT = "OT", _("Other")
    DA = "DA", _("Decline to answer")


class RaceLabels(models.TextChoices):
    NA = "NA", _("American Indian or Alaska Native")
    BL = "BL", _("Black")
    AS = "AS", _("Asian")
    PI = "PI", _("Native Hawaiian or other Pacific Islander")
    WH = "WH", _("White")
    OT = "OT", _("Other")
    DA = "DA", _("Decline to answer")


class SexualOrientationLabels(models.TextChoices):
    BS = "BS", _("Bisexual")
    SG = "SG", _("SameGenderLoving")
    US = "US", _("Unsure")
    HS = "HS", _("Heterosexual")
    OT = "OT", _("Other")
    DA = "DA", _("Decline to answer")


class IsLatinoLabels(models.TextChoices):
    YE = "YE", _("Yes")
    NO = "NO", _("No")
    DA = "DA", _("Decline to answer")


# Note: Maybe inherit from Django's User model?
class Account(models.Model):
    """
    Stores a single user account as identified by email. This is created when
    the app is installed and the user signs up for the first time and is has
    multiple devices - :model: `home.Device` associated with it
    """

    email = models.EmailField(
        unique=True, help_text="Email which uniquely identifies an account"
    )
    name = models.CharField(max_length=250, help_text="User's name")
    zip = models.CharField(max_length=25, help_text="User's zip code")
    age = models.IntegerField(help_text="User's age")
    is_sf_resident = models.BooleanField(
        null=True,
        help_text="Whether the user is a SF resident or not, based on zip",
    )
    is_latino = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=IsLatinoLabels.__members__.items(),
        help_text="Latino or Hispanic origin",
    )
    race = models.JSONField(
        null=True,
        blank=True,
        choices=list(RaceLabels.__members__.items()),
    )
    race_other = models.CharField(
        max_length=75,
        null=True,
        blank=True,
        help_text="Free-form text field for 'race' value 'OT'",
    )
    gender = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=GenderLabels.__members__.items(),
        help_text="Self-identified gender identity of user",
    )
    gender_other = models.CharField(
        max_length=75,
        null=True,
        blank=True,
        help_text="Free-form text field for 'gender' value 'OT'",
    )
    sexual_orien = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=SexualOrientationLabels.__members__.items(),
        help_text="Self-identified sexual orientation of user",
    )
    sexual_orien_other = models.CharField(
        max_length=75,
        null=True,
        blank=True,
        help_text="Free-form text field for 'sexual_orien' value 'OT'",
    )
    is_tester = models.BooleanField(
        default=False, help_text="User is an app tester"
    )
    contests = models.ManyToManyField(
        "Contest",
        blank=True,
        help_text="All the contests the account has enrolled in",
    )
    created = models.DateTimeField(
        auto_now_add=True, help_text="Accounts creation timestamp"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="Accounts updation timestamp"
    )

    def __str__(self):
        return f"{self.name} | {self.email}"

    class Meta:
        ordering = ("-created",)
