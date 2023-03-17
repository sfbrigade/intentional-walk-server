"""
Generate dummy data to be imported into a clean database.
Once generated, a user can import the resulting text into
their postgresql instance.

Import dummy data into a fresh database:

    $ python scripts/dummydata.py --accounts 500 > iw_db.sql
    $ createdb iw_db
    $ python manage.py migrate
    $ psql iw_db < iw_db.sql
    [...this will take a while]

After this, a user should generate an admin account:

    $ python manage.py createsuperuser
    [...fills out a form]

You can then continue on to running the server with the new database.

Run this script with `--help` for a list of options.
"""
import argparse
import binascii
import os
import sys
import traceback
from calendar import monthrange
from collections import OrderedDict
from datetime import date, datetime
from random import randint
from typing import Any, Dict, List, Tuple
from leaderboard import make_leaderboard

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

# All San Francisco zip codes based on:
# https://www.usmapguide.com/california/san-francisco-zip-code-map/
ZIP_CODES = [
    94102,
    94103,
    94104,
    94105,
    94107,
    94108,
    94109,
    94110,
    94111,
    94112,
    94114,
    94115,
    94116,
    94117,
    94118,
    94121,
    94122,
    94123,
    94124,
    94127,
    94129,
    94130,
    94131,
    94132,
    94133,
    94134,
    94158,
]

RACES = [
    "NA",  # American Indian or Alaska Native
    "BL",  # Black
    "AS",  # Asian
    "PI",  # Native Hawaiian or other Pacific Islander
    "WH",  # White
    "OT",  # Other
    "DA",  # Decline to answer
]

GENDERS = [
    "CF",  # "Female"
    "CM",  # "Male"
    "TF",  # "Trans Female"
    "TM",  # "Trans Male"
    "NB",  # "Non-binary"
    "OT",  # "Other"
    "DA",  # "Decline to answer"
]

ORIENTATION = [
    "BS",  # "Bisexual"
    "SG",  # "SameGenderLoving"
    "US",  # "Unsure"
    "HS",  # "Heterosexual"
    "OT",  # "Other"
    "DA",  # "Decline to answer"
]

IS_LATINO = [
    "YE",  # "Yes"
    "NO",  # "No"
    "DA",  # "Decline to answer"
]

TIMEZONE = None

TYPE_FORMATS = {
    str: "'%s'",
    int: "%d",
    float: "%.6f",
    bool: "%s",
    date: "'%s'",
    list: "%s",
}

TYPE_TRANSFORM = {
    str: lambda x: x,
    int: lambda x: x,
    float: lambda x: x,
    bool: lambda x: str(x).lower(),
    date: lambda x: str(x),
    list: lambda x: f"{{{', '.join(x)}}}",
}


def random_element(array: List[Any]):
    n = randint(0, len(array) - 1)
    return array[n]


def type_fmt(value: Any) -> Any:
    transform = TYPE_TRANSFORM.get(type(value))
    return TYPE_FORMATS.get(type(transform(value)))


def insert(table: str, **kwargs) -> Tuple[str, Tuple[Any]]:
    """Generate an SQL insert statement based on `kwargs`"""
    args = OrderedDict(**kwargs)
    values = [arg for arg in args.values() if arg is not None]

    def transform(x):
        return TYPE_TRANSFORM[type(x)](x)

    def _(k):
        return f'"{k}"'

    return (
        f"INSERT INTO {table} "
        f"({', '.join([_(k) for k in args.keys() if args[k] is not None])})"
        " VALUES "
        f"({', '.join([type_fmt(v) for v in values if v is not None])});"
    ) % tuple([transform(v) for v in values])


def random_race():
    return [random_element(RACES)]


def random_age():
    return randint(18, 55)


def random_zip():
    return random_element(ZIP_CODES)


def random_gender():
    return random_element(GENDERS)


def random_orientation():
    return random_element(ORIENTATION)


def random_is_latino():
    return random_element(IS_LATINO)


def random_string(n: int):
    if n % 2 != 0:
        raise ValueError("random_string(n): n % 2 == 0 must be true")
    return binascii.b2a_hex(os.urandom(int(n / 2))).decode()


