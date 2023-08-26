from datetime import date

from django.test import TestCase

from home.utils.dates import get_start_of_week


class TestDates(TestCase):

    # Test get_start_of_week
    def test_get_start_of_week(self):
        dt = date(2023, 8, 23)
        monday = date(2023, 8, 21)
        start_of_week = get_start_of_week(dt)
        self.assertEqual(monday, start_of_week)
