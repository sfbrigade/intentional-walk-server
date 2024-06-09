from datetime import datetime
import logging
import os
import tempfile
from typing import List

from home.management.modules.shared import run_command_factory


class HerokuCLIException(Exception):
    """Exception raised for errors in the Heroku CLI."""


run = run_command_factory(HerokuCLIException)


class HerokuClient:
    """Class to interact with heroku's CLI and API.

    It is intended to use within a context manager to ensure cleanup of temporary files.
    """

    def __init__(self, logger: logging.Logger):
        self._check_installation()
        self.token = self._get_heroku_token()
        self._temp_dir = tempfile.TemporaryDirectory()
        self.dumps: List[str] = []
        self.logger = logger

    def _check_installation(self):
        try:
            # No need to log the output here
            run(["heroku", "--version"])
        except HerokuCLIException:
            # Convert generic exception to a more specific one
            raise HerokuCLIException(
                "Heroku CLI is not installed. "
                + "Please install it from https://devcenter.heroku.com/articles/heroku-cli"
            )

    def _get_heroku_token(self) -> str:
        """Get the heroku token from the CLI and save it.
        This can later be used to interact with the Heroku API.
        """
        try:
            return run(["heroku", "auth:token"]).strip()
        except HerokuCLIException:
            raise HerokuCLIException(
                "Heroku CLI is not authenticated. "
                + "Please authenticate by running 'heroku login'"
            )

    def pg_dump(self, app_name: str) -> str:
        """Fetch a custom heroku pg_dump format of the current the database from heroku."""
        # Why is there no Heroku SDK???
        # Opt for python over shell script for better error handling
        # and maintainability.
        run(["heroku", "pg:backups:capture", "-a", app_name], self.logger)
        file_name = datetime.now().strftime(f"%Y-%m-%d-{app_name}.dump")
        path = os.path.join(self._temp_dir.name, file_name)
        run(
            ["heroku", "pg:backups:download", "-a", app_name, "-o", path],
            self.logger,
        )
        return path

    def cleanup(self):
        self._temp_dir.cleanup()

    def __del__(self):
        self.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