class SQLGenerator:
    accounts = list()
    devices = dict()
    contests = OrderedDict()

    def __init__(self):
        pass

    def account(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        dt = datetime.now(tz=TIMEZONE)

        start_point = int((dt - relativedelta(months=11)).timestamp())
        end_point = int((dt - relativedelta(days=2)).timestamp())

        created_ts = randint(start_point, end_point)
        created = datetime.fromtimestamp(created_ts, TIMEZONE)

        args = OrderedDict(kwargs)
        acct = dict(args)
        acct.update(
            {
                "created": created,
                "updated": dt,
            }
        )
        self.accounts.append(acct)

        return insert(
            "home_account",
            id=args.get("id"),
            email=args.get("email"),
            name=args.get("name"),
            zip=args.get("zip"),
            age=args.get("age"),
            created=created.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
            updated=dt.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
            is_sf_resident=args.get("is_sf_resident"),
            is_latino=args.get("is_latino"),
            gender=args.get("gender"),
            is_tester=args.get("is_tester", False),
            gender_other=args.get("gender_other", "N/A"),
            race_other=args.get("race_other", "N/A"),
            race=args.get("race"),
            sexual_orien=args.get("sexual_orien"),
            sexual_orien_other=args.get("sexual_orien_other", "N/A"),
        )

    def contest(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        contest_id = kwargs.get("contest_id")
        if contest_id in self.contests:
            raise KeyError(f"Contest '{contest_id}' already exists.")

        self.contests[contest_id] = (kwargs.get("start"), kwargs.get("end"))

        return insert(
            "home_contest",
            contest_id=kwargs.get("contest_id", None),
            start=kwargs.get("start"),  # date
            end=kwargs.get("end"),  # date
            start_promo=kwargs.get("start_promo"),  # date
            created=kwargs.get("created", None),  # timestamp with timezone
            updated=kwargs.get("updated", None),  # timestamp with timezone
            start_baseline=kwargs.get("start_baseline"),  # date
        )

    def account_contest(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        return insert(
            "home_account_contests",
            account_id=kwargs.get("account_id"),
            contest_id=kwargs.get("contest_id"),
        )

    def device(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        dev_id = kwargs.get("device_id")

        if dev_id in self.devices:
            raise KeyError(f"Device '{dev_id}' already exists.")

        account_id = kwargs.get("account_id")
        self.devices[account_id] = dev_id

        dt = datetime.now(tz=TIMEZONE)
        return insert(
            "home_device",
            device_id=dev_id,  # Required UID string
            created=dt.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
            account_id=account_id,
        )

    def daily_walk(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        return insert(
            "home_dailywalk",
            date=kwargs.get("date"),  # date
            steps=kwargs.get("steps"),
            distance=kwargs.get("distance"),  # double
            created=kwargs.get("created", None),  # timestamp with timezone
            updated=kwargs.get("updated", None),  # timestamp with timezone
            account_id=kwargs.get("account_id"),  # int
            device_id=kwargs.get("device_id"),  # str
        )

    def intentional_walk(self, **kwargs) -> Tuple[str, Tuple[Any]]:
        return insert(
            "home_intentionalwalk",
            event_id=kwargs.get("event_id"),  # str
            start=kwargs.get("start"),  # timestamp with timezone
            end=kwargs.get("end"),  # timestamp with timezone
            steps=kwargs.get("steps"),  # double
            pause_time=kwargs.get("pause_time"),  # double
            walk_time=kwargs.get("walk_time"),  # double
            distance=kwargs.get("distance"),  # double
            created=kwargs.get("created", None),  # timestamp with timezone
            account_id=kwargs.get("account_id"),  # int
            device_id=kwargs.get("device_id", None),  # str
        )

    def make_accounts(self, n: int) -> Tuple[List[str], List[int]]:
        """
        Generate SQL statements to insert `n` random accounts.

        Each account is created at a random time between the beginning of
        of the first contest and the end of the most recent contest.
        Randomized values are used for nearly all fields, with the
        exception of `id`, `email` and `name`, which use the iteration
        index `id` to set their values. All accounts generated
        through this function are known as SF residents via
        `is_sf_resident=True`.

        :returns: [outputs, account_ids]
                  outputs     - list of SQL insert strings
                  account_ids - list[int] of account IDs used in `outputs`
        """
        global accounts

        account_ids, outputs = [], []
        for id in range(1, n + 1):
            account_ids.append(id)
            output = self.account(
                id=id,
                email=f"user{id}@example.com",
                name=f"User {id}",
                zip=random_zip(),
                age=random_age(),
                is_sf_resident=True,
                is_latino=random_is_latino(),
                race=random_race(),
                gender=random_gender(),
                sexual_orien=random_orientation(),
            )
            outputs.append(output)

        self.accounts.sort(key=lambda x: x["created"])
        return [outputs, account_ids]

    def make_contests(
        self,
        n: int,
    ) -> Tuple[List[str], List[int], Dict[int, datetime]]:
        """Generate SQL statements to insert 3 random contest records."""
        # Create a few contests with consecutive ranges up until the
        # current month at the time this is executed.

        # Put ourselves ahead by one month for contest-range purposes.
        # This will give our data some realistic range, as if we're
        # somewhat in the middle of a contest.
        dt = datetime.now(tz=TIMEZONE) + relativedelta(months=1)
        outputs, contest_ids = [], []
        contest_times = dict()
        delta = 0
        for i in range(n):
            while True:

                # The start is three months before the end.
                start = dt - relativedelta(months=delta + 3)
                # Set `start` to the beginning of the month.
                r = monthrange(start.year, start.month)
                start -= relativedelta(days=max(start.day - 2, 1))

                end = dt - relativedelta(months=delta)
                # Set `end` to the end of the month.
                r = monthrange(end.year, end.month)
                end += relativedelta(days=r[1] - end.day)

                # Make the promo start 5 days before the contest.
                start_promo = start - relativedelta(days=5)
                start_baseline = start - relativedelta(days=1)

                try:
                    contest_id = "-".join([random_string(8) for i in range(4)])
                    output = self.contest(
                        contest_id=contest_id,
                        start=start.date(),
                        end=end.date(),
                        start_promo=start_promo.date(),
                        created=start.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
                        updated=end.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
                        start_baseline=start_baseline.date(),
                    )
                except KeyError:
                    continue

                contest_ids.append(contest_id)
                contest_times[contest_id] = (start, end)
                break

            outputs.append(output)

            # Increment the delta for the next contest period.
            delta += 4

        return [outputs, contest_ids, contest_times]

    def make_account_contests(self) -> List[List[str]]:
        """Generate SQL statements to insert account_contests relationships."""
        outputs = []
        for acct in self.accounts:
            created = acct.get("created").date()
            for contest_id, dt in self.contests.items():
                start, end = dt
                if created >= start and created <= end:
                    outputs.append(
                        self.account_contest(
                            account_id=acct.get("id"), contest_id=contest_id
                        )
                    )
        return [outputs]

    def make_devices(
        self, account_ids: List[int]
    ) -> Tuple[List[str], Dict[int, str]]:
        """Generate SQL statements to insert a device for each `account_id`"""
        n = len(account_ids)
        outputs = []
        devices = dict()
        # Give a device to every account.
        for id in range(1, n + 1):
            account_id = account_ids[id - 1]
            output = None
            while True:
                try:
                    dev_id = random_string(8)
                    output = self.device(
                        device_id=dev_id, account_id=account_id
                    )
                except ValueError:
                    continue
                devices[account_id] = dev_id
                break
            outputs.append(output)
        return [outputs, devices]

    def make_dailywalks(self, devices: Dict[int, str]) -> List[List[str]]:
        """Generate SQL statements to insert random daily walk records"""
        tmp_accounts = self.accounts

        first = tmp_accounts[0].get("created")
        dt = first
        end = datetime.now(tz=TIMEZONE)
        tracked = []
        outputs = []
        while dt < end:
            dt += relativedelta(days=1)

            i = 0
            n = len(tmp_accounts)
            while i < n:
                acct = tmp_accounts[i]

                if acct.get("created") <= dt:
                    tracked.append(acct)
                    tmp_accounts = tmp_accounts[1:]
                    n = len(tmp_accounts)
                    i -= 1

                    if i < 0:
                        i = 0
                else:
                    break

            for acct in tracked:
                account_id = acct.get("id")
                steps = randint(500, 7500)
                output = self.daily_walk(
                    date=dt.date(),
                    steps=steps,
                    # Google says average walk is 0.7km per 1000 steps.
                    # So, we approximate here based on the number of steps.
                    distance=steps * (0.7 / 1000),
                    created=dt.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
                    updated=dt.strftime("%Y-%m-%d %H:%M:%S (%Z)"),
                    account_id=account_id,
                    device_id=devices.get(account_id),
                )

                outputs.append(output)

        return [outputs]

    def make_intentionalwalks(
        self, devices: Dict[int, str]
    ) -> List[List[str]]:
        """Generate SQL statements to insert random intentional walk records"""
        tmp_accounts = self.accounts
        first = tmp_accounts[0].get("created")
        dt = first
        end = datetime.now(tz=TIMEZONE)
        events = set()
        outputs, tracked = [], []
        while dt < end - relativedelta(days=5):
            dt += relativedelta(days=1)

            i = 0
            n = len(tmp_accounts)
            while i < n:
                acct = tmp_accounts[i]

                if acct.get("created") < dt:
                    tracked.append(acct)
                    tmp_accounts = tmp_accounts[1:]
                    n = len(tmp_accounts)
                    i -= 1

                    if i < 0:
                        i = 0
                else:
                    break

            for acct in tracked:
                account_id = acct.get("id")
                steps = randint(500, 7500)

                start_ts = int(dt.timestamp())
                now = datetime.now(tz=TIMEZONE)
                end_ts = int(now.timestamp())

                # Determine a random start time from start to now - 5 hours.
                start_ts = randint(start_ts, end_ts - 5 * 60 * 60)

                # Walk for at least 30 minutes up until 4 hours.
                end_ts = randint(
                    start_ts + 1 * 60 * 30, start_ts + 4 * 60 * 60
                )

                start_time = datetime.fromtimestamp(start_ts, tz=TIMEZONE)
                start_fmt = start_time.strftime("%Y-%m-%d %H:%M:%S (%Z)")

                end_time = datetime.fromtimestamp(end_ts, tz=TIMEZONE)
                end_fmt = end_time.strftime("%Y-%m-%d %H:%M:%S (%Z)")

                event_id = "-".join([random_string(8) for i in range(4)])
                while event_id in events:
                    event_id = "-".join([random_string(8) for i in range(4)])

                events.add(event_id)
                output = self.intentional_walk(
                    event_id=event_id,
                    date=dt.date(),
                    steps=steps,
                    start=start_fmt,
                    end=end_fmt,
                    pause_time=0.0,
                    walk_time=(end_time - start_time).total_seconds(),
                    # Google says average walk is 0.7km per 1000 steps.
                    # So, we approximate here based on the number of steps.
                    distance=steps * (0.7 / 1000),
                    created=end_fmt,
                    account_id=account_id,
                    device_id=devices.get(account_id),
                )

                outputs.append(output)

        return [outputs]


def set_timezone(tz: str) -> None:
    global TIMEZONE
    TIMEZONE = ZoneInfo(tz)


def main() -> int:
    """Main execution entrypoint."""
    p = argparse.ArgumentParser()
    p.add_argument(
        "-a",
        "--accounts",
        default=250,
        type=int,
        help="number of walker accounts to generate (default: 250)",
    )
    p.add_argument(
        "-t",
        "--timezone",
        default="UTC",
        type=str,
        help=(
            "timezone used, should match your django "
            "settings.py timezone (default: 'UTC')"
        ),
    )
    args = p.parse_args()

    # Setup constants configured via arguments
    set_timezone(args.timezone)

    # Generate SQL statements
    sql = SQLGenerator()
    outputs, account_ids = sql.make_accounts(args.accounts)
    print("\n".join(outputs))

    outputs, contest_ids, contest_times = sql.make_contests(3)
    print("\n".join(outputs))

    (outputs,) = sql.make_account_contests()
    print("\n".join(outputs))

    outputs, devices = sql.make_devices(account_ids)
    print("\n".join(outputs))

    (outputs,) = sql.make_dailywalks(devices)
    print("\n".join(outputs))

    (outputs,) = sql.make_intentionalwalks(devices)
    print("\n".join(outputs))

    make_leaderboard()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
