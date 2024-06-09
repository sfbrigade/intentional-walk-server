from logging import Logger
import os
import shutil
import tempfile
from typing import Any, Dict, List
import uuid

from django.db import models

from home.management.modules.shared import run_command_factory
from home.models.mixins.privacyprotectedfields import (
    FieldType,
    PrivacyProtectedFieldsMixin,
)
from faker import Faker


class PGError(Exception):
    """Exception raised for errors in the Postgres class."""

    def __init__(self, message: str):
        self.message = message

    def does_not_exist(self):
        return "does not exist" in self.message


run = run_command_factory(PGError)


class DatabaseScrubLoader:
    """Scrub a database dump and load it into a target database.

    The process is encapsulated in a context manager to ensure that the temporary
    database is cleaned up after the process is complete.

    The process involves the following steps:
    1. Load the original database dump into a temporary database.
    2. Scrub the temporary database of sensitive information.
        - The fields to be scrubbed are determined by the provided sensitive
          fields of each model.
    3. Create a new dump from the scrubbed temporary database.
    4. Apply the scrubbed dump to the target database.

    The use of a temporary database ensures that the original database
    remains unaffected by the scrubbing process.
    In case of any crashes during the process,
    the current databases are not left in an inconsistent state.
    Potentially sensitive information is never set on the local database.
    """

    # Prefix used to identify temporary databases created by this class.
    _tmp_prefix = "tmp"
    # Key used to identify the temporary database in the DATABASES setting.
    _tmp_db_key = "tmp"

    def __init__(
        self,
        user: str,
        host: str,
        port: str,
        models: List[type[models.Model]],
        databases: Dict[str, Any],
        seed: int,
        logger=Logger,
    ):
        """
        Args:
            user (str): The username to be used for database operations.
            host (str): The host on which the database operations are to be performed.
            port (str): The port on which the database operations are to be performed.
            models (List[type[models.Model]]): A list of Django model classes whose data is to be scrubbed.
            databases (Dict[str, Any]):
                The Django DATABASES setting, which contains the configuration for all databases.
            seed (int):
                The seed for the random number generator used in data scrubbing.
                The same seed will result in the same scrubbed data.
        """

        # connection parameters for connecting to postgres server
        self.user = user
        self.host = host
        self.port = port
        self.models = models
        self.databases = databases
        self.seed = seed
        self.logger = logger

        self._verify_installation()
        self._initialize()
        self._create_temp_db()

    def _initialize(self):
        """Initializes the a temporary directory and database."""
        self._temp_dir = tempfile.TemporaryDirectory()
        # Temporary database name
        self._dbname = f"{self._tmp_prefix}_{uuid.uuid4().hex}"

    @property
    def scrub_dump_path(self):
        """Returns path for the scrubbed dump file."""
        return os.path.join(
            self._temp_dir.name, f"{self._dbname}-scrubbed.dump"
        )

    @property
    def dbnameflag(self):
        """Returns a formatted database name flag for use in commands."""
        return f"--dbname=postgresql://{self.user}:@{self.host}:{self.port}/{self._dbname}"

    def seed_with(self: str, dump_file_path: str, precmd: str):
        """Seeds a database from a dump file. Precmd is a psql command to run before the restore."""
        if precmd:
            # Apply additional sql before doing the dump.
            # Primarily used to set up missing schemas or extensions
            # that a dump may rely on.
            run(["psql", self.dbnameflag, "-c", precmd])

        self.logger.info(
            f"seeding temporary database {self._dbname} from {dump_file_path}"
        )
        restore(
            user=self.user,
            host=self.host,
            port=self.port,
            dbname=self._dbname,
            dump_file_path=dump_file_path,
        )

    def copy_scrubbed_to(
        self,
        target_dbname: str,
        target_user: str,
        target_password: str,
        target_host: str,
        target_port: str,
    ):
        """Scrubs and writes the scrubbed dump to the target database."""
        self._scrub_database()
        self.logger.info(f"restoring scrubbed dump to {target_dbname}")
        restore(
            user=target_user,
            host=target_host,
            password=target_password,
            port=target_port,
            dbname=target_dbname,
            dump_file_path=self.scrub_dump_path,
        )

    def _verify_installation(self):
        """Verifies that the required tools are installed in the shell."""
        required_tools = ["createdb", "dropdb", "pg_dump", "psql"]
        for tool in required_tools:
            if shutil.which(tool) is None:
                raise PGError(f"{tool} is not installed or not in PATH")

    def _create_temp_db(self):
        """Creates a temporary database for storing a dump to be scrubbed."""
        self.logger.debug(f"creating temporary database {self._dbname}")
        command = [
            "createdb",
            "-U",
            self.user,
            "-h",
            self.host,
            "-w",
            self._dbname,
        ]
        run(command)

    def _is_temp_db(self, dbname: str) -> bool:
        """Checks if a database is a temporary database."""
        return self._tmp_prefix in dbname

    def _scrub_database(self):
        """Once seeded, scrub the database."""
        fake = Faker()
        # Ensure deterministic scrubbing.
        fake.random.seed(self.seed)

        self.logger.debug("scrubbing sensitive fields")
        scrubbable = (
            model
            for model in self.models
            if issubclass(model, PrivacyProtectedFieldsMixin)
        )
        for model in scrubbable:
            for obj in model.objects.using(self._tmp_db_key).all():
                for field in model.privacy_protected_fields():
                    name = field["name"]
                    typ = field["type"]
                    # It is unfortunate that unique.email() can runs out of unique on large because of
                    # their implementation of pulling from a pool with large amount.
                    # Prepending fake.name() reduces the chance of collision while
                    # still having a reasonable length (as opposed to using a uuid).
                    email = fake.first_name() + fake.unique.email()
                    if typ == FieldType.EMAIL:
                        setattr(obj, name, email)
                    elif typ == FieldType.NAME:
                        setattr(obj, name, fake.name())
                    else:
                        setattr(obj, name, fake.word())
                obj.save()
        self._pg_dump()

    def _drop_temp_db(self):
        """Drops the temporary database."""
        if not self._is_temp_db(self._dbname):
            # Paranoia; refuse to drop a database that doesn't look like a temporary database.
            raise PGError(
                f"refusing to drop database {self._dbname} as it does not appear to be a temporary database."
            )

        try:
            # It's just a temp db; force all connections to close.
            command = [
                "dropdb",
                "--force",
                "-U",
                self.user,
                "-h",
                self.host,
                self._dbname,
            ]
            run(command)
            self.logger.debug(f"dropped temporary database {self._dbname}")
        except PGError as e:
            if e.does_not_exist():
                return
            raise e

    def _pg_dump(self):
        """Creates a dump file of the temporary database."""
        command = [
            "pg_dump",
            "-F",
            "c",
            self.dbnameflag,
            "--no-owner",
            "--no-comments",
            "--clean",
            "--if-exists",
            "--no-acl",
            "-f",
            self.scrub_dump_path,
        ]
        self.logger.debug(
            f"created temporary scrubbed database dump at {self.scrub_dump_path}"
        )
        run(command)

    def _cleanup(self):
        """Cleans up the temporary database and directory."""
        try:
            self.databases.pop(self._tmp_db_key)
        except KeyError:
            self.logger.debug(
                "temporary database wasn't created yet. nothing to clean up."
            )
            pass
        self._drop_temp_db()
        self._temp_dir.cleanup()

    def __enter__(self):
        self.databases[self._tmp_db_key] = {
            **self.databases.get("default", {}),
            "NAME": self._dbname,
            "USER": self.user,
            "HOST": self.host,
            "PORT": self.port,
            "PASSWORD": "",
        }
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def __del__(self):
        self._cleanup()


def restore(
    user: str,
    host: str,
    port: str,
    dbname: str,
    dump_file_path: str,
    password: str = "",
):
    """Restores a database from a dump file."""
    dbnameflag = (
        f"--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}"
    )
    command = [
        "pg_restore",
        dbnameflag,
        "--no-owner",
        "--no-comments",
        "--clean",
        "--if-exists",
        "--no-acl",
        dump_file_path,
    ]
    return run(command)
