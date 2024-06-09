import logging

from django.core.management.base import BaseCommand
import os

from home.management.modules.heroku import HerokuCLIException, HerokuClient
from home.management.modules.scrubber import DatabaseScrubLoader
from home.models import ALL_MODELS
from urllib.parse import urlparse

from server.settings import DATABASES

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This command pulls in a database dump from the specified Heroku app's Postgres database,
    scrubs it, and restores it locally. It's intended to be used in a development environment
    to easily replicate the state of the app's production or staging database.

    The command accepts one argument, 'heroku-app', which specifies the name of the Heroku
    app to fetch the dump from. It defaults to 'iwalk-test', but can also be 'iwalk-staging'
    or 'iwalk-prod'.

    Run python manage.py herokudump --help for more information.
    """

    help = "Pulls in a database dump from the iwalk app postgres, scrubs and restores it locally."

    def add_arguments(self, parser):
        """Adds arguments to the command in addition to the default BaseCommands."""
        parser.add_argument(
            # Positional argument, defaults to required.
            "heroku-app",
            type=str,
            help="The name of the Heroku app to fetch the dump from. Default: iwalk-test",
            default="iwalk-test",
            choices=[
                "iwalk-test",
                "iwalk-staging",
                "iwalk-prod",
            ],
        )

    def handle(self, *args, **options):
        if os.environ.get("DEPLOY_ENV") != "development":
            # Paranoia check to ensure that the command
            # is only run in development environment.
            logger.error(
                "this command is only runnable in a development environment."
            )
            raise SystemExit(1)

        app = options["heroku-app"]
        logger.info(f"Fetching database dump from Heroku app: {app}")
        verbosity = options.get("verbosity")
        # we don't need this many levels of distinction
        match verbosity:
            case 0:
                level = logging.ERROR
            case 1:  # Default
                level = logging.INFO
            case 2 | 3:
                level = logging.DEBUG
        logger.setLevel(level)

        try:
            self.run(app, logger)
        except KeyboardInterrupt:
            raise SystemExit(1)

    def run(self, app: str, logger: logging.Logger):
        try:
            heroku_client = HerokuClient(logger=logger)
        except HerokuCLIException as e:
            logger.error(e)
            raise SystemExit(1)

        with heroku_client:
            heroku_dump = heroku_client.pg_dump(app)
            dbconfigs = self.load_targets_from_env()
            logger.debug(f"using database configurations: {dbconfigs}")

            with DatabaseScrubLoader(
                # Connect to the database for a temporary
                # scrubbing session.
                user=dbconfigs["target_user"],
                host=dbconfigs["target_host"],
                port=dbconfigs["target_port"],
                models=ALL_MODELS,
                databases=DATABASES,
                # seed is fixed for deterministic scrubbing.
                seed=123,
                logger=logger,
            ) as db_scrubber:
                db_scrubber.seed_with(
                    heroku_dump,
                    precmd=self.get_precmd(app),
                )
                logger.info("scrubbing the database with the heroku dump.")
                db_scrubber.copy_scrubbed_to(**dbconfigs)
                logger.info("completed.")

    def load_targets_from_env(self):
        """Load the target database configurations from the Django environment."""
        url = os.environ["DATABASE_URL"]
        result = urlparse(url)
        # This returns a dictionary of the target database configurations
        # that the Django app by default uses.
        return {
            "target_host": result.hostname or "localhost",
            "target_port": result.port or "5432",
            "target_user": result.username or "postgres",
            "target_password": result.password or "",
            "target_dbname": result.path[1:] or "iwalk",
        }

    def get_precmd(self, app: str) -> str:
        """SQL commands to run before running pg_restore --clean.

        The alternative option would be to disconnect from the database,
        drop the database completely and give the dump a fresh start,
        and then tell Django to reconnect (to use its ORM to scrub),
        which complicates the code. This is much simpler.
        """
        match app:
            case "iwalk-test", "iwalk-staging":
                # The dumps in iwalk-test and iwalk-staging have line:
                # CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "heroku_ext";
                # This is because heroku now creates a schema heroku_ext for extensions.
                # https://devcenter.heroku.com/changelog-items/2446
                return """
               CREATE SCHEMA IF NOT EXISTS heroku_ext;
               """
            case "iwalk-prod":
                # Our current prod database doesn't have the same as above.
                # If we decide we need new extensions and move over to the heroku_ext,
                # edit this accordingly.
                return ""
            case _:
                raise ValueError(f"Unknown Heroku app: {app}")
