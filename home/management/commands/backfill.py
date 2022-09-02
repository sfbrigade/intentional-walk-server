import csv

from django.core.management.base import BaseCommand
from django.db import connection

from home.models import Contest, DailyWalk


class Command(BaseCommand):
    """
    Example:
        python manage.py backfill account_contests --dry_run
    """

    help = "Backfill data"
    choices = {
        "account_contests": "Use dailywalks to backfill account_contests relationship (many-to-many)",
    }

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers()

        # Backfill table home_account_contests (contests by account)
        subparser_account_contests = subparsers.add_parser(
            "account_contests",
            help="Use dailywalks to backfill account_contests relationship (many-to-many)",
        )
        subparser_account_contests.add_argument(
            "--dry_run", "-N", action="store_true", help="Dry run (no-op)"
        )
        subparser_account_contests.set_defaults(
            func=self._backfill_account_contests
        )

        subparser_account_contests_opts = (
            subparser_account_contests.add_mutually_exclusive_group(
                required=True
            )
        )
        subparser_account_contests_opts.add_argument(
            "--all", action="store_true", help="Populate all contests"
        )
        subparser_account_contests_opts.add_argument(
            "--contest_date",
            help="Select contest to populate by any date during the contest (or multiple if separated by commas)",
        )
        subparser_account_contests_opts.add_argument(
            "--contest_id",
            help="Select contest to populate by contest_id. (Separate multiple by commas.)",
        )

    def handle(self, *args, **options):
        options["func"](**options)

    def _backfill_account_contests(self, dry_run=False, **options):
        walks_processed = 0
        contest_walks = 0
        entry_set = set()

        # Choose contest
        # TODO: allow start and end dates for filtering
        if options["contest_id"]:
            contests = set(
                [
                    Contest.objects.get(pk=_cid)
                    for _cid in options["contest_id"].split(",")
                ]
            )
        elif options["contest_date"]:
            contests = set(
                [
                    Contest.active(for_date=_date, strict=True)
                    for _date in options["contest_date"].split(",")
                ]
            )
        elif options["all"]:
            contests = Contest.objects.all()
        else:
            sys.exit(1)

        # Retrieve ALL daily walks and try to fit them into contests
        daily_walks = DailyWalk.objects.all().order_by("date")
        for walk in daily_walks:
            acct = walk.account
            walks_processed += 1

            # Retrieve the active contest for this walk
            active_contest = Contest.active(for_date=walk.date, strict=True)

            # Only process if the active contest was selected
            if active_contest in contests:
                contest_walks += 1

                if not acct.contests.filter(pk=active_contest.pk):
                    # Keep track of rows that were (or would have been) added
                    entry_set.add((acct, active_contest))
                    if not dry_run:
                        walk.account.contests.add(active_contest)

            if walks_processed % 1000 == 0:
                print(f"Processed {walks_processed} walks...")

        if_dry_run = " (DRY RUN)" if dry_run else ""
        print(f"Contest walks processed: {contest_walks}")
        print(f"Rows added: {len(entry_set)}{if_dry_run}")
