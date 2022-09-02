import os
import sys

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Reset database (truncate application tables)"

    def handle(self, *args, **options):
        if os.getenv("DEPLOY_ENV").lower().startswith("prod"):
            print("This command is not allowed on a production server.")
            sys.exit(1)

        question = (
            "\nAre you sure you want to truncate all tables?"
            " (Type `yes` exactly): "
        )
        answer = input(question)
        if answer == "yes":
            cursor = connection.cursor()

            # Truncating accounts (with cascade) will also truncate
            # devices, daily walks, and intentional walks
            cursor.execute(
                "TRUNCATE TABLE home_account RESTART IDENTITY CASCADE;"
            )
            print("All accounts, devices, and walks have been reset.")

            # Also truncate contests
            cursor.execute("TRUNCATE TABLE home_contest CASCADE;")
            print("All contests have been reset.")

        else:
            print("Aborted resetdb.\n")
