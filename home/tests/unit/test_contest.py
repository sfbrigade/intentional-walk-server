from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from home.models import Account, Contest


class TestContest(TestCase):

    # Test a successful creation of a Contest
    def test_create(self):
        contest = Contest()
        contest.start_baseline = "2020-06-01"
        contest.start_promo = "2020-07-01"
        contest.start = "2020-07-01"
        contest.end = "2020-07-31"
        contest.save()
        self.assertIsNotNone(contest.pk)

    # Test validation of start/end dates
    def test_validates_dates(self):
        contest = Contest()

        # Start before baseline => error
        contest.start_baseline = "2020-07-01"
        contest.start_promo = "2020-06-21"
        contest.start = "2020-07-01"
        contest.end = "2020-07-31"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Baseline period must begin before contest start")

        # Start before promo is error
        contest.start_baseline = "2020-06-01"
        contest.start_promo = "2020-07-07"
        contest.start = "2020-07-01"
        contest.end = "2020-07-01"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Promotion must start before or at same time as Start")

        # Start same as end is error
        contest.start_baseline = "2020-06-01"
        contest.start_promo = "2020-07-01"
        contest.start = "2020-07-01"
        contest.end = "2020-07-01"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "End of contest must be after Start")

        # Start after end is error
        contest.start_baseline = "2020-06-01"
        contest.start_promo = "2020-07-01"
        contest.start = "2020-07-31"
        contest.end = "2020-07-01"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "End of contest must be after Start")

        # Save a valid contest
        contest.start_baseline = "2020-06-01"
        contest.start_promo = "2020-06-21"
        contest.start = "2020-07-01"
        contest.end = "2020-07-31"
        contest.save()
        self.assertIsNotNone(contest.pk)

        # Editing an existing contest does not raise an error
        contest.end = "2020-07-21"
        contest.save()
        self.assertEqual("2020-07-21", contest.end)

    def test_overlapping_contests(self):
        # Save a valid contest
        existing_contest = Contest()
        existing_contest.start_baseline = None
        existing_contest.start_promo = "2020-06-21"
        existing_contest.start = "2020-07-01"
        existing_contest.end = "2020-07-31"
        existing_contest.save()
        self.assertIsNotNone(existing_contest.pk)

        # Test validation of start/end dates
        contest = Contest()

        # New overlapping contests cause errors
        contest.start_promo = "2020-06-01"
        contest.start = "2020-06-01"
        contest.end = "2020-06-28"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Contest must not overlap another")

        contest.start_promo = "2020-06-01"
        contest.start = "2020-06-01"
        contest.end = "2020-08-14"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Contest must not overlap another")

        contest.start_promo = "2020-07-01"
        contest.start = "2020-07-01"
        contest.end = "2020-07-21"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Contest must not overlap another")

        contest.start_promo = "2020-07-07"
        contest.start = "2020-07-07"
        contest.end = "2020-07-14"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Contest must not overlap another")

        contest.start_promo = "2020-07-14"
        contest.start = "2020-07-14"
        contest.end = "2020-08-21"
        with self.assertRaises(ValidationError) as error:
            contest.save()
        self.assertEqual(error.exception.message, "Contest must not overlap another")

        # It IS okay if the baseline or promo date occurs during a different (previous) contest.
        contest.start_baseline = "2020-07-01"
        contest.start_promo = "2020-07-21"
        contest.start = "2020-08-01"
        contest.end = "2020-08-31"
        contest.save()
        self.assertIsNotNone(contest.pk)

    def test_active(self):
        # create a few contests
        contest1 = Contest()
        contest1.start_baseline = "3000-04-01"
        contest1.start_promo = "3000-04-24"
        contest1.start = "3000-05-01"
        contest1.end = "3000-05-31"
        contest1.save()

        contest2 = Contest()
        contest1.start_baseline = "3000-06-01"
        contest2.start_promo = "3000-06-21"
        contest2.start = "3000-07-01"
        contest2.end = "3000-07-31"
        contest2.save()

        # Helper function
        def _assertEqual(create_obj, db_obj):
            self.assertIsNotNone(db_obj)
            self.assertEqual(str(create_obj.pk), db_obj.pk)

        # before first baseline, failure
        with freeze_time("3000-03-31"):
            self.assertIsNone(Contest.active())
            self.assertIsNone(Contest.active(strict=True))

        # after first baseline but before first promo starts, failure
        with freeze_time("3000-04-02"):
            self.assertIsNone(Contest.active())
            self.assertIsNone(Contest.active(strict=True))

        # after promo starts for first contest
        with freeze_time("3000-04-28"):
            _assertEqual(contest1, Contest.active())
            _assertEqual(contest1, Contest.active(strict=True))

        # during first contest
        with freeze_time("3000-05-15"):
            _assertEqual(contest1, Contest.active())
            _assertEqual(contest1, Contest.active(strict=True))

        # after first contest, before baseline and promo starts for next
        with freeze_time("3000-06-14"):
            _assertEqual(contest1, Contest.active())
            self.assertIsNone(Contest.active(strict=True))

        # after promo starts for next
        with freeze_time("3000-06-28"):
            _assertEqual(contest2, Contest.active())
            _assertEqual(contest2, Contest.active(strict=True))

        # after last contest
        with freeze_time("3000-08-14"):
            _assertEqual(contest2, Contest.active())
            self.assertIsNone(Contest.active(strict=True))

        # Now test the same using Contest.active with `for_date`
        # instead of faking time
        self.assertIsNone(Contest.active(for_date=date(3000,4,1)))

        _assertEqual(contest1, Contest.active(for_date=date(3000,4,28)))
        _assertEqual(contest1, Contest.active(for_date=date(3000,5,15)))
        _assertEqual(contest1, Contest.active(for_date=date(3000,6,14)))
        _assertEqual(contest2, Contest.active(for_date=date(3000,6,28)))
        _assertEqual(contest2, Contest.active(for_date=date(3000,8,14)))

        # Test with `for_date` and `strict`
        self.assertIsNone(Contest.active(for_date=date(3000,8,14), strict=True))

    def test_for_baseline(self):
        # create a few contests
        contest1 = Contest()
        contest1.start_baseline = "3000-04-01"
        contest1.start_promo = "3000-04-24"
        contest1.start = "3000-05-01"
        contest1.end = "3000-05-31"
        contest1.save()

        self.assertIsNone(Contest.for_baseline("3000-03-31"))
        self.assertEqual(str(contest1.pk), Contest.for_baseline("3000-04-01").pk)
        self.assertIsNone(Contest.for_baseline("3000-05-01"))

    def test_associate_contest_with_account(self):
        contest = Contest.objects.create(
            start_promo="3000-04-24",
            start="3000-05-01",
            end="3000-05-31",
        )
        # TODO: use generator
        acct = Account.objects.create(
            email="fake@us.email",
            age=100,
        )
        acct.contests.add(contest)
        acct.contests.add(contest)
        self.assertEqual(1, len(Contest.objects.all()))
