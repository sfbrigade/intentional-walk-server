from django.test import TestCase

from home.views.api.appuser import validate_account_input


class TestValidateAccountInput(TestCase):
    def test_valid_input(self):
        examples = [
            dict(
                zip="12345",
                age=99,
                is_latino="YE",
                race=["BL"],
                gender="TF",
                sexual_orien="SG",
            ),
            dict(
                zip="12345", age=99, is_latino="DA", race=["DA"], gender="DA"
            ),
            dict(is_latino=None, gender=None, race=None),
            dict(
                gender="OT",
                gender_other="other gender",
                sexual_orien="OT",
                sexual_orien_other="pansexual",
            ),
            dict(race=["BL", "OT"], race_other="other race"),
            dict(),
        ]

        for example in examples:
            validate_account_input(example)

    def test_invalid_input(self):
        examples = [
            dict(name=""),
            dict(zip="1234"),
            dict(age=0),
            dict(is_latino=True),
            dict(gender="", gender_other="other gender"),
            dict(sexual_orien="", sexual_orien_other="idk"),
            dict(race=None, race_other="other race"),
            dict(gender="NB", gender_other="nonbinary"),
        ]

        for example in examples:
            with self.assertRaises(AssertionError, msg=example):
                validate_account_input(example)
