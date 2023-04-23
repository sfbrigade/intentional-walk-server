import logging

from django.core.management.base import BaseCommand
from django.db import connection

from home.models import Account

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deletes duplicate account records"

    def handle(self, *args, **options):
        emails = []
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT LOWER("email") AS le, COUNT(*)
                FROM home_account
                GROUP BY le
                HAVING COUNT(*) > 1
                ORDER BY le
                """
            )
            results = cursor.fetchall()
            emails = [row[0] for row in results]

        for email in emails:
            logger.info(f"Deduping: {email}")
            accounts = Account.objects.filter(email__iexact=email).order_by(
                "created"
            )
            # delete all but the newest account
            accounts = accounts[0 : len(accounts) - 1]  # noqa E203
            for account in accounts:
                account.delete()

        logger.info("Done.")
