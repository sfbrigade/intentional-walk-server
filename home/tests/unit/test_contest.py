from django.core.exceptions import ValidationError
from django.test import TestCase

from home.models import Contest


class TestContest(TestCase):


    # Test a successful creation of a Contest
    def test_create(self):
        contest = Contest()
        contest.start = '2020-07-01'
        contest.end = '2020-07-31'
        contest.save()
        self.assertIsNotNone(contest.pk)


    # Test validation of start/end dates
    def test_validates_dates(self):
        contest = Contest()

        # Start same as end is error
        contest.start = '2020-07-01'
        contest.end = '2020-07-01'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'End of contest must be after Start')

        # Start after end is error
        contest.start = '2020-07-31'
        contest.end = '2020-07-01'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'End of contest must be after Start')

        # Save a valid contest
        contest.start = '2020-07-01'
        contest.end = '2020-07-31'
        contest.save()
        self.assertIsNotNone(contest.pk)

        # Editing an existing contest does not raise an error
        contest.end = '2020-07-21'
        contest.save();

        contest = Contest()

        # New overlapping contests cause errors
        contest.start = '2020-06-01'
        contest.end = '2020-07-14'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'Contest must not overlap another')

        contest.start = '2020-06-01'
        contest.end = '2020-08-14'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'Contest must not overlap another')

        contest.start = '2020-07-01'
        contest.end = '2020-07-21'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'Contest must not overlap another')

        contest.start = '2020-07-07'
        contest.end = '2020-07-14'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'Contest must not overlap another')

        contest.start = '2020-07-14'
        contest.end = '2020-08-21'
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, 'Contest must not overlap another')
