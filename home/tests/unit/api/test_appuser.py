from django.test import TestCase

from home.models import Account
from home.views.api.appuser import is_tester, validate_account_input


class TestIsTester(TestCase):
    def test_is_tester(self):
        examples = [
            ("Tester A", True),
            ("Test B", False), # are we sure this is the behavior we want?
            ("tester c", True),
            ("Testerosa", False),
            ("tester-d", True),
            ("Tester_E", True),
            ("testrata", False),
            ("tester", False), # are we sure this is the behavior we want?
        ]
        for example, expected in examples:
            self.assertEqual(expected, is_tester(example), f"failed '{example}'")

class TestValidateAccountInput(TestCase):
    def test_valid_input(self):
        examples = [
            dict(zip="12345", age=99, is_latino=True, race=["BL"], gender="TF"),
            dict(is_latino=None, gender=None, race=None),
            dict(gender="OT", gender_other="other gender"),
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
            dict(is_latino="yes"),
            dict(gender="", gender_other="other gender"),
            dict(race=None, race_other="other race"),
            dict(gender="NB", gender_other="nonbinary"),
        ]

        for example in examples:
            with self.assertRaises(AssertionError, msg=example):
                validate_account_input(example)
